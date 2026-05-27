import pandas as pd
import logging
import re
from app.services.config_loader import ConfigManager

# Logger setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

#================================================================
# CLEANING SERVICE - TEMPLATES FOR YOU TO BUILD
#================================================================

"""
TEMPLATE STRUCTURE:

You need to implement these methods:

1. __init__()
   - Load ConfigManager
   - Get canonical schema
   - Initialize self.report = {}
   - Initialize self.cleaning_log = []

2. clean_dataframe(df)
   - Main orchestration
   - Call all 6 cleaning steps
   - Return cleaned_df

3. _clean_nulls(df)
   - Replace "" with pd.NA
   - Remove rows where NOT nullable columns are NaN
   - Log and return df

4. _remove_duplicates(df)
   - Get dedup config from schema
   - Use df.drop_duplicates()
   - Log and return df

5. _trim_whitespace(df)
   - Loop columns with trim_whitespace = true
   - Use .str.strip()
   - Log and return df

6. _clean_currency_values(df)
   - Remove $€£ symbols using regex
   - Remove thousand separators (,)
   - Log and return df

7. _standardize_dates(df)
   - Find datetime columns
   - Use pd.to_datetime() with infer_datetime_format=True
   - Log and return df

8. _standardize_strings(df)
   - Lowercase if configured
   - Remove extra spaces
   - Log and return df

9. _generate_cleaning_report()
   - Build report dict with status, counts, operations
   - Store in self.report

10. get_cleaning_report()
    - Return self.report

11. get_dataframe()
    - Return self.df
"""

# SCHEMA REFERENCES YOU'LL NEED:
"""
# Get canonical fields
canonical_fields = self.schema.get("canonical_fields", {})

# For each field:
field_info = canonical_fields[column]
nullable = field_info.get("nullable", False)
datatype = field_info.get("datatype")  # "float64", "datetime", "string"
cleaning = field_info.get("cleaning", {})  # {"trim_whitespace": true, ...}

# Global rules
cleaning_rules = self.schema.get("cleaning_rules", {})
lowercase = cleaning_rules.get("lowercase_headers", False)

# Deduplication config
dedup = self.schema.get("deduplication", {})
dedup_enabled = dedup.get("enabled", False)
subset = dedup.get("subset", [])  # List of columns
"""

# PANDAS OPERATIONS YOU'LL USE:
"""
# Replace empty strings
df = df.replace('', pd.NA)

# Check nulls
df[df[column].isnull()].shape[0]  # Count nulls
df = df[df[column].notnull()]  # Remove nulls

# Remove duplicates
df = df.drop_duplicates(subset=['col1', 'col2'], keep='first')

# Trim whitespace
df[column] = df[column].str.strip()

# Remove currency symbols
df[column] = df[column].astype(str).str.replace(r'[$€£¥₹]', '', regex=True)

# Remove commas
df[column] = df[column].str.replace(',', '')

# Parse dates
df[column] = pd.to_datetime(df[column], errors='coerce', infer_datetime_format=True)

# Lowercase
df[column] = df[column].str.lower()

# Remove extra spaces
df[column] = df[column].str.replace(r'\s+', ' ', regex=True)
"""

class CleaningService:
    """
    Data Cleaning Service
    
    TODO: Build this class
    """
    
    def __init__(self):
        """
         Initialize
        """
        self.config = ConfigManager()
        self.schema = self.config.get_canonical_schema()
        self.report = {}
        self.cleaning_log = []
        pass
    
    def clean_dataframe(self, df):
        """
        Orchestration method
        Call all cleaning steps and return cleaned_df
        
        Execution Order:
        1. _clean_nulls
        2. _remove_duplicates
        3. _trim_whitespace
        4. _clean_currency_values
        5. _standardize_dates
        6. _standardize_strings
        
        Returns:
        --------
        cleaned_dataframe
        """
        
        logger.info("="*60)
        logger.info("STARTING DATA CLEANING PROCESS")
        logger.info("="*60)
        
        #-------------------------------------------------
        # SETUP PHASE
        #-------------------------------------------------
        
        # Record initial row/column count
        initial_rows = df.shape[0]
        initial_cols = df.shape[1]
        
        logger.info(f"Initial dataset: {initial_rows} rows, {initial_cols} columns")
        
        # Initialize report dictionary
        self.report = {
            "initial_rows": initial_rows,
            "initial_columns": initial_cols,
            "steps": {}
        }
        
        #-------------------------------------------------
        # STEP 1: CLEAN NULLS
        #-------------------------------------------------
        
        try:
            logger.info("\n[STEP 1] Cleaning null values...")
            df, report_nulls = self._clean_nulls(df)
            self.report["steps"]["clean_nulls"] = report_nulls
            self.report["steps"]["clean_nulls"]["status"] = "success"
            logger.info("✓ Null cleaning completed")
        except Exception as e:
            logger.error(f"✗ Error in null cleaning: {str(e)}")
            self.report["steps"]["clean_nulls"] = {"status": "error", "error": str(e)}
        
        #-------------------------------------------------
        # STEP 2: REMOVE DUPLICATES
        #-------------------------------------------------
        
        try:
            logger.info("\n[STEP 2] Removing duplicate rows...")
            result = self._remove_duplicates(df)
            
            # Handle inconsistent return type
            if isinstance(result, tuple):
                df, report_dupes = result
            else:
                report_dupes = result
            
            self.report["steps"]["remove_duplicates"] = report_dupes
            self.report["steps"]["remove_duplicates"]["status"] = "success"
            logger.info("✓ Duplicate removal completed")
        except Exception as e:
            logger.error(f"✗ Error in duplicate removal: {str(e)}")
            self.report["steps"]["remove_duplicates"] = {"status": "error", "error": str(e)}
        
        #-------------------------------------------------
        # STEP 3: TRIM WHITESPACE
        #-------------------------------------------------
        
        try:
            logger.info("\n[STEP 3] Trimming whitespace...")
            result = self._trim_whitespace(df)
            
            # Handle inconsistent return type
            if isinstance(result, tuple):
                df, report_trim = result
            else:
                df = result
                report_trim = {"status": "completed"}
            
            self.report["steps"]["trim_whitespace"] = report_trim
            self.report["steps"]["trim_whitespace"]["status"] = "success"
            logger.info("✓ Whitespace trimming completed")
        except Exception as e:
            logger.error(f"✗ Error in whitespace trimming: {str(e)}")
            self.report["steps"]["trim_whitespace"] = {"status": "error", "error": str(e)}
        
        #-------------------------------------------------
        # STEP 4: CLEAN CURRENCY VALUES
        #-------------------------------------------------
        
        try:
            logger.info("\n[STEP 4] Cleaning currency values...")
            result = self._clean_currency_values(df)
            
            # Handle inconsistent return type
            if isinstance(result, tuple):
                df, report_currency = result
            else:
                report_currency = result
            
            self.report["steps"]["clean_currency"] = report_currency
            self.report["steps"]["clean_currency"]["status"] = "success"
            logger.info("✓ Currency cleaning completed")
        except Exception as e:
            logger.error(f"✗ Error in currency cleaning: {str(e)}")
            self.report["steps"]["clean_currency"] = {"status": "error", "error": str(e)}
        
        #-------------------------------------------------
        # STEP 5: STANDARDIZE DATES
        #-------------------------------------------------
        
        try:
            logger.info("\n[STEP 5] Standardizing dates...")
            result = self._standardize_dates(df)
            
            # Handle inconsistent return type
            if isinstance(result, tuple):
                df, report_dates = result
            else:
                report_dates = {"status": "completed"}
            
            self.report["steps"]["standardize_dates"] = report_dates
            self.report["steps"]["standardize_dates"]["status"] = "success"
            logger.info("✓ Date standardization completed")
        except Exception as e:
            logger.error(f"✗ Error in date standardization: {str(e)}")
            self.report["steps"]["standardize_dates"] = {"status": "error", "error": str(e)}
        
        #-------------------------------------------------
        # STEP 6: STANDARDIZE STRINGS
        #-------------------------------------------------
        
        try:
            logger.info("\n[STEP 6] Standardizing strings...")
            result = self._standardize_strings(df)
            
            # Handle inconsistent return type
            if isinstance(result, tuple):
                df, report_strings = result
            else:
                report_strings = {"status": "completed"}
            
            self.report["steps"]["standardize_strings"] = report_strings
            self.report["steps"]["standardize_strings"]["status"] = "success"
            logger.info("✓ String standardization completed")
        except Exception as e:
            logger.error(f"✗ Error in string standardization: {str(e)}")
            self.report["steps"]["standardize_strings"] = {"status": "error", "error": str(e)}
        
        #-------------------------------------------------
        # FINALIZATION PHASE
        #-------------------------------------------------
        
        # Record final row/column count
        final_rows = df.shape[0]
        final_cols = df.shape[1]
        
        self.report["final_rows"] = final_rows
        self.report["final_columns"] = final_cols
        self.report["rows_removed_total"] = initial_rows - final_rows
        self.report["overall_status"] = "success"
        
        # Store cleaned dataframe
        self.df = df
        
        logger.info("\n" + "="*60)
        logger.info("DATA CLEANING COMPLETED SUCCESSFULLY")
        logger.info(f"Final dataset: {final_rows} rows, {final_cols} columns")
        logger.info(f"Total rows removed: {initial_rows - final_rows}")
        logger.info("="*60 + "\n")
        
        return df
    
    def _clean_nulls(self, df):
        """
            Handle missing values using
            business-aware retail strategies.

            Strategies:
            -----------
            sales / total_amount  -> median
            quantity              -> median
            discount              -> 0
            category              -> unknown
            payment_method        -> unknown
            customer_id           -> guest_customer
            product_name          -> unknown_product
            transaction_date      -> drop rows

            Returns:
            --------
            (
                cleaned_dataframe,
                null_handling_report
            )
        """
        logger.info(
        "Cleaning null values ."
        )
        #-------------------------------------------------
        # CREATE A SAFE COPY
        #-------------------------------------------------

        df = df.copy()

        #-------------------------------------------------
        # INTIALIZE REPORT
        #-------------------------------------------------

        report = {
            "columns_processed" : [],
            "strategies_applied" : {},
            "nulls_before" : {},
            "nulls_after" : {},
            "rows_removed" : 0
        }
        
        #-------------------------------------------------
        # initial row count
        #-------------------------------------------------

        initial_rows = df.shape[0]


        #==================================================
        # column wise null handling
        # SALES COLUMNS
        #==================================================

        if "sales" in df.columns :
            null_count = df["sales"].isnull().sum()

            report["nulls_before"]["sales"] = int(null_count)
            if null_count > 0 :
                median_value = df["sales"].median()

                df["sales"] = df["sales"].fillna(median_value)

                logger.info(
                    f"Filled {null_count} nulls in 'sales' with median value {median_value}"
                )

                report["strategies_applied"]["sales"] = (
                    "median_imputation"
                )
            report["nulls_after"]["sales"] = int(
                df["sales"].isnull().sum()
            )

            report["columns_processed"].append("sales")
        
        #==================================================
        # TOTAL AMOUNT COLUMNS
        #==================================================

        if "total_amount" in df.columns :
            null_count = df["total_amount"].isnull().sum()

            report["nulls_before"]["total_amount"] = int(null_count)

            if null_count > 0 :
                median_value = df["total_amount"].median()

                df["total_amount"] = df["total_amount"].fillna(median_value)

                logger.info(
                    f"Filled {null_count} nulls in 'total_amount' with median value {median_value}"
                )

                report["strategies_applied"]["total_amount"] = (
                    "median_imputation"
                )
                

            report["nulls_after"]["total_amount"] = int(
                df["total_amount"].isnull().sum()
            )
            report["columns_processed"].append("total_amount")
        

        #==================================================
        # QUANTITY COLUMNS
        #==================================================

        if "quantity" in df.columns:
            null_count = df["quantity"].isnull().sum()

            report["nulls_before"]["quantity"] = int(null_count)

            if null_count > 0 :
                median_value = df["quantity"].median()

                df["quantity"] = df["quantity"].fillna(median_value)

                logger.info(
                    f"Filled {null_count} nulls in 'quantity' with median value {median_value}"
                )

                report["strategies_applied"]["quantity"] = (
                    "median_imputation"
                )
        
            report["nulls_after"]["quantity"] = int(
                    df["quantity"].isnull().sum()   
            )
            report["columns_processed"].append("quantity")

        #==================================================
        # DISCOUNT COLUMNS
        #==================================================

        if "discount" in df.columns:

            null_count = df["discount"].isnull().sum()

            report["nulls_before"]["discount"] = int(
                null_count
            )

            if null_count > 0:

                df["discount"] = df["discount"].fillna(0)

                logger.info(
                    "Filled discount nulls with 0"
                )

                report["strategies_applied"][
                    "discount"
                ] = "zero_fill"

            report["nulls_after"]["discount"] = int(
                df["discount"].isnull().sum()
            )

            report["columns_processed"].append(
                "discount"
            )

        # =====================================================
        # 5. CATEGORY COLUMN
        # =====================================================

        if "category" in df.columns:

            null_count = df["category"].isnull().sum()

            report["nulls_before"]["category"] = int(
                null_count
            )

            if null_count > 0:

                df["category"] = df["category"].fillna(
                    "unknown"
                )

                logger.info(
                    "Filled category nulls with "
                    "'unknown'"
                )

                report["strategies_applied"][
                    "category"
                ] = "unknown_fill"

            report["nulls_after"]["category"] = int(
                df["category"].isnull().sum()
            )

            report["columns_processed"].append(
                "category"
            )

        # =====================================================
        # 6. PAYMENT METHOD COLUMN
        # =====================================================

        if "payment_method" in df.columns:

            null_count = df[
                "payment_method"
            ].isnull().sum()

            report["nulls_before"][
                "payment_method"
            ] = int(null_count)

            if null_count > 0:

                df["payment_method"] = df[
                    "payment_method"
                ].fillna("unknown")

                logger.info(
                    "Filled payment_method nulls "
                    "with 'unknown'"
                )

                report["strategies_applied"][
                    "payment_method"
                ] = "unknown_fill"

            report["nulls_after"][
                "payment_method"
            ] = int(
                df["payment_method"].isnull().sum()
            )

            report["columns_processed"].append(
                "payment_method"
            )

        # =====================================================
        # 7. CUSTOMER ID COLUMN
        # =====================================================

        if "customer_id" in df.columns:

            null_count = df["customer_id"].isnull().sum()

            report["nulls_before"]["customer_id"] = int(
                null_count
            )

            if null_count > 0:

                df["customer_id"] = df[
                    "customer_id"
                ].fillna("guest_customer")

                logger.info(
                    "Filled customer_id nulls "
                    "with 'guest_customer'"
                )

                report["strategies_applied"][
                    "customer_id"
                ] = "guest_customer_fill"

            report["nulls_after"]["customer_id"] = int(
                df["customer_id"].isnull().sum()
            )

            report["columns_processed"].append(
                "customer_id"
            )

        # =====================================================
        # 8. PRODUCT NAME COLUMN
        # =====================================================

        if "product_name" in df.columns:

            null_count = df[
                "product_name"
            ].isnull().sum()

            report["nulls_before"]["product_name"] = int(
                null_count
            )

            if null_count > 0:

                df["product_name"] = df[
                    "product_name"
                ].fillna("unknown_product")

                logger.info(
                    "Filled product_name nulls "
                    "with 'unknown_product'"
                )

                report["strategies_applied"][
                    "product_name"
                ] = "unknown_product_fill"

            report["nulls_after"]["product_name"] = int(
                df["product_name"].isnull().sum()
            )

            report["columns_processed"].append(
                "product_name"
            )

        # =====================================================
        # 9. TRANSACTION DATE COLUMN
        # =====================================================

        if "transaction_date" in df.columns:

            null_count = df[
                "transaction_date"
            ].isnull().sum()

            report["nulls_before"][
                "transaction_date"
            ] = int(null_count)

            if null_count > 0:

                df = df.dropna(
                    subset=["transaction_date"]
                )

                logger.info(
                    "Dropped rows with missing "
                    "transaction_date"
                )

                report["strategies_applied"][
                    "transaction_date"
                ] = "drop_rows"

            report["nulls_after"][
                "transaction_date"
            ] = int(
                df["transaction_date"].isnull().sum()
            )

            report["columns_processed"].append(
                "transaction_date"
            )

        # =====================================================
        # FINAL ROW COUNT
        # =====================================================

        final_rows = df.shape[0]

        report["rows_removed"] = int(
            initial_rows - final_rows
        )

        # =====================================================
        # SUCCESS LOG
        # =====================================================

        logger.info(
            "Missing value handling completed successfully"
        )

        return df, report
    
    #=======================================================================
    # FUNCTION TO REMOVE DUPLICATES
    #=======================================================================
    def _remove_duplicates(self, df):
        """
        TODO: Remove duplicate rows
        """
        logger.info(
            "Starting duplicate removal process."
        )

        #-------------------------------------------------
        # CREATE A SAFE COPY 
        #-------------------------------------------------

        df = df.copy()

        #-------------------------------------------------
        # STORE INITIAL ROW COUNT
        #-------------------------------------------------
        initial_rows = df.shape[0]

        #-------------------------------------------------
        #   DECTECT DUPLICATE ROWS
        # -------------------------------------------------

        duplicate_count = df.duplicated().sum()

        logger.info(
            f"Found {duplicate_count} duplicate rows in the dataframe."
        )      

        #-------------------------------------------------
        # REMOVE DUPLICATE ROWS
        #-------------------------------------------------

        df = df.drop_duplicates()

        #-------------------------------------------------
        # FINAL ROW COUNT
        #-------------------------------------------------

        final_rows = df.shape[0]
        rows_removed = initial_rows - final_rows

        #-------------------------------------------------
        # REPORT
        #-------------------------------------------------

        duplicate_report = {
            "initial_rows": int(initial_rows),
            "final_rows": int(final_rows),
            "duplicate_rows_removed": int(rows_removed)
        }
        logger.info(
            f"Duplicate removal completed. {rows_removed} duplicate rows removed."
        )
        return duplicate_report
    
    #=======================================================================
    # FUNCTION TO TRIM WHITESPACE
    #=======================================================================
    def _trim_whitespace(self, df):
        """
        TODO: Trim whitespace from strings
        """

        logger.info(
            "Starting whitespace trimming process."
        )

        #-------------------------------------------------
        # CREATE A SAFE COPY 
        #-------------------------------------------------
        df = df.copy()

        string_columns = df.select_dtypes(include=["object", "string"]).columns
        
        for column in string_columns :
            df[column] = df[column].apply(
            lambda value:
            value.strip()
            if isinstance(value, str)
            else value
            )

        return df
    #=======================================================================
    # FUNCTION TO CLEAN CURRENCY VALUES 
    #=======================================================================
    def _clean_currency_values(self, df):
       
        """
        
        Remove currency symbols and thousand separators from numeric columns.
        
        Removes: $, €, £, ¥, ₹
        Removes: , (thousand separators)
        
        Returns:
        --------
        (cleaned_dataframe, currency_report)
        """
        logger.info(
            "Starting currency value cleaning process."
        )
        
        #-------------------------------------------------
        # CREATE A SAFE COPY
        #-------------------------------------------------
        df = df.copy()
        
        #-------------------------------------------------
        # INITIALIZE REPORT
        #-------------------------------------------------
        report = {
            "columns_cleaned": [],
            "values_modified": 0,
            "status": "success"
        }
        
        #-------------------------------------------------
        # CURRENCY PATTERNS
        #-------------------------------------------------
        currency_symbols = r'[$€£¥₹]'
        thousand_separator = ','
        
        #-------------------------------------------------
        # GET CANDIDATE COLUMNS (numeric/object types)
        #-------------------------------------------------
        numeric_columns = df.select_dtypes(
            include=['float64', 'int64', 'object']
        ).columns
        
        #-------------------------------------------------
        # PROCESS EACH NUMERIC COLUMN
        #-------------------------------------------------
        for column in numeric_columns:
            try:
                # Check if column contains currency symbols or commas
                sample_values = df[column].astype(str).head()
                
                if any(
                    any(c in str(v) for c in '$€£¥₹,')
                    for v in sample_values
                ):
                    # Count values before
                    values_before = df[column].notna().sum()
                    
                    # Remove currency symbols
                    df[column] = df[column].astype(str).str.replace(
                        currency_symbols, 
                        '', 
                        regex=True
                    )
                    
                    # Remove thousand separators
                    df[column] = df[column].str.replace(
                        thousand_separator, 
                        ''
                    )
                    
                    # Count values after
                    values_after = df[column].notna().sum()
                    
                    report["columns_cleaned"].append(column)
                    report["values_modified"] += (values_before - values_after)
                    
                    logger.info(
                        f"Cleaned currency from column: {column}"
                    )
            
            except Exception as e:
                logger.warning(
                    f"Could not clean currency in {column}: {str(e)}"
                )
                report["status"] = "partial_success"
        
        logger.info(
            f"Currency cleaning completed. Columns cleaned: {len(report['columns_cleaned'])}"
        )
        
        return df, report
    

    #=======================================================================
    #  FUNCTION TO STANDARDIZE DATES
    # =======================================================================    
    def _standardize_dates(self, df):
        """
        TODO: Parse and standardize dates
           Operations:
            -----------
            1. Convert to datetime
            2. Handle invalid dates
            3. Standardize format
            4. Generate cleaning report
        """
        logger.info(
            "Standardizing date columns."
        )

        # CREATE A SAFE COPY
        df = df.copy()

        cleaning_report ={
            "columns_standardized" : [],
            "invalid_dates_handled" : {},
            "invalid_dates_converted_to_na" : 0
        }
       
        possible_date_columns = [
            "transaction_date",
            "order_date",
            "sale_date",
            "date",
            "purchase_date",
            "created_at",
            "updated_at"
        ]
        for column in possible_date_columns:
            if column not in df.columns :
                continue

            logger.info(
                f"processing date column : {column}"
            )
            null_before = df[column].isnull().sum()

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )

            null_after = df[column].isnull().sum()

            invalid_dates = null_after - null_before
            cleaning_report["invalid_dates_handled"][column] = int(invalid_dates)
            cleaning_report["invalid_dates_converted_to_na"] += int(invalid_dates)
            cleaning_report["columns_standardized"].append(column)

            logger.info(
                f"Standardized {column}. Invalid dates handled: {invalid_dates}"
            )

        logger.info(
            "Date standardization completed."
        )
        
        return df, cleaning_report


    #=======================================================================
    # FUNCTION TO STANDARDIZE STRINGS
    #=======================================================================
    def _standardize_strings(self, df):
        """
        TODO: Lowercase and normalize strings
          Operations:
           -----------
           1. Trim whitespaces
           2. Convert to lowercase
           3. Replace spaces with underscore
           4. Remove special characters
           5. Normalize multiple spaces

        """
        logger.info(
            "starting string standardization process."
        )

        df = df.copy()

        cleaning_report = {
            "column_standardized" : [],
             "total_string_columns" : 0
        }

        #-------------------------------------------------
        # DETECT STRING COLUMN
        #-------------------------------------------------

        string_columns = df.select_dtypes(
            include=["object", "string"]
            ).columns
        
        cleaning_report["total_string_columns"] = len(string_columns)

        #-------------------------------------------------
        # PROCESS EACH STRING
        #-------------------------------------------------
        for column in string_columns :
            logger.info(
                f"Standardizing column: {column}"
            )

            df[column]  = df[column].apply(
                lambda value: self.standardize_string(value) if isinstance(value, str) else value
            )
            cleaning_report["column_standardized"].append(column)
        logger.info("String standardization completed.")
        return df, cleaning_report
    #======================================================
    # HELPER FUNCTION TO STANDARDIZE A SINGLE STRING
    #======================================================
    def standardize_string(self, value):
        value = value.strip()
        value = value.lower()
        value = re.sub(
            r"\s+", " ", value
        )
        value = value.replace(" ", "_")
        value = re.sub(
            r"[^a-z0-9_]", "", value
        )

        return value
    #======================================================
    # GENERATE CLEANING REPORT
    #======================================================
    def _generate_cleaning_report(self):
        """
        TODO: Build report with operations log
        """
        logger.info(
            "Generating cleaning report."
        )

        #-------------------------------------------------
        # verify data exists
        #-------------------------------------------------

        if not hasattr(self, 'report') or not self.report:
            logger.warning(
                "No cleaning report data available to generate report."
            )
            return 
        
        #-------------------------------------------------
        # ADD METADATA
        #-------------------------------------------------
        from datetime import datetime
        self.report["metadata"] = {
            "generated_at" : datetime.now().isoformat() ,
            "schema_version" : self.schema.get("version", "unknown"),
            "domain": self.schema.get("dataset", {}).get("domain", "unknown"),
            "timezone": self.schema.get("metadata", {}).get("timezone", "unknown")
        }
        #-------------------------------------------------
        # LOG REPORT SUMMARY
        #-------------------------------------------------

        initial_rows = self.report.get("initial_rows", 0)
        final_rows = self.report.get("final_rows", 0)
        rows_removed = self.report.get("rows_removed_total", 0)

        percent_preserved = (final_rows / initial_rows * 100) if initial_rows > 0 else 0

        self.report["summary"] = {
            "initial_rows": int(initial_rows),
            "final_rows": int(final_rows),
            "rows_removed": int(rows_removed),
            "percent_preserved": round(percent_preserved, 2),
            "inital_columns": int(self.report.get("initial_columns", 0)),
            "final_columns": int(self.report.get("final_columns", 0)),
            "overall_status": self.report.get("overall_status", "unknown")
        }    

        #-------------------------------------------------
        # EXTRACT STEP SUMMARIES
        #-------------------------------------------------

        steps_summary = {}
        steps = self.report.get("steps", {})
        
        for step_name, step_data in steps.items():
            steps_summary[step_name] = {
                "status": step_data.get("status", "unknown"),
                "details": {k: v for k, v in step_data.items() if k != "status"}
            }

        self.report["steps_summary"] = steps_summary
        
        logger.info(
            f"Report generated successfully with {len(steps_summary)} steps completed"
        )
    #==========================================================
    # getting cleaning report
    #==========================================================
    def get_cleaning_report(self):
        """
        Return the comprehensive cleaning report.
        
        Returns:
        --------
        dict - Complete report with all cleaning operations metadata
        """
        if not hasattr(self, 'report') or not self.report:
            logger.warning("No cleaning report available. Run clean_dataframe() first.")
            return {}
        return self.report
    
    #==========================================================
    # getting cleaned dataframe
    #==========================================================
    def get_dataframe(self):
        """
        Return the cleaned dataframe.
        
        Returns:
        --------
        DataFrame - Cleaned and processed dataframe
        """
        if not hasattr(self, 'df') or self.df is None:
            logger.warning("No cleaned dataframe available. Run clean_dataframe() first.")
            return None
        return self.df

