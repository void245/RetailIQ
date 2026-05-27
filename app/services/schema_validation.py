import pandas as pd 
import numpy as np

# to reuse canonical mapping logic from canonical service
from app.services.canonical_service import process_canonical_mapping 

from app.services.config_loader import ConfigManager 

#---------------------------------------------------
# CREATING A VALIDATION CLASS
#---------------------------------------------------

class SchemaValidationServices :

    def __init__(self):
        self.config = ConfigManager()
        self.schema = self.config.get_canonical_schema()
        self.report ={}
    
    def validate_schema(self , df : pd.DataFrame , schema) :
        """
            Validate the dataframe against the canonical schema and generate a validation report.
            1. normalize columns
            2. map columns
            3. validate required cols
            4. validate datatypes
            5. validate rules
            6. generate report
        """
        # calling process_canonical_mapping to get column mapping and unmapped columns

        processed_df , mapping_report = process_canonical_mapping(df , self.schema)

        # STORE MAPPING REPORT
        self.mapping_report = mapping_report

        # NOW VALIDATE THE PROCESSED DF AGAINST THE SCHEMA
        self._validate_required_columns(processed_df )
        self._validate_datatypes(processed_df)
        self._validate_business_rules(processed_df)
        self._detect_anomalies(processed_df)
        self._generate_report()

    def _validate_required_columns(self , df ) :
        """
            Validate that all required columns are present in the dataframe.
        """
        required_columns = self.schema.get('required_columns' , [])

        # getting actual columns from df 
        actual_columns = df.columns.tolist()

        # missing columns 
        missing_columns = [col for col in required_columns if col not in actual_columns]

        # getting all canonical fields name from schema
        canonical_fields = list(self.schema.get('canonical_fields' , {}).keys())

        # extra columns
        extra_columns = [col for col in actual_columns if col not in canonical_fields]

        # status 

        status = "FAIL" if missing_columns else "PASS"
        error_count = len(missing_columns)

        # result dictionary

        result = {
            "status" : status,
            "required_columns" : required_columns, 
            "present_columns" : actual_columns ,
            "missing_columns" : missing_columns ,
            "extra_columns" : extra_columns ,
            "total_columns" : len(actual_columns),
            "details" : f"{error_count} required columns missing" if error_count else "All required columns are present"
        }

        self.structure_validation = result

        return result
    
    def _validate_datatypes(self , df) :
        """
            Validate that the datatypes of the columns match the schema.
        """

        # getting datatype schema
        datatype_schema = self.schema.get('datatype_schema', {})        

        # initalize 
        dtype_error = []
        coercion = []
        validation_columns =[]
        total_errors = 0

        # looping through each column

        for column in df.columns :
            if column not in datatype_schema :
                continue

            expected_dtype = datatype_schema[column]
            actual_dtype = str(df[column].dtype)

            # check if actual dtype matches expected
            if actual_dtype == expected_dtype :
                validation_columns.append({
                    "column" : column,
                    "expected_dtype" : expected_dtype,
                    "actual_dtype" : actual_dtype,
                    "status" : "matched"
                })
                continue

            coercion_result = self._try_coerce_column(df , column, expected_dtype)

            if coercion_result["success"] :
                coercion.append(coercion_result)
                df[column] = coercion_result["coerced_values"]
            else :
                dtype_error.append(coercion_result)
                total_errors += 1
        
        status = "PASS" if total_errors == 0 else ("WARNING" if coercion else "FAIL")
        
        result = {
            "status": status,
            "total_columns": len(datatype_schema),
            "validated_columns": len(validation_columns),
            "dtype_errors": dtype_error,
            "coercions": coercion,
            "error_count": total_errors,
            "coercion_count": len(coercion)
        }
        
        self.datatype_validation = result
        return result

    
    def _try_coerce_column(self , df , column , expected_dtype) :
        """
            Try to coerce the column to the expected datatype and check if it succeeds.
        """
        try :
            actual_dtype = str(df[column].dtype)
            original_nulls = df[column].isnull().sum()

            # numeric coercion 

            if expected_dtype in ['int64' , 'float64', 'float32', 'int32'] :
                coerced = pd.to_numeric(df[column], errors = 'coerce')

            # datetime coercion
            elif expected_dtype == "datetime" :
                coerced = pd.to_datetime(df[column] , errors = 'coerce' , infer_datetime_format = True)
            
            # string 
            elif expected_dtype in ['object', 'string'] :
                coerced = df[column].astype(str)
            
            else :
                coerced = df[column].astype(expected_dtype)

            new_nulls = coerced.isnull().sum()
            introduced_nulls = new_nulls - original_nulls
            total_values = len(coerced)
            successful_coercions = total_values - new_nulls
            success_rate = (successful_coercions / total_values *100) if total_values > 0 else 0 

            return {
                "column" : column ,
                "expected_dtype" : expected_dtype,
                "from_type" : actual_dtype,
                "to_type" : expected_dtype,
                "success" : success_rate >= 95 ,
                "success_rate" : round(success_rate ,2),
                "coerced_values" : coerced,
                "introduced_nulls" : introduced_nulls,
                "sample_values" : df[column].head(3).tolist()
            }
        except Exception as e :
            return {
                "column" : column ,
                "expected_dtype" : expected_dtype,
                "from_type" : actual_dtype,
                "to_type" : expected_dtype,
                "success" : False ,
                "success_rate" : 0.0,
                "coerced_values" : 0,
                "introduced_nulls" : 0,
                "error" : str(e)
            }

    def _validate_business_rules(self , df):
        """
           
            Validate dataframe columns against configured business rules.

            This method applies schema-defined validation constraints
            such as:
            - min/max thresholds
            - null checks
            - integer enforcement
            - regex validation
            - date validation

            Returns:
                dict: Validation summary including violations,
                row statistics, and validation status.
        """

                
        # getting business rules from schema

        validation_rules = self.schema.get("validation_rules", {})
        
        # state validation for keeping track of overall status

        violations = []
        all_violation_rows = set()

        # loop through each column and apply rules 

        for column , rules in validation_rules.items() :
            if column not in df.columns :
                continue 

            # apply min rule 
            if "min" in rules :
                min_value = rules["min"]
                violating_rows = df[df[column] < min_value].index.tolist()
                if violating_rows :
                    violations.append({
                        "column" : column,
                        "rule" : "min" ,
                        "constraint" : f"Value should be >= {min_value}",
                        "violation_count" : len(violating_rows),
                        "violation_rows" : violating_rows,
                        "sample_violations" : df.loc[violating_rows , column].head(3).tolist() 
                    })
                    all_violation_rows.update(violating_rows)
            
            # apply max rule
            if "max" in rules :
                max_value = rules["max"]
                violating_rows = df[df[column] > max_value].index.tolist()

                if violating_rows :
                    violations.append({
                        "column" : column,
                        "rule" : "max" ,
                        "constraint" : f"Value should be <= {max_value}",
                        "violation_count" : len(violating_rows),
                        "violation_rows" : violating_rows,
                        "sample_violations" : df.loc[violating_rows , column].head(3).tolist() 
                    })
                    all_violation_rows.update(violating_rows)
            
            # apply not null rule 
            if rules.get("not_null" , False) :
                violating_rows = df[df[column].isnull()].index.tolist()

                if violating_rows :
                    violations.append({
                        "column" : column,
                        "rule" : "not_null" ,
                        "constraint" : f"Value should not be null",
                        "violation_count" : len(violating_rows),
                        "violation_rows" : violating_rows,
                        "sample_violations" : df.loc[violating_rows , column].head(3).tolist() 
                    })
                    all_violation_rows.update(violating_rows)
            
            # apply integer rule
            if rules.get("integer",False):

              try:
                int_mask = df[column].apply(lambda x: x == int(x) if pd.notna(x) else True)
                violating_rows = df[~int_mask].index.tolist()
            

                if violating_rows :
                    violations.append({
                        "column" : column,
                        "rule" : "integer" ,
                        "constraint" : f"Value should be an integer",
                        "violation_count" : len(violating_rows),
                        "violation_rows" : violating_rows,
                        "sample_violations" : df.loc[violating_rows , column].head(3).tolist() 
                    })
                    all_violation_rows.update(violating_rows)
              except : 
                   pass
            
            # apply regex rule

            if "regex_pattern" in rules :
                pattern = rules["regex_pattern"]

                try :
                    regex_match = df[column].astype(str).str.match(pattern)
                    violating_rows = df[~regex_match].index.tolist()

                    if violating_rows :
                        violations.append({
                            "column" : column,
                            "rule" : "regex_pattern" ,
                            "constraint" : f"Value should match regex: {pattern}",
                            "violation_count" : len(violating_rows),
                            "violation_rows" : violating_rows,
                            "sample_violations" : df.loc[violating_rows , column].head(3).tolist() 
                        })
                        all_violation_rows.update(violating_rows)
                except :
                    pass
            
            # apply "past_date" rule
            if rules.get("past_date", False):
                try :
                    today = pd.Timestamp.today()
                    violating_rows = df[pd.to_datetime(df[column], errors='coerce') > today].index.tolist()

                    if violating_rows :
                        violations.append({
                            "column" : column,
                            "rule" : "past_date" ,
                            "constraint" : f"Date should be in the past",
                            "violation_count" : len(violating_rows),
                            "violation_rows" : violating_rows,
                            "sample_violations" : df.loc[violating_rows , column].head(3).tolist() 
                        })
                        all_violation_rows.update(violating_rows)
                except :
                    pass
            
            # statistics

            total_rows = len(df)
            invalid_rows = len(all_violation_rows)
            valid_rows = total_rows - invalid_rows

            # validation status

            status = "FAIL" if violations else "PASS"
            
            result = {
                "status" : status,
                "total_rows" : total_rows,
                "valid_rows" : valid_rows,
                "invalid_rows" : invalid_rows,
                "violations" : violations,
                "total_violation_count" : len(all_violation_rows),
                "violation_rows" : list(all_violation_rows)
            }

            self.business_rules_validation = result 
            return result

    def _detect_anomalies(self, df):
        """
            Detect anomalies in the dataframe using simple statistical methods.
            This can be extended with more sophisticated anomaly detection techniques.
        """

        # get anomaly detection config
        anomaly_config = self.schema.get("anomaly_detection", {})

        if not anomaly_config.get("enabled", False) :
            result = {
                "status" : "PASS",
                "anomaly_detection_enabled" : False,
                "anomalies" : [],
                "anomalies_count" : 0,
                "anomaly_rows" : []
            }
            self.anomaly_detection = result
            return result
        
        anomalies = []
        all_anomaly_rows = set()

        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if "zscore" in anomaly_config.get("methods", []):
            
            zscore_threshold = anomaly_config.get("zscore_threshold", 3)
        
            for column in numeric_columns:
             mean = df[column].mean()
             std = df[column].std()
            
             if std == 0:  # Skip zero variance columns
                continue
            
             z_scores = np.abs((df[column] - mean) / std)
             anomalous_indices = df[z_scores > zscore_threshold].index.tolist()
            
             if anomalous_indices:
                anomalies.append({
                    "column": column,
                    "method": "zscore",
                    "threshold": zscore_threshold,
                    "anomaly_count": len(anomalous_indices),
                    "anomaly_rows": anomalous_indices[:100],
                    "severity": "warning"
                })
                all_anomaly_rows.update(anomalous_indices)
    
        # apply IQR METHOD 

        if "iqr" in anomaly_config.get("methods", []):
            iqr_multiplier = 1.5

            for column in numeric_columns : 
                Q1 = df[column].quantile(0.25)
                Q3 = df[column].quantile(0.75)
                IQR = Q3 - Q1

                if IQR == 0 :
                    continue

                lower_bound = Q1 - iqr_multiplier * IQR
                upper_bound = Q3 + iqr_multiplier * IQR

                anomalous_indices = df[(df[column] < lower_bound) | (df[column] > upper_bound)].index.tolist()

                if anomalous_indices:
                    anomalies.append({
                        "column": column,
                        "method": "iqr",
                        "threshold": iqr_multiplier,
                        "anomaly_count": len(anomalous_indices),
                        "anomaly_rows": anomalous_indices[:100],
                        "severity": "warning"
                    })
                    all_anomaly_rows.update(anomalous_indices)

        business_rules = anomaly_config.get("business_rules", {})

        if business_rules.get("negative_values", False) and "sales" in df.columns :
            anomalous_indices = df[df["sales"] < 0].index.tolist()
            if anomalous_indices :
                anomalies.append({
                    "column" : "sales",
                    "method" : "negative_values",
                    "threshold" : "Value should be non-negative",
                    "anomaly_count" : len(anomalous_indices),
                    "anomaly_rows" : anomalous_indices[:100],
                    "severity" : "critical"
                })
                all_anomaly_rows.update(anomalous_indices)

        if business_rules.get("future_dates", False) and "date" in df.columns :
            today = pd.Timestamp.today()
            anomalous_indices = df[pd.to_datetime(df["date"], errors='coerce') > today].index.tolist()

            if anomalous_indices :
                anomalies.append({
                    "column" : "date",
                    "method" : "future_dates",
                    "threshold" : "Date should not be in the future",
                    "anomaly_count" : len(anomalous_indices),
                    "anomaly_rows" : anomalous_indices[:100],
                    "severity" : "critical"
                })
                all_anomaly_rows.update(anomalous_indices)

        if business_rules.get("zero_quantity_check", False) and "quantity" in df.columns :
            anomalous_indices = df[df["quantity"] == 0].index.tolist()

            if anomalous_indices :
                anomalies.append({
                    "column" : "quantity",
                    "method" : "zero_quantity_check",
                    "threshold" : "Quantity should not be zero",
                    "anomaly_count" : len(anomalous_indices),
                    "anomaly_rows" : anomalous_indices[:100],
                    "severity" : "warning"
                })
                all_anomaly_rows.update(anomalous_indices)

        status = "PASS" if len(all_anomaly_rows) == 0 else "WARNING"

        result = {
            "status" : status,
            "total_rows" : len(df),
            "anomaly_rows_count" : len(all_anomaly_rows),
            "anomalies" : anomalies,
            "total_anomalies" : len(anomalies),
            "anomaly_rows" : list(all_anomaly_rows)
        }

        self.anomaly_detection = result 
        return result
    
    def _generate_report(self):
        """Generate comprehensive validation report combining all results."""
        
        # Step 1: Get all validation results
        mapping_report = getattr(self, 'mapping_report', {})
        structure_validation = getattr(self, 'structure_validation', {})
        datatype_validation = getattr(self, 'datatype_validation', {})
        business_rules_validation = getattr(self, 'business_rules_validation', {})
        anomaly_detection = getattr(self, 'anomaly_detection', {})
        
        # Step 2: Extract metadata
        total_rows = business_rules_validation.get("total_rows", 0)
        valid_rows = business_rules_validation.get("valid_rows", total_rows)
        total_columns = len(mapping_report.get("mapped_columns", {}))
        unmapped_columns = mapping_report.get("unmapped_columns", [])
        
        # Step 3: Determine overall status
        statuses = [
            structure_validation.get("status", "PASS"),
            datatype_validation.get("status", "PASS"),
            business_rules_validation.get("status", "PASS"),
            anomaly_detection.get("status", "PASS")
        ]
        overall_status = "FAIL" if "FAIL" in statuses else ("WARNING" if "WARNING" in statuses else "PASS")
        
        # Step 4: Calculate summary metrics
        structure_errors = structure_validation.get("error_count", 0)
        dtype_errors = datatype_validation.get("error_count", 0)
        rule_violations = business_rules_validation.get("total_violations", 0)
        anomaly_count = len(anomaly_detection.get("anomaly_rows", []))
        
        total_critical_errors = structure_errors + dtype_errors + rule_violations
        
        # Step 5: Generate recommendations
        recommendations = []
    
        if structure_validation.get("missing_columns"):
            missing = structure_validation["missing_columns"]
            recommendations.append(f"❌ CRITICAL: Missing required columns: {missing}")
        
        if unmapped_columns:
            recommendations.append(f"⚠️ WARNING: {len(unmapped_columns)} unmapped columns: {unmapped_columns}")
        
        if datatype_validation.get("dtype_errors"):
            error_columns = [e["column"] for e in datatype_validation["dtype_errors"]]
            recommendations.append(f"❌ CRITICAL: Fix datatype errors in: {error_columns}")
        
        if business_rules_validation.get("violations"):
            for v in business_rules_validation["violations"]:
                count = v.get("violation_count", 0)
                col = v.get("column", "")
                rule = v.get("rule", "")
                recommendations.append(f"❌ CRITICAL: {count} {rule} violations in '{col}'")
        
        if anomaly_count > 0:
            recommendations.append(f"⚠️ WARNING: Detected {anomaly_count} anomalous rows")
        
        if overall_status == "PASS":
            recommendations.append("✓ Dataset ready for RetailIQ AI")
        elif overall_status == "WARNING":
            recommendations.append("⚠️ Proceed with caution - review warnings")
        else:
            recommendations.append("❌ Fix errors before processing")
        
        # Step 6: Determine is_usable
        is_usable = overall_status in ["PASS", "WARNING"]
    
        # Step 7: Calculate usability score
        if total_rows == 0:
            usability_score = {"score": 0, "rating": "UNUSABLE"}
        else:
            valid_ratio = valid_rows / total_rows * 50
            schema_score = max(0, 30 - (total_critical_errors * 2))
            warning_score = max(0, 20 - (anomaly_count * 0.5))
            total_score = round(valid_ratio + schema_score + warning_score, 1)
            
            if total_score >= 90:
                rating = "EXCELLENT"
            elif total_score >= 75:
                rating = "GOOD"
            elif total_score >= 60:
                rating = "ACCEPTABLE"
            elif total_score >= 40:
                rating = "POOR"
            else:
                rating = "UNUSABLE"
            
            usability_score = {
                "score": total_score,
                "rating": rating,
                "breakdown": {
                    "data_quality": round(valid_ratio, 1),
                    "schema_compliance": round(schema_score, 1),
                    "warning_factor": round(warning_score, 1)
                }
            }
        
        # Step 8: Build final report
        self.report = {
            "metadata": {
                "total_rows": total_rows,
                "valid_rows": valid_rows,
                "invalid_rows": total_rows - valid_rows,
                "total_columns": total_columns,
                "timestamp": pd.Timestamp.now().isoformat()
            },
            
            "overall_status": overall_status,
            "is_usable": is_usable,
            
            "validation_results": {
                "structure": structure_validation,
                "datatypes": datatype_validation,
                "business_rules": business_rules_validation,
                "anomalies": anomaly_detection,
                "mapping": mapping_report
            },
            
            "summary": {
                "total_issues": total_critical_errors + anomaly_count,
                "critical_errors": total_critical_errors,
                "structure_errors": structure_errors,
                "datatype_errors": dtype_errors,
                "rule_violations": rule_violations,
                "warnings": anomaly_count
            },
            
            "recommendations": recommendations,
            "usability_score": usability_score
        }

    def get_is_usable(self):
        """Get final usability decision."""
        return self.report.get("is_usable", False)

    def get_full_report(self):
        """Get complete validation report."""
        return self.report