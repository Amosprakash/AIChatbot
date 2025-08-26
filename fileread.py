import os
import hashlib
from werkzeug.utils import secure_filename
from flask import session
import re
file_cache = {}

# Store active merge file name per session
MERGE_DIR = r"D:\Python\Deep Learning\uploads"
os.makedirs(MERGE_DIR, exist_ok=True)
last_file_path = os.path.join(MERGE_DIR, "last_used.txt")


def extract_text_from_file(file_storage, file_bytes=None, file_hash=None):
    try:
        filename = file_storage.filename.lower()

        if file_bytes is None:
            file_bytes = file_storage.read()
        if file_hash is None:
            file_hash = hashlib.md5(file_bytes).hexdigest()

        if file_hash in file_cache:
            return file_cache[file_hash]

        text = ""
        if filename.endswith(".pdf"):
            import fitz
            import pytesseract
            from PIL import Image
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                page_text = page.get_text("text")
                if page_text:
                    text += page_text

            if not text.strip():
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page in doc:
                    pix = page.get_pixmap(dpi=150)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples).convert("L")
                    text += pytesseract.image_to_string(img, config="--psm 6")

        elif filename.endswith(".docx"):
            import docx
            file_storage.stream.seek(0)
            doc = docx.Document(file_storage)
            text = "\n".join(p.text for p in doc.paragraphs)

        elif filename.endswith(".xlsx"):
            import pandas as pd
            file_storage.stream.seek(0)
            df = pd.read_excel(file_storage, engine='openpyxl')
            text = df.to_json(orient="records", force_ascii=False, indent=2)

        elif filename.endswith(".xls"):
            import pandas as pd
            file_storage.stream.seek(0)
            df = pd.read_excel(file_storage, engine='xlrd')
            text = df.to_json(orient="records", force_ascii=False, indent=2)

        elif filename.endswith(".csv"):
            import pandas as pd
            file_storage.stream.seek(0)
            df = pd.read_csv(file_storage)
            text = df.to_json(orient="records", force_ascii=False, indent=2)

        elif filename.endswith(".txt"):
            text = file_bytes.decode("utf-8", errors="ignore")

        elif filename.endswith((".png", ".jpg", ".jpeg")):
            from PIL import Image
            import pytesseract
            file_storage.stream.seek(0)
            image = Image.open(file_storage)
            text = pytesseract.image_to_string(image)

        else:
            return "❌ Unsupported file type."

        file_cache[file_hash] = text
        return text

    except Exception as e:
        return f"❌ Error while processing file: {str(e)}"




def sanitize_filename(name):
    return secure_filename(name.replace(" ", "_").lower()) + ".txt"

def extract_and_merge_files(uploaded_files, command_text=None):
    # Step 1: Determine or override active merge filename
    active_file_name = session.get("active_merge_file", "default_merged.txt")

    if command_text:
        extracted_name = extract_filename_from_request(command_text)
        if extracted_name:
            active_file_name = extracted_name
            session["active_merge_file"] = active_file_name

        # backward compatibility
        elif command_text.lower().startswith("merge with"):
            parts = command_text.lower().split("merge with")
            if len(parts) > 1:
                active_file_name = sanitize_filename(parts[1].strip())
                session["active_merge_file"] = active_file_name

    # Step 2: Extract and build merged content
    merged_text = ""
    for file_storage in uploaded_files:
        file_bytes = file_storage.read()
        file_storage.stream.seek(0)  # Reset for re-use
        file_hash = hashlib.md5(file_bytes).hexdigest()
        extracted_text = extract_text_from_file(file_storage, file_bytes, file_hash)

        merged_text += f"\n\n### Start of Document: {file_storage.filename} ###\n"
        merged_text += extracted_text.strip()
        merged_text += f"\n### End of Document: {file_storage.filename} ###\n"

    # Step 3: Write merged text to disk
    file_path = os.path.join(MERGE_DIR, active_file_name)
    print(f"📁 Writing to: {file_path}")
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(merged_text + "\n")

    # Step 4: Track last used
    with open(os.path.join(MERGE_DIR, "last_used.txt"), "w", encoding="utf-8") as tracker:
        tracker.write(active_file_name)

    return merged_text
def extract_target_filename(prompt):
    prompt = prompt.lower().strip()

    # Remove known prefix patterns
    prompt = re.sub(r"^(ask|question about)\s+", "", prompt)
    prompt = prompt.replace("merged file", "").replace("about", "").strip()

    if prompt:
        filename = sanitize_filename(prompt)
        return filename

    # fallback to last_used.txt
    try:
        with open(os.path.join(MERGE_DIR, "last_used.txt"), "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "default_merged.txt"
import re
from flask import url_for

def extract_filename_from_request(prompt):
    prompt = prompt.lower().strip()

    if "last file" in prompt or "latest merged file" in prompt or "download last" in prompt:
        try:
            with open(os.path.join(MERGE_DIR, "last_used.txt"), "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    # Try extracting filename from prompt
    match = re.search(r"(download|get|send|fetch)\s+(the\s+)?file\s*(named|called)?\s*([\w\-\.]+)", prompt)
    if match:
        return match.group(4)

    # Or fallback to a simple guess
    words = prompt.split()
    for word in words:
        if word.endswith((".txt", ".pdf", ".xlsx", ".xls", ".csv")):
            return word

    return None

import re

def is_file_creation_request(user_input):
    """
    Detect if the user's prompt is asking to create a file.
    Example matches:
    - "Create this as report.xlsx"
    - "Make this into PDF"
    - "Save as summary.txt"
    - "Create this as worklog.pdf"
    """
    if not user_input:
        return False

    file_keywords = ["create this as", "make this into", "save as", "generate file as"]
    file_extensions = [".pdf", ".xlsx", ".csv", ".txt", ".docx"]

    lower_input = user_input.lower()
    if any(keyword in lower_input for keyword in file_keywords):
        return any(ext in lower_input for ext in file_extensions)

    return False
def is_download_request(prompt):
    """
    Detect if the user is requesting to download a file.
    Matches prompts like:
    - "download the file"
    - "get worklog.xlsx"
    - "send last file"
    - "fetch report.pdf"
    """
    if not prompt:
        return False

    prompt = prompt.lower()
    keywords = ["download", "get", "fetch", "send", "retrieve"]

    has_keyword = any(k in prompt for k in keywords)
    has_extension = any(ext in prompt for ext in [".txt", ".pdf", ".xlsx", ".csv", ".docx"]) or \
                    "last file" in prompt or "latest file" in prompt

    return has_keyword and has_extension
