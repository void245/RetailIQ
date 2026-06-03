import logging
from flask import Blueprint, request, jsonify

from app.services.upload_service import UploadService

# ======================================================
# LOGGER CONFIG
# ======================================================

logger = logging.getLogger(__name__)

# ======================================================
# BLUEPRINT
# ======================================================

upload_bp = Blueprint('upload_bp', __name__)

# ======================================================
# UPLOAD ROUTE - SIMPLE FILE UPLOAD & STORAGE
# ======================================================

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload and store dataset file using UploadService.
    
    Responsibility: Orchestrate upload workflow
    - Validate file
    - Save to disk
    - Register metadata
    - Return dataset_id
    """
    
    try:
        logger.info("Starting file upload process...")
        
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({
                "success": False,
                "message": "No file part in request"
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({
                "success": False,
                "message": "No file selected"
            }), 400
        
        logger.info(f"Processing file: {file.filename}")
        upload_service = UploadService()
        result = upload_service.handle_upload(file)
        
        if not result['success']:
            logger.error(f"Upload failed: {result['message']}")
            return jsonify(result), 400
        
        logger.info(f"File uploaded with dataset_id: {result['dataset_id']}")
        
        return jsonify({
            "success": True,
            "message": result['message'],
            "dataset_id": result['dataset_id']
        }), 201
    
    except Exception as e:
        logger.exception(f"Unexpected error during upload: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred during upload",
            "error": str(e)
        }), 500