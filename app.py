import uuid
from PIL import Image
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
import zipfile


def allowed_file(filename):
    # Define the allowed file extensions
    allowed_extensions = {'jpg', 'jpeg', 'png'}

    # Check if the file extension is in the set of allowed extensions
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")


# Define the path to the 'tmp' folder
UPLOAD_FOLDER = './tmp/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
MARKED_FOLDER = './marked/'
app.config['MARKED_FOLDER'] = MARKED_FOLDER


@app.route('/upload', methods=['POST'])
def upload_and_download():
    uniq_id = str(uuid.uuid4())

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    files = request.files.getlist('file')

    uploaded_files = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(uniq_id[:8] + "-" + file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            uploaded_files.append(filename)

    # Load the watermark image
    watermark = Image.open("./tmp/" + uniq_id[:9] + "watermark.png")

    # Specify the input and output folders
    input_folder = app.config['UPLOAD_FOLDER']
    output_folder = app.config['MARKED_FOLDER']

    os.makedirs(output_folder, exist_ok=True)

    resize_percentage = 30

    for filename in os.listdir(input_folder):
        if filename.endswith(".jpg") or filename.endswith(".jpeg"):
            image = Image.open(os.path.join(input_folder, filename))
            img_width, img_height = image.size
            watermark_width = int(img_width * (resize_percentage / 100))
            watermark_height = int(watermark.size[1] * (watermark_width / watermark.size[0]))
            watermark_resized = watermark.resize((watermark_width, watermark_height), Image.LANCZOS)
            position = ((img_width - watermark_width) // 2, (img_height - watermark_height) // 2)
            marked_image = image.copy()
            marked_image.paste(watermark_resized, position, watermark_resized)
            output_path = os.path.join(output_folder, filename)
            marked_image.save(output_path, "JPEG")

    marked_images = os.listdir(output_folder)

    if len(marked_images) == 0:
        return jsonify({'error': 'No marked images available for download'})

    if len(marked_images) == 1:
        return send_from_directory(output_folder, marked_images[0])
    else:
        print("GENERANDO EL ZIP")
        matching_files = [filename for filename in os.listdir(output_folder) if filename.startswith(uniq_id[:8])]
        zip_filename = app.config['UPLOAD_FOLDER'] + "/" + uniq_id[:9] + 'marked_images.zip'

        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for filename in matching_files:
                file_path = os.path.join(output_folder, filename)
                zipf.write(file_path, os.path.basename(file_path))
        print(app.config["UPLOAD_FOLDER"])
        print(uniq_id[:9] + "marked_images.zip")
        print(app.config['UPLOAD_FOLDER'], uniq_id[:9] + "marked_images.zip")
        #return send_from_directory(app.config['UPLOAD_FOLDER'], uniq_id[:9] + "marked_images.zip", as_attachment=True)
        return send_from_directory(input_folder, uniq_id[:9] + "marked_images.zip", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
