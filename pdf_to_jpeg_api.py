from flask import Flask, request, send_file, jsonify
from pdf2image import convert_from_bytes
import io
import time

app = Flask(__name__)

@app.route("/convert", methods=["POST"])
def convert_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        images = convert_from_bytes(file.read())
        img_io = io.BytesIO()
        images[0].save(img_io, 'JPEG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name='out.jpg')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

