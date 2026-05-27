import os

class Config:

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    UPLOAD_FOLDER = os.path.join(
        os.getcwd(), 'temp_uploads'
    )

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    ALLOWED_EXTENSIONS = {
        'csv',
        'xlsx'
    }

    ALLOWED_MIME = {
        'text/csv',
        'application/vnd.ms-excel'
    }