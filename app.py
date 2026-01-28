import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif'}
ALLOWED_LANGUAGES = {'eng': 'English', 'khm': 'Khmer'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')

# Configure tesseract command: prefer `TESSERACT_CMD` env var, else try common install path (Windows)
tess_env = os.environ.get('TESSERACT_CMD')
if tess_env:
    pytesseract.pytesseract.tesseract_cmd = tess_env
else:
    common = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(common):
        pytesseract.pytesseract.tesseract_cmd = common


def tesseract_available() -> bool:
    try:
        _ = pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    # Single-page app (all output is shown on index)
    return render_template(
        'index.html',
        languages=ALLOWED_LANGUAGES,
        last_lang=session.get('last_lang', 'eng'),
        last_txt=session.get('last_txt'),
        last_text=session.get('last_text', '')
    )


@app.route('/upload', methods=['POST'])
def upload():
    # This endpoint is used by fetch() from index.html → return JSON
    wants_json = (
        request.headers.get('X-Requested-With') == 'fetch' or
        'application/json' in (request.headers.get('Accept') or '')
    )

    def json_fail(msg: str, code: int = 400):
        if wants_json:
            return jsonify({"ok": False, "error": msg}), code
        flash(msg)
        return redirect(url_for('index'))

    if 'image' not in request.files:
        return json_fail('No file part')

    file = request.files['image']
    if not file or file.filename == '':
        return json_fail('No selected file')

    if not allowed_file(file.filename):
        return json_fail('File type not allowed')

    # Save with unique name (prevents overwriting files)
    original = secure_filename(file.filename)
    ext = original.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Open image
    try:
        image = Image.open(filepath)
    except Exception as e:
        return json_fail(f'Failed to open image: {e}', 500)

    # Language
    lang = request.form.get('lang', 'eng')
    if lang not in ALLOWED_LANGUAGES:
        lang = 'eng'

    # OCR
    try:
        text = pytesseract.image_to_string(image, lang=lang)
    except pytesseract.pytesseract.TesseractError as e:
        msg = f'OCR error from Tesseract: {e}'
        if lang == 'khm':
            msg += ' (Khmer language data may not be installed: khm.traineddata)'
        return json_fail(msg, 500)
    except Exception as e:
        return json_fail(f'OCR error: {e}', 500)

    text = (text or "").strip()

    # Save extracted text as .txt
    txt_filename = f"{os.path.splitext(filename)[0]}.txt"
    txt_path = os.path.join(app.config['UPLOAD_FOLDER'], txt_filename)
    try:
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        session['last_txt'] = txt_filename
        session['last_lang'] = lang
        session['last_text'] = text
    except Exception:
        txt_filename = None

    # Extra helpful diagnostics if empty
    if not text:
        available = tesseract_available()
        # Keep response OK, but add a warning message for UI
        warn = "No text detected. Try a clearer image or correct language."
        if not available:
            warn = "Tesseract not detected. Please install Tesseract OCR."
        return jsonify({
            "ok": True,
            "text": "",
            "lang": lang,
            "warning": warn,
            "download_txt": url_for('download_file', filename=txt_filename) if txt_filename else None
        })

    return jsonify({
        "ok": True,
        "text": text,
        "lang": lang,
        "download_txt": url_for('download_file', filename=txt_filename) if txt_filename else None
    })


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
