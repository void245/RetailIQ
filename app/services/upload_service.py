from app.services.validation_service import validate_file
from app.services.file_service import save_uploaded_file
from app.services.metadata_manager import MetadataManager


class UploadService:
    def __init__(self):
        self.metadata_manager = MetadataManager()

    def handle_upload(self, file):
        # step 1 : validate file
        if not validate_file(file):
            return {"success": False, "message": "Invalid file type. Only CSV and Excel files are allowed."}
        
        # step 2 : save file 

        file_path = save_uploaded_file(file)

        # step 3 : register metadata

        registration_result = self.metadata_manager.register_dataset(file,file_path)

        # step 4 : return response
        if registration_result:
            return {"success": True, "message": "File uploaded and registered successfully.", "dataset_id": registration_result}
        else:
            return {"success": False, "message": "File uploaded but failed to register metadata."}     
        
        
