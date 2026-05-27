from app.config import Config
from flask import request

def allowed_file(file):
    """Validate : 
                 1.Extension 
                 2.MIME type
                 3. File size
    """

    filename = getattr(file, 'filename', '')

    #----------------------------------------
    # 1. Extension Check
    #----------------------------------------

    if '.' not in filename:
       return False
    
    extension = filename.rsplit('.', 1)[1].lower()

    if extension not in Config.ALLOWED_EXTENSIONS:
        return False
   
    #----------------------------------------
    # 2. MIME Type Check
    #----------------------------------------

    mime_type = file.content_type

    if mime_type not in Config.ALLOWED_MIME:
        return False
    
    #----------------------------------------
    # 3. File Size Check
    #----------------------------------------

    try :
        current_position = file.tell()

        file.stream.seek(0,2) # move to end of file
        file_size = file.stream.tell()

        file.stream.seek(current_position) # reset to original position

    except Exception as e:    
        data = file.read()
        file_size = len(data)

        try :
            file.seek(0)
        except Exception :
            pass
    return file_size <= Config.MAX_CONTENT_LENGTH     

def validate_file():
    # File exists?
    if 'file' not in request.files:
        return "No file part in request"

    file = request.files['file']

    # Filename empty?
    if file.filename == '':
        return "No file selected"

    # Validate file
    if not allowed_file(file):
        return "Invalid file"

    return None