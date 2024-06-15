from application import app, dropzone
from flask import render_template, request, redirect, url_for, session
from .forms import QRCodeData
import secrets
import os
import cv2
import pytesseract
from PIL import Image
import numpy as np
from gtts import gTTS
from application import utils

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == 'POST':
        # Set a session value
        sentence = ""

        f = request.files.get('file')
        if not f:
            return "No file uploaded", 400

        filename, extension = os.path.splitext(f.filename)
        generated_filename = secrets.token_hex(10) + f"{extension}"

        file_location = os.path.join(app.config['UPLOADED_PATH'], generated_filename)
        f.save(file_location)

        # Debug: Ensure file is saved correctly
        print(f"File saved to {file_location}")

        # OCR Processing
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path as per your system

        img = cv2.imread(file_location)
        if img is None:
            print("Failed to read image file")
            return "Failed to read image file", 400

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Debug: Verify image reading and conversion
        print("Image read and converted successfully")

        try:
            boxes = pytesseract.image_to_data(img)
        except Exception as e:
            print(f"OCR processing failed: {e}")
            return f"OCR processing failed: {e}", 500

        # Debug: Print OCR data
        print("OCR Data:", boxes)

        for i, box in enumerate(boxes.splitlines()):
            if i == 0:
                continue

            box = box.split()
            if len(box) == 12:
                sentence += box[11] + " "

        session["sentence"] = sentence

        # Debug: Print extracted sentence
        print("Extracted Sentence:", sentence)

        # Delete file after processing
        os.remove(file_location)

        return redirect("/decoded/")

    return render_template("upload.html", title="Upload")

@app.route("/decoded", methods=["GET", "POST"])
def decoded():
    sentence = session.get("sentence", "")
    # Debug: Ensure session sentence is retrieved
    print("Session Sentence:", sentence)

    lang, _ = utils.detect_language(sentence)  # Ensure utils has detect_language function

    form = QRCodeData()

    if request.method == "POST":
        generated_audio_filename = secrets.token_hex(20) + ".mp4"
        text_data = form.data_field.data
        translate_to = form.language.data

        translated_text = utils.translate_text(text_data, translate_to)  # Ensure utils has translate_text function
        tts = gTTS(translated_text, lang=translate_to)

        file_location = os.path.join(app.config['AUDIO_FILE_UPLOAD'], generated_audio_filename)
        tts.save(file_location)

        form.data_field.data = translated_text

        return render_template("decoded.html",
                               title="Decoded",
                               form=form,
                               lang=utils.languages.get(lang),
                               audio=True,
                               file=generated_audio_filename)

    form.data_field.data = sentence
    session["sentence"] = ""

    return render_template("decoded.html",
                           title="Decoded",
                           form=form,
                           lang=utils.languages.get(lang),
                           audio=False)
