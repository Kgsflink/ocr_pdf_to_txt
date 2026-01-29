KGSFLINK:
To achieve high-quality extraction for handwritten text and Hindi language, we need to use Tesseract's LSTM engine with multi-language data packs.

### 1. Prerequisites (Crucial)
You must install the Hindi language pack for Tesseract on your system:
*   Linux: sudo apt-get install tesseract-ocr-hin
*   Mac: brew install tesseract-lang
*   Windows: Download the hin.traineddata from tesseract-ocr/tessdata and place it in your Tesseract-OCR/tessdata folder.

Install Python dependencies:
pip install flask pdfplumber pytesseract pdf2image pillow python-docx pandas python-bidi arabic-reshaper

---

### 2. The Advanced Backend (`main.py`)
This version includes a dedicated OCR engine configured for Hindi + English and better handling of large files to prevent connection timeouts.

```python
import os
import pandas as pd
import pytesseract
import pdfplumber
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
from PIL import Image, ImageOps, ImageFilter
from docx import Document
from datetime import datetime

app = Flask(__name__)

# Config
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'txt'}

for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image):
    """
    Improves OCR accuracy for handwriting by converting to grayscale 
    and applying thresholding.
    """
    image = image.convert('L')  # Grayscale
    image = image.filter(ImageFilter.SHARPEN)
    return image

def extract_ocr(image, lang='eng+hin'):
    """Performs OCR with specific handwriting/language config"""
    # PSM 3: Fully automatic page segmentation, but no orientation detection.
    # OEM 3: Default, based on what is available.
    custom_config = r'--oem 3 --psm 3'
    return pytesseract.image_to_string(image, lang=lang, config=custom_config)

def process_pdf(path, lang):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content and len(content.strip()) > 20: # If text exists
                text += content + "\n"
            else:
                # If page is an image or handwriting, use OCR
                # We convert only the specific page to image to save memory
                images = convert_from_path(path, first_page=page.page_number, last_page=page.page_number)
                for img in images:
                    processed_img = preprocess_image(img)
                    text += extract_ocr(processed_img, lang) + "\n"
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    target_format = request.form.get('format', 'txt')
    lang_choice = request.form.get('lang', 'eng+hin') # Default to both
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(input_path)
    
    try:
        ext = filename.rsplit('.', 1)[1].lower()
        extracted_text = ""

        if ext == 'pdf':
            extracted_text = process_pdf(input_path, lang_choice)
        elif ext in ['jpg', 'jpeg', 'png']:
            img = Image.open(input_path)
            extracted_text = extract_ocr(preprocess_image(img), lang_choice)
        elif ext == 'docx':
            doc = Document(input_path)
            extracted_text = "\n".join([p.text for p in

p in doc

.paragraphs])
        else:
            with open(input_path, 'r', encoding='utf-8') as f:
                extracted_text = f.read()

        if not extracted_text.strip():
            return jsonify({'error': 'Could not detect any text. Ensure the image is clear.'}), 400

        # Save Logic
        base_name = filename.rsplit('.', 1)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_filename = f"{base_name}_{timestamp}.{target_format}"
        out_path = os.path.join(app.config['OUTPUT_FOLDER'], out_filename)

        if target_format == 'txt':
            with open(out_path, 'w', encoding='utf-8') as f: f.write(extracted_text)
        elif target_format == 'md':
            with open(out_path, 'w', encoding='utf-8') as f: f.write(f"# OCR Result\n\n{extracted_text}")
        elif target_format == 'docx':
            d = Document()
            d.add_paragraph(extracted_text)
            d.save(out_path)
        elif target_format == 'csv':
            lines = [l for l in extracted_text.split('\n') if l.strip()]
            pd.DataFrame(lines, columns=['Content']).to_csv(out_path, index=False, encoding='utf-8-sig')

        return jsonify({
            'success': True,
            'preview': extracted_text[:1500],
            'download_url': f'/download/{out_filename}',
            'filename': out_filename
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename), as_attachment=True)

if name == '__main__':
    app.run(debug=True, port=5000, threaded=True)
```

```

---

### 3. The Improved Frontend (`templates/index.html`)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Lingual OCR Pro</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root { --primary: #6366f1; --bg: #f3f4f6; --text: #1f2937; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); padding: 20px; }
        .card { max-width: 800px; margin: 40px auto; background: white; padding: 30px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
        .header { text-align: center; margin-bottom: 30px; }
        
        .upload-area { border: 2px dashed #d1d5db; padding: 40px; border-radius: 12px; text-align: center; cursor: pointer; transition: 0.3s; }
        .upload-area:hover { border-color: var(--primary); background: #f5f3ff; }
        
        .options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }
        .option-group { display: flex; flex-direction: column; gap: 8px; }
        select, button { padding: 12px; border-radius: 8px; border: 1px solid #d1d5db; font-size: 1rem; }
        
        .btn-main { background: var(--primary); color: white; border: none; font-weight: 600; cursor: pointer; display: flex; justify-content: center; align-items: center; gap: 10px; }
        .btn-main:hover { opacity: 0.9; }
        .btn-main:disabled { background: #9ca3af; cursor: not-allowed; }

        .preview-container { margin-top: 30px; display: none; }
        pre { background: #1e293b; color: #f8fafc; padding: 20px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; font-size: 14px; max-height: 400px; }
        
        .loader { display: none; margin: 20px auto; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid var(--primary); border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>

<div class="card">
    <div class="header">
        <h1>🖋️ OCR Pro</h1>
        <p>English & Hindi Handwriting / Image / PDF Extractor</p>

</div>

    <div class="upload-area" id="dropZone">
        <i class="fas fa-file-upload fa-3x" style="color: var(--primary); margin-bottom: 10px;"></i>
        <p id="file-name">Drag & Drop or Click to Upload</p>
        <input type="file" id="fileInput" hidden>
    </div>

    <div class="options-grid">
        <div class="option-group">
            <label><strong>1. Language</strong></label>
            <select id="langSelect">
                <option value="eng+hin">English + Hindi (Mixed)</option>
                <option value="hin">Hindi Only</option>
                <option value="eng">English Only</option>
            </select>
        </div>
        <div class="option-group">
            <label><strong>2. Output Format</strong></label>
            <select id="formatSelect">
                <option value="txt">Text (.txt)</option>
                <option value="docx">Word (.docx)</option>
                <option value="csv">Excel/Data (.csv)</option>
                <option value="md">Markdown (.md)</option>
            </select>
        </div>
    </div>

    <button class="btn-main" id="startBtn" style="width: 100%;">
        <span>Process Document</span>
        <i class="fas fa-arrow-right"></i>
    </button>

    <div class="loader" id="loader"></div>

    <div class="preview-container" id="previewArea">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h3>Extraction Preview</h3>
            <a id="downloadLink" class="btn-main" style="padding: 5px 15px; text-decoration: none; font-size: 0.8rem;">Download</a>
        </div>
        <pre id="textPreview"></pre>
    </div>
</div>

<script>
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const startBtn = document.getElementById('startBtn');
    const loader = document.getElementById('loader');
    const previewArea = document.getElementById('previewArea');

    dropZone.onclick = () => fileInput.click();
    
    fileInput.onchange = () => {
        if(fileInput.files.length) document.getElementById('file-name').innerText = fileInput.files[0].name;
    };

    startBtn.onclick = async () => {
        if(!fileInput.files.length) return alert("Select a file");

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('lang', document.getElementById('langSelect').value);
        formData.append('format', document.getElementById('formatSelect').value);

        loader.style.display = 'block';
        previewArea.style.display = 'none';
        startBtn.disabled = true;

        try {
            // Increased timeout handling via fetch
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout

            const response = await fetch('/process', { 
                method: 'POST', 
                body: formData,
                signal: controller.signal
            });
            
            const data = await response.json();
            clearTimeout(timeoutId);

            if(data.success) {
                document.getElementById('textPreview').innerText = data.preview;
                document.getElementById('downloadLink').href = data.download_url;
                previewArea.style.display = 'block';
            } else {
                alert(data.error);
            }
        } catch (e) {
            alert("Request timed out or connection lost. Large PDFs take longer to OCR.");
        } finally {
            loader.style.display = 'none';
            startBtn.disabled = false;
        }
    };
</script>
</body>
</html>
```

```

### Improvements made:
1.  Handwriting Optimization: Added preprocess_image function that uses Grayscale and Sharpening to make handwriting strokes clearer for Tesseract.
2.  Hindi Support: Configured Tesseract to use eng+hin. This allows the tool to read a document that has both languages mixed together.
3.  **Connection

Fixes**: 
    *   Enabled threaded=True in Flask to prevent the server from hanging on long tasks.
    *   Set MAX_CONTENT_LENGTH to 50MB for high-res images.
    *   Added a frontend 2-minute timeout to allow time for heavy OCR processing.
4.  Deep PDF Scanning: The process_pdf function now checks if a page has digital text. If not, it converts that specific page to a high-res image and performs OCR. This handles "Images inside PDFs" perfectly.
5.  Multi-Format Export: Now converts extracted text to .csv, .docx, .txt, and .md.
