import logging 
import pandas as pd 
from pathlib import Path
from app.config import ALLOWED_EXTENSIONS


#======================================================
# LOGGER CONFIG
#======================================================

logger = logging.getLogger(__name__)

#======================================================
# DATASET READER SERVICES
#======================================================

def read_dataset(file_path):
    """
        Read dataset from the given file path and return a pandas DataFrame.
    """


    try :
        path = Path(file_path)

        logger.info(
            f"starting datasey ingestion"
        )

        if not path.exists():
            logger.error(
                f"Dataset file not found at path : {file_path}"
            )
            
            return (
                None, "Dataset not found"

            )
        
        # EXTENSION CHECK

        extension = path.suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            logger.error(
                f"Unsupported file extension : {extension}"
            )

            return (
                None ,
                f"Unsupported file extension : {extension}"
            )
        
        # read dataset 

        if extension == '.csv' :
            try :
                logger.info(
                    "Reading csv dataset"
                )

                df = pd.read_csv(file_path)
            except UnicodeDecodeError :
                logger.warning (
                    "UTF-8 decoding failed. "
                    "Trying latin1 encoding."
                )

                df = pd.read_csv(file_path, encoding = "latin1")
        elif extension == ".xlsx" :
            logger.info(
                "Reading Excel Dataset"
            )

            df = pd.read_excel(file_path) 

        #===============================================
        # EMPTY DATAFRAME
        # ==============================================

        if df.empty :
            logger.warning(
                f"Empty dataset : {file_path}"
            )  
            return (
                None ,
                "Uploaded dataset is empty"
            )
        
        #===============================================
        # SUCCESS
        #===============================================

        logger.info(
            "Dataset loaded successfully | "
            f"Rows: {df.shape[0]} | "
            f"Columns: {df.shape[1]}"
        )

        #===============================================
        #RETURN RAW DF
        #===============================================

        return (
            df ,
            None
        )
    
    # empty csv error
    except pd.errors.EmptyDataError :
        logger.error(
            "uploaded CSV is empty."
        )
        return (
            None,
            "uploaded CSV is empty."
        )
    
    # CSV PARSING ERROR


    except pd.errors.ParserError as e:
        logger.error(
            f"Error parsing CSV file : {str(e)}"
        )
        return (
            None,
            f"Error parsing CSV file : {str(e)}"
            )
    
    except Exception as e :
        logger.exception(
            "Unexpected dataset ingestion occur."
        )
        return (
            None,
            f"Unexpected dataset ingestion error: {str(e)}"
        )