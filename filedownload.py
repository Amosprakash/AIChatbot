import os
from flask import send_file, abort

UPLOAD_FOLDER = r"D:\Python\Deep Learning\uploads"

def download_uploaded_file(filename):
    # Sanitize filename to avoid directory traversal
    safe_path = os.path.join(UPLOAD_FOLDER, os.path.basename(filename))

    if not os.path.isfile(safe_path):
        return abort(404, description="File not found.")

    return send_file(
        safe_path,
        as_attachment=True,
        download_name=filename
    )
