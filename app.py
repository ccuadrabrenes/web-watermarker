from PIL import Image
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
import shutil

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
UPLOAD_FOLDER = 'tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload', methods=['POST'])
def upload_images():
    # Check if the 'tmp' folder exists; if not, create it
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Check if the request contains files
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    files = request.files.getlist('file')

    uploaded_files = []

    for file in files:
        if file and allowed_file(file.filename):
            # Save the file to the 'tmp' folder
            if "png" in file.filename:
                print("Este es un PNG y su nombre es: "+file.filename)
                filename = secure_filename("watermark.png")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                uploaded_files.append(filename)
            else:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                uploaded_files.append(filename)

    return jsonify({'message': 'Files uploaded successfully', 'uploaded_files': uploaded_files})

@app.route('/download-marked')
def download_marked_images():
    # Load the watermark image
    watermark = Image.open("./tmp/watermark.png")

    # Specify the input and output folders
    input_folder = "./tmp"
    output_folder = "./marked"

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Define the percentage by which you want to resize the watermark (e.g., 50%)
    resize_percentage = 30  # You can change this percentage as needed

    # Process each JPEG file in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".jpg") or filename.endswith(".jpeg"):
            # Open the JPEG image
            image = Image.open(os.path.join(input_folder, filename))

            # Get the dimensions of the image
            img_width, img_height = image.size

            # Calculate the new dimensions of the watermark based on the percentage
            watermark_width = int(img_width * (resize_percentage / 100))
            watermark_height = int(watermark.size[1] * (watermark_width / watermark.size[0]))

            # Resize the watermark
            watermark_resized = watermark.resize((watermark_width, watermark_height), Image.LANCZOS)

            # Calculate the position to center the resized watermark
            position = ((img_width - watermark_width) // 2, (img_height - watermark_height) // 2)

            # Create a copy of the image to add the watermark
            marked_image = image.copy()

            # Paste the resized watermark on the image at the center position
            marked_image.paste(watermark_resized, position, watermark_resized)

            # Save the watermarked image to the output folder
            output_path = os.path.join(output_folder, filename)
            marked_image.save(output_path, "JPEG")
            print(f"Image marked: {filename}")

    # Check if there are marked images to download
    marked_images = os.listdir(output_folder)
    if len(marked_images) == 0:
        return jsonify({'error': 'No marked images available for download'})

    # If there's only one marked image, send it as a single file
    if len(marked_images) == 1:
        return send_from_directory(output_folder, marked_images[0])

    # If there are multiple marked images, create a zip file and send it
    marked_images_zip = os.path.join(output_folder, 'marked_images.zip')
    shutil.make_archive(marked_images_zip[:-4], 'zip', output_folder)

    # Send the zip file as a download
    return send_from_directory(output_folder, 'marked_images.zip', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)