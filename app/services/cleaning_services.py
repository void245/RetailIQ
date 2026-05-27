import pandas as pd
import logging
from app.services.config_loader import ConfigManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class CleaningService:
    def __init__(self):
        self.config = ConfigManager()
        self.schema = self.config.get_canonical_schema()
        self.report = {}
        self.cleaning_log = []
        logger.info("CleaningService initialized")

    def clean_dataframe(self, df):
        """
            Clean the given DataFrame based on the canonical schema and validation rules.
            1. Clean nulls
            2. Remove duplicates
            3. Trim whitespace
            4. Clean currency
            5. Standardize dates
            6. Standardize strings
            7. Generate report
        """
        logger.info("Starting dataframe cleaning pipeline...")
        
        df_clean = df.copy()
        initial_rows = len(df_clean)
        
        logger.info("Step 1: Cleaning null values...")
        df_clean = self._clean_nulls(df_clean)
        
        logger.info("Step 2: Removing duplicates...")
        df_clean = self._remove_duplicates(df_clean)
        
        logger.info("Step 3: Trimming whitespace...")
        df_clean = self._trim_whitespace(df_clean)
        
        logger.info("Step 4: Cleaning currency values...")
        df_clean = self._clean_currency_values(df_clean)
        
        logger.info("Step 5: Standardizing dates...")
        df_clean = self._standardize_dates(df_clean)
        
        logger.info("Step 6: Standardizing strings...")
        df_clean = self._standardize_strings(df_clean)
        
        logger.info("Step 7: Generating cleaning report...")
        self._generate_cleaning_report(initial_rows, len(df_clean), df_clean.shape[1])
        
        logger.info("✓ Cleaning pipeline completed")
        return df_clean
    
    def _clean_nulls(self, df):
        """Replace empty strings with NaN and remove rows with required field NULLs."""
        logger.info("Cleaning null values...")
        
        rows_before = len(df)
        df = df.replace('', pd.NA)
        
        canonical_fields = self.schema.get("canonical_fields", {})
        
        for column, field_info in canonical_fields.items():
            if column not in df.columns:
                continue
            
            is_nullable = field_info.get("nullable", False)
            
            if not is_nullable:
                rows_with_nan = df[df[column].isnull()].shape[0]
                df = df[df[column].notnull()]
                
                if rows_with_nan > 0:
                    logger.info(f"  Removed {rows_with_nan} rows with null '{column}'")
        
        rows_after = len(df)
        self.cleaning_log.append({
            "operation": "clean_nulls",
            "rows_before": rows_before,
            "rows_after": rows_after,
            "rows_removed": rows_before - rows_after
        })
        
        return df
    
    def _remove_duplicates(self, df):
        """Remove exact duplicate rows based on schema config."""
        logger.info("Removing duplicate rows...")
        
        rows_before = len(df)
        dedup_config = self.schema.get("deduplication", {})
        
        if not dedup_config.get("enabled", False):
            logger.info("  Deduplication disabled")
            return df
        
        subset = dedup_config.get("subset", list(df.columns))
        subset = [col for col in subset if col in df.columns]
        
        df = df.drop_duplicates(subset=subset, keep='first')
        
        rows_after = len(df)
        logger.info(f"  Removed {rows_before - rows_after} duplicate rows")
        
        self.cleaning_log.append({
            "operation": "remove_duplicates",
            "rows_before": rows_before,
            "rows_after": rows_after,
            "rows_removed": rows_before - rows_after,
            "subset_columns": subset
        })
        
        return df
    
    def _trim_whitespace(self, df):
        """Trim leading/trailing whitespace from string columns."""
        logger.info("Trimming whitespace...")
        
        canonical_fields = self.schema.get("canonical_fields", {})
        trimmed_columns = []
        
        for column in df.columns:
            if column not in canonical_fields:
                continue
            
            field_info = canonical_fields[column]
            cleaning_rules = field_info.get("cleaning", {})
            
            if cleaning_rules.get("trim_whitespace", False):
                if df[column].dtype == 'object':
                    df[column] = df[column].str.strip()
                    trimmed_columns.append(column)
                    logger.info(f"  Trimmed column: {column}")
        
        self.cleaning_log.append({
            "operation": "trim_whitespace",
            "columns_affected": trimmed_columns
        })
        
        return df
    
    def _clean_currency_values(self, df):
        """Remove currency symbols and thousand separators."""
        logger.info("Cleaning currency values...")
        
        canonical_fields = self.schema.get("canonical_fields", {})
        cleaned_columns = []
        
        for column in df.columns:
            if column not in canonical_fields:
                continue
            
            field_info = canonical_fields[column]
            cleaning_rules = field_info.get("cleaning", {})
            
            if cleaning_rules.get("remove_currency_symbols", False) or \
               cleaning_rules.get("remove_thousands_separator", False):
                
                if df[column].dtype == 'object':
                    df[column] = df[column].astype(str).str.replace(r'[$€£¥₹]', '', regex=True)
                    df[column] = df[column].str.replace(',', '')
                    cleaned_columns.append(column)
                    logger.info(f"  Cleaned currency in column: {column}")
        
        self.cleaning_log.append({
            "operation": "clean_currency",
            "columns_affected": cleaned_columns
        })
        
        return df
    
    def _standardize_dates(self, df):
        """Parse multiple date formats and standardize to datetime."""
        logger.info("Standardizing dates...")
        
        canonical_fields = self.schema.get("canonical_fields", {})
        standardized_columns = []
        
        for column in df.columns:
            if column not in canonical_fields:
                continue
            
            field_info = canonical_fields[column]
            
            if field_info.get("datatype") != "datetime":
                continue
            
            try:
                df[column] = pd.to_datetime(
                    df[column],
                    errors='coerce',
                    infer_datetime_format=True
                )
                standardized_columns.append(column)
                logger.info(f"  Standardized dates in column: {column}")
            except Exception as e:
                logger.warning(f"  Error standardizing dates in {column}: {str(e)}")
        
        self.cleaning_log.append({
            "operation": "standardize_dates",
            "columns_affected": standardized_columns
        })
        
        return df
    
    def _standardize_strings(self, df):
        """Lowercase, normalize spacing in string columns."""
        logger.info("Standardizing strings...")
        
        canonical_fields = self.schema.get("canonical_fields", {})
        standardized_columns = []
        
        global_cleaning = self.schema.get("cleaning_rules", {})
        lowercase_headers = global_cleaning.get("lowercase_headers", False)
        
        for column in df.columns:
            if column not in canonical_fields:
                continue
            
            field_info = canonical_fields[column]
            
            if field_info.get("datatype") not in ["string", "object"]:
                continue
            
            if df[column].dtype == 'object':
                if lowercase_headers:
                    df[column] = df[column].astype(str).str.lower()
                
                df[column] = df[column].astype(str).str.replace(r'\s+', ' ', regex=True)
                
                standardized_columns.append(column)
                logger.info(f"  Standardized strings in column: {column}")
        
        self.cleaning_log.append({
            "operation": "standardize_strings",
            "columns_affected": standardized_columns
        })
        
        return df
    
    def _generate_cleaning_report(self, rows_input, rows_output, total_columns):
        """Generate comprehensive cleaning report."""
        
        rows_removed = rows_input - rows_output
        
        self.report = {
            "status": "SUCCESS" if rows_removed < rows_input * 0.5 else "PARTIAL",
            "total_rows_input": rows_input,
            "total_rows_output": rows_output,
            "total_columns": total_columns,
            "rows_removed": rows_removed,
            "retention_rate": round((rows_output / rows_input * 100), 2) if rows_input > 0 else 0,
            "operations": self.cleaning_log,
            "summary": {
                "total_operations": len(self.cleaning_log),
                "total_rows_modified": sum([op.get("rows_removed", 0) for op in self.cleaning_log]),
                "total_columns_affected": sum([len(op.get("columns_affected", [])) for op in self.cleaning_log])
            }
        }
        
        logger.info(f"✓ Cleaning Report Generated:")
        logger.info(f"  Input rows: {rows_input}, Output rows: {rows_output}")
        logger.info(f"  Retention rate: {self.report['retention_rate']}%")
    
    def get_cleaning_report(self):
        """Get the cleaning report."""
        return self.report
    
    def get_dataframe(self):
        """Return the report metadata."""
        return {"status": "success", "data": self.report}
        