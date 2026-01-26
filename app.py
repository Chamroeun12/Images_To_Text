import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
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

# Configure tesseract command: prefer `TESSERACT_CMD` env var, else try common install path
tess_env = os.environ.get('TESSERACT_CMD')
if tess_env:
    pytesseract.pytesseract.tesseract_cmd = tess_env
else:
    common = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(common):
        pytesseract.pytesseract.tesseract_cmd = common


def tesseract_available():
    try:
        _ = pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    last_txt = session.get('last_txt')
    last_lang = session.get('last_lang', 'eng')
    return render_template('index.html', last_txt=last_txt, languages=ALLOWED_LANGUAGES, last_lang=last_lang)


@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    file = request.files['image']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Open image with Pillow and run OCR
        try:
            image = Image.open(filepath)
        except Exception as e:
            flash(f'Failed to open image: {e}')
            return redirect(url_for('index'))

        # Choose language for OCR (default to English)
        lang = request.form.get('lang', 'eng')
        if lang not in ALLOWED_LANGUAGES:
            flash(f'Unsupported language {lang}; defaulting to English.')
            lang = 'eng'

        try:
            text = pytesseract.image_to_string(image, lang=lang)
        except pytesseract.pytesseract.TesseractError as e:
            flash(f'OCR error from Tesseract: {e}')
            if lang == 'khm':
                flash('Khmer language (khm) may not be installed. See README for installation instructions.')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'OCR error: {e}')
            return redirect(url_for('index'))

        # If OCR returned empty, warn the user and log diagnostic info
        if not text or not text.strip():
            available = tesseract_available()
            flash('OCR returned no text. Ensure Tesseract is installed and the image is clear.')
            flash(f'Tesseract available: {available}. tesseract_cmd={pytesseract.pytesseract.tesseract_cmd}')
            if lang == 'khm':
                flash('If using Khmer, make sure khm.traineddata is present in Tesseract tessdata folder.')
            print('DEBUG: OCR empty; tesseract_cmd=', pytesseract.pytesseract.tesseract_cmd)

        # Save extracted text as .txt next to the uploaded image
        base, _ = os.path.splitext(filename)
        txt_filename = f"{base}.txt"
        txt_path = os.path.join(app.config['UPLOAD_FOLDER'], txt_filename)
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            # store last txt file in session so index page can show download
            session['last_txt'] = txt_filename
            session['last_lang'] = lang
        except Exception:
            # Non-fatal: continue without saving
            txt_filename = None

        return render_template('result.html', filename=filename, text=text, txt_filename=txt_filename, lang=lang, languages=ALLOWED_LANGUAGES)
    else:
        flash('File type not allowed')
        return redirect(url_for('index'))


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/download/<path:filename>')
def download_file(filename):
    # Force download with attachment headers
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
