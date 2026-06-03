import logging
from flask import Blueprint, request, jsonify 
from app.services.dataset_reader import read_dataset
from app.services.canonical_service import normalize_dataset_columns
from app.services.schema_validation import SchemaValidationServices
from app.services.cleaning_services import CleaningService
from app.services.summary_service import SummaryService
from app.services.metadata_manager import MetadataManager
from app.services.retail_analytics_service.retail_analytics_service import RetailAnalyticsService

# ======================================================
# LOGGER CONFIG
# ======================================================

logger = logging.getLogger(__name__)

# ======================================================
# BLUEPRINT
# ======================================================

analytics_bp = Blueprint('analytics', __name__)

# ======================================================
# HELPER FUNCTION: VALIDATE ANALYSIS REQUEST
# ======================================================

def validate_analysis_request():
    """
    Validate the analysis request format and retrieve file_path from dataset_id.
    
    Returns:
        tuple: (error_message, file_path) - error_message is None if valid
    """
    
    if not request.is_json:
        return "Request must be JSON format", None
    
    request_data = request.get_json()
    
    if not request_data or "dataset_id" not in request_data:
        return "Missing required field: dataset_id", None
    
    dataset_id = request_data.get("dataset_id")
    
    if not dataset_id or not isinstance(dataset_id, str):
        return "dataset_id must be a non-empty string", None
    
    metadata_manager = MetadataManager()
    metadata = metadata_manager.get_dataset(dataset_id)
    
    if not metadata:
        return f"Dataset not found: {dataset_id}", None
    
    file_path = metadata.get('file_path')
    
    if not file_path:
        return f"File path not found for dataset: {dataset_id}", None
    
    return None, file_path


# ======================================================
# ANALYTICS ROUTES - COMPLETE PIPELINE
# ======================================================

@analytics_bp.route('/analyze', methods=['POST']) 
def analyze_dataset():
    """
    Analyze existing dataset with complete pipeline.
    
    Responsibility: Analyze only
    Pipeline:
    1. Validate request
    2. Read dataset
    3. Canonicalization
    4. Schema Validation
    5. Data Cleaning
    6. Analytics
    7. Response
    
    Expected JSON request:
    {
        "file_path": "/path/to/uploaded/file.csv"
    }
    
    Returns comprehensive data analysis report.
    """
    
    try:
        # ======================================================
        # STEP 1: VALIDATE REQUEST
        # ======================================================
        
        logger.info("Step 1: Validating request...")
        validation_error, file_path = validate_analysis_request()
        
        if validation_error:
            logger.error(f"Validation failed: {validation_error}")
            return jsonify({
                "success": False,
                "message": validation_error,
                "error": validation_error
            }), 400
        
        logger.info(f"Request valid for: {file_path}")
        
        # ======================================================
        # STEP 2: READ DATASET
        # ======================================================
        
        logger.info("Step 2: Reading dataset...")
        df, error_message = read_dataset(file_path)
        
        if df is None:
            logger.error(f"Dataset read failed: {error_message}")
            return jsonify({
                "success": False,
                "message": "Failed to read dataset",
                "error": error_message,
                "file_path": file_path
            }), 400
        
        logger.info(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
        
        # ======================================================
        # STEP 3: CANONICALIZATION
        # ======================================================
        
        logger.info("Step 3: Canonicalizing dataset...")
        df = normalize_dataset_columns(df)
        logger.info("Canonicalization completed")
        
        # ======================================================
        # STEP 4: SCHEMA VALIDATION
        # ======================================================
        
        logger.info("Step 4: Validating schema...")
        schema_validator = SchemaValidationServices()
        schema_validator.validate_schema(df, None)
        schema_report = schema_validator.report
        logger.info("Schema validation completed")
        
        # ======================================================
        # STEP 5: DATA CLEANING
        # ======================================================
        
        logger.info("Step 5: Cleaning data...")
        cleaning_service = CleaningService()
        df_cleaned = cleaning_service.clean_dataframe(df)
        logger.info(f"Data cleaned: {df_cleaned.shape[0]} rows remaining (removed {df.shape[0] - df_cleaned.shape[0]} rows)")
        
        # ======================================================
        # STEP 6: ANALYTICS
        # ======================================================
        
        logger.info("Step 6: Generating comprehensive retail analytics...")
        dataset_id = request.get_json().get("dataset_id")
        analytics_service = RetailAnalyticsService(df_cleaned, dataset_id=dataset_id)
        analysis_report = analytics_service.analyze()
        logger.info("Comprehensive retail analytics generated successfully")
        
        # ======================================================
        # STEP 7: RESPONSE
        # ======================================================
        
        logger.info("Returning response...")
        return jsonify({
            "success": True,
            "message": "Data analysis completed successfully",
            "data": analysis_report,
            "metadata": {
                "file_path": file_path,
                "rows_original": df.shape[0],
                "rows_after_cleaning": df_cleaned.shape[0],
                "columns_analyzed": df_cleaned.shape[1],
                "analysis_type": "comprehensive",
                "schema_validation": schema_report
            }
        }), 200
    
    except Exception as e:
        logger.exception(f"Unexpected error during analysis: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred during analysis",
            "error": str(e)
        }), 500


# ======================================================
# QUICK ANALYSIS ENDPOINT
# ======================================================

@analytics_bp.route('/analyze/quick', methods=['POST'])
def quick_analyze():
    """
    Quick analysis - skips cleaning, returns basic stats.
    
    Expected JSON request:
    {
        "file_path": "/path/to/uploaded/file.csv"
    }
    
    Returns: overview, data_quality, statistics
    """
    
    try:
        # Validate request
        validation_error, file_path = validate_analysis_request()
        
        if validation_error:
            logger.error(f"Validation failed: {validation_error}")
            return jsonify({
                "success": False,
                "message": validation_error
            }), 400
        
        logger.info(f"Quick analysis requested for: {file_path}")
        
        # Read dataset
        df, error_message = read_dataset(file_path)
        
        if df is None:
            logger.error(f"Dataset read failed: {error_message}")
            return jsonify({
                "success": False,
                "message": "Failed to read dataset",
                "error": error_message
            }), 400
        
        # Generate full summary
        summary_service = SummaryService()
        analysis_report = summary_service.generate_complete_summary(df)
        
        # Return only overview and data quality
        quick_response = {
            "overview": analysis_report.get("overview", {}),
            "data_quality": analysis_report.get("data_quality", {}),
            "statistics": analysis_report.get("statistics", {})
        }
        
        return jsonify({
            "success": True,
            "message": "Quick analysis completed",
            "data": quick_response,
            "metadata": {
                "file_path": file_path,
                "rows_analyzed": df.shape[0],
                "columns_analyzed": df.shape[1],
                "analysis_type": "quick"
            }
        }), 200
    
    except Exception as e:
        logger.exception(f"Error during quick analysis: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500
        
        logger.info(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
        
        # ======================================================
        # STEP 3: GENERATE COMPREHENSIVE ANALYSIS
        # (includes data cleaning & validation)
        # ======================================================
        
        logger.info("Starting comprehensive data analysis...")
        summary_service = SummaryService()
        analysis_report = summary_service.generate_complete_summary(df)
        
        logger.info("Analysis completed successfully")
        
        # ======================================================
        # STEP 4: BUILD & RETURN SUCCESS RESPONSE
        # ======================================================
        
        return jsonify({
            "success": True,
            "message": "Data analysis completed successfully",
            "data": analysis_report,
            "metadata": {
                "file_path": file_path,
                "rows_analyzed": df.shape[0],
                "columns_analyzed": df.shape[1],
                "analysis_type": "comprehensive"
            }
        }), 200
    
    except Exception as e:
        logger.exception(f"Unexpected error during analysis: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred during analysis",
            "error": str(e)
        }), 500


# ======================================================
# OPTIONAL: LIGHTWEIGHT ANALYSIS ENDPOINT
# ======================================================

@analytics_bp.route('/analyze/quick', methods=['POST'])
def quick_analyze():
    """
    Quick analysis endpoint - returns only basic stats.
    
    Expected JSON request:
    {
        "file_path": "/path/to/uploaded/file.csv"
    }
    
    Returns: overview, data_quality, statistics
    """
    
    try:
        # Validate request
        validation_error, file_path = validate_analysis_request()
        
        if validation_error:
            logger.error(f"Validation failed: {validation_error}")
            return jsonify({
                "success": False,
                "message": validation_error
            }), 400
        
        logger.info(f"Quick analysis requested for: {file_path}")
        
        # Read dataset
        df, error_message = read_dataset(file_path)
        
        if df is None:
            logger.error(f"Dataset read failed: {error_message}")
            return jsonify({
                "success": False,
                "message": "Failed to read dataset",
                "error": error_message
            }), 400
        
        # Generate full summary
        summary_service = SummaryService()
        analysis_report = summary_service.generate_complete_summary(df)
        
        # Return only overview and data quality
        quick_response = {
            "overview": analysis_report.get("overview", {}),
            "data_quality": analysis_report.get("data_quality", {}),
            "statistics": analysis_report.get("statistics", {})
        }
        
        return jsonify({
            "success": True,
            "message": "Quick analysis completed",
            "data": quick_response,
            "metadata": {
                "file_path": file_path,
                "rows_analyzed": df.shape[0],
                "columns_analyzed": df.shape[1],
                "analysis_type": "quick"
            }
        }), 200
    
    except Exception as e:
        logger.exception(f"Error during quick analysis: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500