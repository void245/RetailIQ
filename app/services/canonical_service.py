#--------------------------------------------------------
# SCHEMA INTELLIGENCE ENGINE
#---------------------------------------------------------

# THIS MODULE PROVIDE SERVICES :

# 1. TO NORMALIZE THE DATASET
# 2. MAP ALIASES 
# 3. RENAME DATASET COLUMNS 
# 4.DETECT UNMAPPED FIELDS
# 5. GENERATE MAPPING REPORT

import re 
import logging
import pandas as pd 
from app.services.dataset_reader import read_dataset
from app.services.config_loader import ConfigManager
from typing import Dict, List, Tuple

#---------------------------------------------------------
# LOGGER CONFIG
#---------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

config = ConfigManager()

#---------------------------------------------------------
# PHASE 1: COLUMN NORMALIZATION
#---------------------------------------------------------

def normalize_column_name(column_name):
    """
        Normalize the column name by converting it to lowercase and replacing spaces with underscores.
    """
    normalized_name = column_name.strip().lower()
    normalized_name = re.sub(r'[^a-z0-9 ]', '', normalized_name)
    normalized_name = normalized_name.replace(' ', '_')

    return normalized_name

#---------------------------------------------------------
# PHASE 2 : NORMALIZE DATASET COLUMNS
#---------------------------------------------------------

def normalize_dataset_columns(df):
    """
        Normalize the column names of the given DataFrame.
    """

    logger.info(
        "Normalizing dataset columns"
    )

    df.columns = [normalize_column_name(col) for col in df.columns]

    logger.info(
        "Dataset columns normalized"
    )
    return df

#----------------------------------------------------------
# LOAD CONFIG AND CANONICAL SCHEMA
#----------------------------------------------------------

canonical_schema = config.get_canonical_schema()

#----------------------------------------------------------
# PHASE 3 : MAP ALIASES TO CANONICAL FIELDS
#----------------------------------------------------------

def build_column_mapping(dataframe_columns : List[str]) -> Tuple[Dict[str,str],List[str]]:
    """
        Build a mapping from the dataset columns to the canonical fields based on the config.
    """

    logger.info(
        "Building column mappig to canonical fields"
    )

    mapping = {}
    unmapped_columns = []

    #----------------------------------------------------
    # LOOP THROUGH UPLOADED COLUMNS
    #----------------------------------------------------
    for uploaded_column in dataframe_columns :
        mapped = False

        #------------------------------------------------
        # LOOP THROUGH CANONICAL SCHEMA
        #------------------------------------------------

        for canonical_field, aliases in canonical_schema.items():

            normalized_aliases = [normalize_column_name(alias) for alias in aliases]

            # include canonical field itself

            normalized_aliases.append(normalize_column_name(canonical_field))

            #------------------------------------------------
            # CHECK FOR MATCH
            #------------------------------------------------

            if uploaded_column in normalized_aliases :

                mapping[uploaded_column] = canonical_field
                mapped = True

                logger.info(
                    f"Mapped column : "
                    f"{uploaded_column} -> {canonical_field}"
                )

                break

            #-----------------------------------------------
            # NO MATCH FOUND
            #-----------------------------------------------

            if not mapped :
                unmapped_columns.append(uploaded_column)

                logger.warning(
                    f"No mapping found for column : {uploaded_column}"
                )

                return mapping, unmapped_columns
            

#---------------------------------------------------------------
#APPLY CANONICAL TRANSFORMATION
#---------------------------------------------------------------

def apply_canonical_mapping(df : pd.DataFrame , mapping : Dict[str,str]) -> pd.DataFrame :
   """
      RENAME DATAFRAME COLUMN USING CANONICAL MAPPING
   """

   logger.info(
       "Applying canonical transformation."
   )
   transformed_df = df.rename(columns= mapping)

   return transformed_df

#-----------------------------------------------------------------
# GENERATE MAPPING REPORT
#-----------------------------------------------------------------

def generate_mapping_report(mapping : Dict[str,str], unmapped_columns : List[str]) -> Dict :
    """
        Generate a mapping report summarizing the mapping results.
    """
    report = {
        "mapped_columns" : mapping ,
        "unmapped_columns" : unmapped_columns,
        "total_mapped_columns" : len(mapping),
        "total_unmapped_columns" : len(unmapped_columns)
    }

    logger.info(
        f"Mapping report generated : {report}"
    )
    
    return report

#-------------------------------------------------------------------
# MASTER CANONICAL PIPELINE
#-------------------------------------------------------------------

def process_canonical_mapping(df : pd.DataFrame) -> Tuple[pd.DataFrame, Dict] :
    """
    Complete canonical transformation pipeline.

    Pipeline:
    ---------
    Raw DataFrame
        ↓
    Normalize Columns
        ↓
    Build Mapping
        ↓
    Apply Canonical Transformation
        ↓
    Generate Mapping Report
        ↓
    Return Processed DataFrame

    """
    
    #----------------------------------------------------
    # 1. NORMALIZE COLUMNS
    #----------------------------------------------------

    normalized_df = normalize_dataset_columns(df)

    #----------------------------------------------------
    # 2.BUILD MAPPING
    #----------------------------------------------------

    mapping , unmapped_columns = build_column_mapping(
        normalized_df.columns.tolist()
    )
    
    #----------------------------------------------------
    # APPLY CANONICAL TRANSFORMATION
    #----------------------------------------------------

    processed_df = apply_canonical_mapping(normalized_df , mapping)

    #----------------------------------------------------
    # GENERATE MAPPING REPORT
    #----------------------------------------------------

    mapping_report = generate_mapping_report(mapping, unmapped_columns)

    logger.info(
        "Canonical mapping process completed."
    )

    return processed_df , mapping_report