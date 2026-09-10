import os
import uuid
from pathlib import Path

UPLOAD_ROOT = Path(os.getenv('SIAG_UPLOAD_DIR', 'uploads'))
MEDIA_DIR = UPLOAD_ROOT / 'media'
DOCS_DIR = UPLOAD_ROOT / 'documents'
THUMBS_DIR = UPLOAD_ROOT / 'thumbs'


def ensure_dirs():
    for d in (MEDIA_DIR, DOCS_DIR, THUMBS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def save_upload(uploaded_file, subfolder='media') -> str:
    """
    Save an uploaded Streamlit file object and return the stored filename.
    Caller should also insert metadata into the DB.
    """
    ensure_dirs()
    dest = MEDIA_DIR if subfolder == 'media' else DOCS_DIR
    ext = Path(uploaded_file.name).suffix
    stored_name = f"{uuid.uuid4().hex}{ext}"
    out_path = dest / stored_name
    with open(out_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return str(out_path)


def delete_file(path_str: str):
    try:
        Path(path_str).unlink(missing_ok=True)
    except Exception:
        pass
