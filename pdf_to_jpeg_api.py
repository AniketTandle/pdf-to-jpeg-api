from flask import Flask, request, send_file, jsonify
from pdf2image import convert_from_path
import os
import uuid
import threading
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

app = Flask(__name__)

# Folder to store uploaded/converted files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def cleanup_file(path, delay=60):
    """Delete a file after a delay (default: 60s)"""
    threading.Timer(delay, lambda: os.remove(path) if os.path.exists(path) else None).start()

@app.route('/convert', methods=['POST'])
def convert_pdf_to_jpeg():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files allowed"}), 400

    # Save uploaded file
    pdf_filename = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.pdf")
    file.save(pdf_filename)

    try:
        # Convert PDF to image(s)
        images = convert_from_path(pdf_filename)
        image_paths = []

        for img in images:
            img = img.convert("RGB")
            img_filename = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.jpeg")
            img.save(img_filename, 'JPEG')
            image_paths.append(img_filename)

        if len(image_paths) == 1:
            response = send_file(image_paths[0], mimetype='image/jpeg')
        else:
            zip_buffer = BytesIO()
            with ZipFile(zip_buffer, 'w', ZIP_DEFLATED) as zipf:
                for path in image_paths:
                    if os.path.exists(path):
                        zipf.write(path, os.path.basename(path))
            zip_buffer.seek(0)
            response = send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name='converted_images.zip'
            )

        # Cleanup
        cleanup_file(pdf_filename)
        for path in image_paths:
            cleanup_file(path)

        return response

    except Exception as e:
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)
        for path in image_paths:
            if os.path.exists(path):
                os.remove(path)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
