# Image to Text (Flask + Tesseract)

Simple Flask web app to upload an image and extract text using Tesseract OCR via `pytesseract`.

## Requirements

- Python 3.8+
- Tesseract-OCR installed on the system (separate from the Python package)

### Install Tesseract on Windows

Download the installer from: https://github.com/tesseract-ocr/tesseract/releases
Install it (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`).

After installing, either add the Tesseract folder to your PATH or set the `TESSERACT_CMD` environment variable to the full path of `tesseract.exe`.

## Setup

Create a virtual environment and install Python packages:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
pip install -r requirements.txt
```

If you didn't add Tesseract to PATH, set the env var (Windows example):

```powershell
setx TESSERACT_CMD "C:\Program Files\Tesseract-OCR\tesseract.exe"
# Restart your terminal after setx for it to take effect
```

Or set it only for the current session:

```powershell
$env:TESSERACT_CMD = 'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Run

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser, upload an image, and the extracted text will be shown.

## Notes

- The app saves uploaded files to the `uploads/` folder created next to `app.py`.
- For better accuracy, consider preprocessing images (binarization, deskewing) or using more advanced OCR models.

## Khmer language support

To enable Khmer OCR, add the Khmer trained data file (`khm.traineddata`) into Tesseract's `tessdata` folder.

1. Download `khm.traineddata` from the Tesseract tessdata repository, for example:

   https://github.com/tesseract-ocr/tessdata/raw/main/khm.traineddata

2. Copy the downloaded file into your Tesseract `tessdata` folder. On Windows this is usually:

   `C:\Program Files\Tesseract-OCR\tessdata\khm.traineddata`

3. Restart the app and choose **Khmer** from the language dropdown before uploading an image.

If you still see no output for Khmer, try the `tessdata_best` or `tessdata_fast` variants or confirm your Tesseract installation path and permissions.
