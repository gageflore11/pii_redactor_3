"""
 Lots of changes throughout. Might be easier to just copy + paste entire files but
    I put comments highlighting exactly what I changed so it's easier to debug if something breaks.
     
      Altered files: 
       * app.py
       * results.html
       * styles.css 
"""       
# ***************** For this block copy from here... ********************
import os
from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory, send_file
# Original line might still work with yours: from pii_redactor import pii_redactor 
# Replace all instances of PiiRedactor with pii_redactor if yours no longer works
from pii_redactor import PiiRedactor
from io import BytesIO
import zipfile

app=Flask(__name__)

# Files can be up to 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# Allow these files
app.config['UPLOAD_EXTENSIONS'] = ['.txt', '.pdf', '.docx']
# Send files to upload folder
app.config['UPLOAD_PATH'] = 'uploads/'

# New stuff, replace old RESULT_PATH, add lines to create folders
app.config['RESULT_PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(app.config['UPLOAD_PATH'], exist_ok=True)
os.makedirs(app.config['RESULT_PATH'], exist_ok=True)

# **************** ... to here *******************************


@app.route('/')
def index():
    return render_template('index.html')


#**************** REPLACE ORIGINAL UPLOAD_FILES ROUTE WITH THIS *********************************
@app.route('/', methods=['POST'])
def upload_files():
    redacted_text = None
    redacted_files = []
   
    text_input = request.form.get('text_input')
    if text_input and text_input.strip():
        text_input_file_path = os.path.join(app.config['UPLOAD_PATH'], 'text_input.txt')
        with open(text_input_file_path, 'w', encoding='utf-8') as file:
            file.write(text_input)
        output_path = os.path.join(app.config['RESULT_PATH'], 'text_input_redacted.txt') 
        PiiRedactor().redact_wrapper(text_input_file_path, output_path)
        with open(output_path, 'r', encoding='utf-8') as file:
            redacted_text = file.read()
        redacted_files.append('text_input_redacted.txt')

    for uploaded_file in request.files.getlist('file'):
        if uploaded_file.filename:
            file_path = os.path.join(app.config['UPLOAD_PATH'], uploaded_file.filename)
            uploaded_file.save(file_path)

            name, ext = os.path.splitext(uploaded_file.filename)
            redacted_filename = f"{name}_redacted{ext}"
            output_path = os.path.join(app.config['RESULT_PATH'], redacted_filename)

            PiiRedactor().redact_wrapper(file_path, output_path)
            redacted_files.append(redacted_filename)

    return render_template(
        'results.html',
        redacted_text=redacted_text,
        redacted_files=redacted_files
    )



#***************** DOWNLOAD ALL ROUTE, COPY PASTE THIS ****************************
@app.route('/download-all')
def download_all():
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf: 
        # Iterate over every file in /results
        for filename in os.listdir(app.config['RESULT_PATH']):
            file_path = os.path.join(app.config['RESULT_PATH'], filename)
            if os.path.isfile(file_path):
                # arcname will keep whatever filename in the zip, this can be changed
                zf.write(file_path, arcname=filename)
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype = 'application/zip',
        as_attachment = True,
        download_name = 'redacted_files.zip'
    )

# ******************* NEW DOWNLOAD ROUTE, COPY PASTE THIS ****************************
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['RESULT_PATH'], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

