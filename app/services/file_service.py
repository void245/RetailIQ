from fileinput import filename
import os
import uuid
from werkzeug.utils import secure_filename
from app.config import Config

def save_uploaded_file(file):

    filename_parts = os.path.splitext(file.filename)
    extension = filename_parts[1].lower() 

    if extension == '.csv' :
        subfolder = 'csv_files' 
    elif extension == '.xlsx' :
        subfolder = 'excel_files'
    else : 
        raise ValueError("Unsupported file type")    
    
    target_folder = os.path.join(Config.UPLOAD_FOLDER, subfolder)
    os.makedirs(target_folder, exist_ok=True)

    original_filename = secure_filename(file.filename)

    unique_filename = ( f"{uuid.uuid4()}_{original_filename}")

    save_path = os.path.join(target_folder, unique_filename)

    file.save(save_path)

    return save_path