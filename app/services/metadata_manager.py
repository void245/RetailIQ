import json
import uuid
import os
from datetime import datetime
from app.config import Config

class MetadataManager:
    def __init__(self):
        self.metadata_dir = os.path.join(Config.BASE_DIR, "metadata")
        self.metadata_file = os.path.join(self.metadata_dir, 'datasets_metadata.json')
        self._ensure_metadata_file()

    def _ensure_metadata_file(self) :
        if not os.path.exists(self.metadata_dir):
            os.makedirs(self.metadata_dir, exist_ok = True)
        if not os.path.exists(self.metadata_file):
            with open (self.metadata_file, 'w')as f:
                json.dump({},f)


    def _load_metadata(self) :
      
       try :
           self._ensure_metadata_file()

           with open(self.metadata_file, 'r')as f:
               return json.load(f)
       except json.JSONDecodeError:
           print("Error: Metadata file is corrupted. Reinitializing.")
           return{}
       except FileNotFoundError:
              print("Error: Metadata file not found. ")
              return {}
       except Exception as e:
           print(f"Unexpected error while loading metadata: {e}")
           return {}
       
    def _save_metadata(self,metadata_dict) :
        try:
            with open(self.metadata_file, 'w')as f:
                json.dump(metadata_dict, f, indent=4)
        except Exception as e:
            print(f"Error saving metadata: {e}")

    def register_dataset(self, file, file_path):
         """Create new dataset entry and return dataset_id"""
         # GENERATE DATASET_ID , CREATE METADATA OBJECT 
         # SAVE TO JSON , RETURN DATASET_ID

         dataset_id = str(uuid.uuid4())

         # extracting file info 
         filename = file.filename
         file_size = os.path.getsize(file_path)
         file_extension = os.path.splitext(filename)[1]
         upload_time = datetime.now().isoformat()
         
         metadata_entry = {
             "dataset_id" : dataset_id,
             "filename":filename,
             "file_path": file_path,
             "file_size":file_size,
             "file_extension":file_extension,
             "upload_time": upload_time,
             "status":"uploaded"
         }
         all_metadata = self._load_metadata()

         all_metadata[dataset_id] = metadata_entry
         try:

           self._save_metadata(all_metadata)
         except Exception as e:
             print(f"Error saving metadata: {e}")
             return None
         return dataset_id 
    
    def get_dataset(self,dataset_id):
        """Return metadata for a given dataset_id"""
        all_metadata = self._load_metadata()

        req_data = all_metadata.get(dataset_id)

        if not req_data:
            print(f"Dataset with id {dataset_id} not found.")
            return None

        return req_data