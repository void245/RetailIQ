from flask import Blueprint, request, jsonify

from app.services.validation_service import allowed_file,validate_file
from app.services.file_service import save_uploaded_file
from app.services.summary_service import generate_daataset_summary

upload_bp = Blueprint('upload_bp', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    validation_error = validate_file()

    if validation_error:
        return jsonify(
            {
                "success" : False ,
                "message" : validation_error
            }
        )
    
    file = request.files['file']

    if not allowed_file(file):
        return jsonify(
            {
                "success" : False ,
                "message" : "File type not allowed"
            }
        ) , 400
    
    saved_path = save_uploaded_file(file)

    dataset_summary = generate_daataset_summary(saved_path)

    return jsonify(
        {
            "success": True,
            "message": "File uploaded and processed successfully",
        }
    ), 200