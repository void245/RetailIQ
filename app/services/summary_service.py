import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter
from datetime import datetime
from scipy import stats

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ========================================================
# SUMMARY SERVICE - COMPREHENSIVE DATA ANALYSIS
# ========================================================

class SummaryService:
    """
    Generates comprehensive data summaries and analytics from cleaned datasets.
    This service is the final step in the data pipeline after cleaning.
    
    Pipeline Flow:
    dataset_reader.py → canonical_service.py → schema_validator.py 
    → cleaning_service.py → summary_service.py
    """

    def __init__(self):
        """Initialize the SummaryService with empty report structures."""
        self.df = None
        self.report = {}
        self.column_summaries = {}
        self.data_quality_report = {}
        self.statistical_report = {}
        self.distribution_report = {}
        logger.info("SummaryService initialized")

    # ========================================================
    # MAIN ENTRY POINT - GENERATE COMPREHENSIVE SUMMARY
    # ========================================================

    def generate_complete_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a complete data summary from the cleaned DataFrame.
        
        Args:
            df (pd.DataFrame): Cleaned and validated dataframe
            
        Returns:
            Dict: Comprehensive summary report containing all analyses
        """
        logger.info("Starting comprehensive data summary generation...")
        
        self.df = df.copy()
        
        # Step 1: Basic Dataset Overview
        self._generate_overview()
        
        # Step 2: Data Quality Analysis
        self._analyze_data_quality()
        
        # Step 3: Statistical Analysis
        self._generate_statistical_analysis()
        
        # Step 4: Distribution Analysis
        self._analyze_distributions()
        
        # Step 5: Column-by-Column Summary
        self._generate_column_summaries()
        
        # Step 6: Data Insights and Patterns
        self._extract_insights()
        
        # Step 7: Calculate KPIs
        self._calculate_kpis()
        
        # Step 8: Generate Business Summary
        self._generate_business_summary()
        
        # Step 9: Detect Trends
        self._detect_trends()
        
        # Step 10: Prepare Dashboard Metrics
        self._prepare_dashboard_metrics()
        
        # Step 11: Anomaly Detection
        self._detect_anomalies()
        
        # Step 12: Correlation Analysis
        self._analyze_correlations()
        
        # Step 13: Compile Final Report
        self._compile_final_report()
        
        logger.info("✓ Comprehensive summary generation completed")
        return self.report

    # ========================================================
    # 1. DATASET OVERVIEW
    # ========================================================

    def _generate_overview(self) -> None:
        """Generate basic dataset overview."""
        logger.info("Generating dataset overview...")
        
        self.report['overview'] = {
            'total_rows': int(self.df.shape[0]),
            'total_columns': int(self.df.shape[1]),
            'column_names': self.df.columns.tolist(),
            'memory_usage_mb': round(self.df.memory_usage(deep=True).sum() / 1024**2, 2),
            'generated_at': datetime.now().isoformat(),
        }

    # ========================================================
    # 2. DATA QUALITY ANALYSIS
    # ========================================================

    def _analyze_data_quality(self) -> None:
        """Analyze overall data quality metrics."""
        logger.info("Analyzing data quality...")
        
        total_cells = self.df.shape[0] * self.df.shape[1]
        
        self.data_quality_report = {
            'total_cells': int(total_cells),
            'null_cells': int(self.df.isnull().sum().sum()),
            'non_null_cells': int(total_cells - self.df.isnull().sum().sum()),
            'completeness_percentage': round(
                ((total_cells - self.df.isnull().sum().sum()) / total_cells * 100), 2
            ),
            'duplicate_rows': int(self.df.duplicated().sum()),
            'unique_rows': int(len(self.df.drop_duplicates())),
            'column_null_counts': self.df.isnull().sum().to_dict(),
            'column_null_percentages': (
                (self.df.isnull().sum() / len(self.df) * 100).round(2).to_dict()
            ),
        }
        
        self.report['data_quality'] = self.data_quality_report

    # ========================================================
    # 3. STATISTICAL ANALYSIS
    # ========================================================

    def _generate_statistical_analysis(self) -> None:
        """Generate statistical summaries for numeric columns."""
        logger.info("Generating statistical analysis...")
        
        numeric_df = self.df.select_dtypes(include=[np.number])
        
        self.statistical_report = {
            'numeric_columns': numeric_df.columns.tolist(),
            'statistics': {}
        }
        
        for column in numeric_df.columns:
            col_data = numeric_df[column].dropna()
            
            if len(col_data) > 0:
                self.statistical_report['statistics'][column] = {
                    'count': int(len(col_data)),
                    'mean': round(float(col_data.mean()), 4),
                    'median': round(float(col_data.median()), 4),
                    'std_dev': round(float(col_data.std()), 4),
                    'min': round(float(col_data.min()), 4),
                    'max': round(float(col_data.max()), 4),
                    'q25': round(float(col_data.quantile(0.25)), 4),
                    'q75': round(float(col_data.quantile(0.75)), 4),
                    'iqr': round(
                        float(col_data.quantile(0.75) - col_data.quantile(0.25)), 4
                    ),
                    'variance': round(float(col_data.var()), 4),
                    'skewness': round(float(col_data.skew()), 4),
                    'kurtosis': round(float(col_data.kurtosis()), 4),
                }
        
        self.report['statistics'] = self.statistical_report

    # ========================================================
    # 4. DISTRIBUTION ANALYSIS
    # ========================================================

    def _analyze_distributions(self) -> None:
        """Analyze value distributions for categorical and numeric columns."""
        logger.info("Analyzing distributions...")
        
        self.distribution_report = {
            'categorical_distributions': {},
            'numeric_distributions': {}
        }
        
        # Categorical columns
        categorical_df = self.df.select_dtypes(include=['object', 'category'])
        
        for column in categorical_df.columns:
            value_counts = self.df[column].value_counts()
            
            self.distribution_report['categorical_distributions'][column] = {
                'unique_values': int(self.df[column].nunique()),
                'top_10_values': value_counts.head(10).to_dict(),
                'missing_count': int(self.df[column].isnull().sum()),
            }
        
        # Numeric columns - Create bins
        numeric_df = self.df.select_dtypes(include=[np.number])
        
        for column in numeric_df.columns:
            col_data = numeric_df[column].dropna()
            
            if len(col_data) > 0 and col_data.nunique() > 10:
                # Create histograms for numeric columns
                hist, bin_edges = np.histogram(col_data, bins=10)
                
                self.distribution_report['numeric_distributions'][column] = {
                    'unique_values': int(col_data.nunique()),
                    'histogram_bins': 10,
                    'histogram_counts': hist.tolist(),
                    'histogram_edges': bin_edges.tolist(),
                }
        
        self.report['distributions'] = self.distribution_report

    # ========================================================
    # 5. COLUMN-BY-COLUMN SUMMARIES
    # ========================================================

    def _generate_column_summaries(self) -> None:
        """Generate detailed summaries for each column."""
        logger.info("Generating column-by-column summaries...")
        
        column_summaries = {}
        
        for column in self.df.columns:
            col_dtype = str(self.df[column].dtype)
            null_count = int(self.df[column].isnull().sum())
            null_percentage = round(null_count / len(self.df) * 100, 2)
            
            column_summaries[column] = {
                'data_type': col_dtype,
                'non_null_count': int(len(self.df[column]) - null_count),
                'null_count': null_count,
                'null_percentage': null_percentage,
                'unique_values': int(self.df[column].nunique()),
                'distinct_percentage': round(
                    self.df[column].nunique() / len(self.df) * 100, 2
                ),
            }
            
            # Add type-specific information
            if pd.api.types.is_numeric_dtype(self.df[column]):
                col_data = self.df[column].dropna()
                if len(col_data) > 0:
                    column_summaries[column].update({
                        'min_value': float(col_data.min()),
                        'max_value': float(col_data.max()),
                        'mean_value': round(float(col_data.mean()), 4),
                    })
            else:
                # For string columns, get top value
                top_value = self.df[column].value_counts().idxmax() if not self.df[column].value_counts().empty else 'N/A'
                column_summaries[column]['most_frequent_value'] = str(top_value)
        
        self.column_summaries = column_summaries
        self.report['column_summaries'] = column_summaries

    # ========================================================
    # 6. EXTRACT INSIGHTS AND PATTERNS
    # ========================================================

    def _extract_insights(self) -> None:
        """Extract meaningful insights and patterns from the data."""
        logger.info("Extracting insights and patterns...")
        
        insights = {
            'highly_sparse_columns': [],
            'highly_dense_columns': [],
            'constant_columns': [],
            'binary_columns': [],
            'date_columns': [],
            'data_quality_issues': [],
        }
        
        for column in self.df.columns:
            null_percentage = self.column_summaries[column]['null_percentage']
            unique_count = self.column_summaries[column]['unique_values']
            total_rows = len(self.df)
            
            # Sparse columns (>50% null)
            if null_percentage > 50:
                insights['highly_sparse_columns'].append({
                    'column': column,
                    'null_percentage': null_percentage,
                })
            
            # Dense columns (<5% null)
            if null_percentage < 5:
                insights['highly_dense_columns'].append(column)
            
            # Constant columns (only 1 unique value)
            if unique_count == 1:
                insights['constant_columns'].append(column)
            
            # Binary columns (2 unique values)
            if unique_count == 2:
                insights['binary_columns'].append(column)
            
            # Data quality issues
            if null_percentage > 20:
                insights['data_quality_issues'].append({
                    'column': column,
                    'issue': f'High null percentage: {null_percentage}%',
                })
        
        self.report['insights'] = insights

    # ========================================================
    # 7. KPI CALCULATION
    # ========================================================

    def _calculate_kpis(self) -> None:
        """Calculate key performance indicators."""
        logger.info("Calculating KPIs...")
        
        kpis = {}
        
        # Data Completeness KPI
        total_cells = self.df.shape[0] * self.df.shape[1]
        null_cells = self.df.isnull().sum().sum()
        completeness_rate = round(
            ((total_cells - null_cells) / total_cells * 100), 2
        )
        kpis['data_completeness_rate'] = completeness_rate
        
        # Data Quality Score (0-100)
        duplicate_ratio = (self.df.duplicated().sum() / len(self.df)) * 100
        quality_score = round(completeness_rate * 0.6 + (100 - duplicate_ratio) * 0.4, 2)
        kpis['data_quality_score'] = quality_score
        
        # Duplicate Rate
        kpis['duplicate_rate_percentage'] = round(duplicate_ratio, 2)
        
        # Sparsity Rate (% of nulls)
        kpis['sparsity_rate'] = round((null_cells / total_cells * 100), 2)
        
        # Column Health Score
        column_health_scores = {}
        for col in self.df.columns:
            null_pct = (self.df[col].isnull().sum() / len(self.df)) * 100
            health_score = 100 - null_pct
            column_health_scores[col] = round(health_score, 2)
        
        kpis['column_health_scores'] = column_health_scores
        kpis['average_column_health'] = round(
            np.mean(list(column_health_scores.values())), 2
        )
        
        # Numeric Column KPIs
        numeric_df = self.df.select_dtypes(include=[np.number])
        if len(numeric_df) > 0:
            numeric_kpis = {}
            
            for col in numeric_df.columns:
                col_data = numeric_df[col].dropna()
                if len(col_data) > 0:
                    cv = (col_data.std() / col_data.mean()) if col_data.mean() != 0 else 0
                    numeric_kpis[col] = {
                        'coefficient_of_variation': round(cv, 4),
                        'data_range': round(col_data.max() - col_data.min(), 4),
                        'data_range_ratio': round(
                            (col_data.max() - col_data.min()) / col_data.mean() 
                            if col_data.mean() != 0 else 0, 4
                        ),
                    }
            
            kpis['numeric_column_metrics'] = numeric_kpis
        
        self.report['kpis'] = kpis

    # ========================================================
    # 8. BUSINESS SUMMARY GENERATION
    # ========================================================

    def _generate_business_summary(self) -> None:
        """Generate high-level business summary."""
        logger.info("Generating business summary...")
        
        business_summary = {}
        
        # Dataset Overview
        business_summary['dataset_overview'] = {
            'total_records': int(self.df.shape[0]),
            'total_attributes': int(self.df.shape[1]),
            'storage_size_mb': round(self.df.memory_usage(deep=True).sum() / 1024**2, 2),
            'records_per_mb': round(
                self.df.shape[0] / (self.df.memory_usage(deep=True).sum() / 1024**2), 2
            ),
        }
        
        # Data Maturity Assessment
        quality_score = self.report.get('kpis', {}).get('data_quality_score', 0)
        completeness = self.report.get('kpis', {}).get('data_completeness_rate', 0)
        
        if quality_score >= 80 and completeness >= 90:
            maturity = 'MATURE'
        elif quality_score >= 60 and completeness >= 70:
            maturity = 'DEVELOPING'
        else:
            maturity = 'NEEDS_IMPROVEMENT'
        
        business_summary['data_maturity'] = {
            'level': maturity,
            'quality_score': quality_score,
            'completeness_score': completeness,
        }
        
        # Data Distribution Summary
        categorical_df = self.df.select_dtypes(include=['object', 'category'])
        numeric_df = self.df.select_dtypes(include=[np.number])
        
        business_summary['data_composition'] = {
            'categorical_columns': len(categorical_df),
            'numeric_columns': len(numeric_df),
            'datetime_columns': len(self.df.select_dtypes(include=['datetime64'])),
            'other_types': len(self.df.columns) - len(categorical_df) - len(numeric_df),
        }
        
        # Top Value Insights
        top_insights = {}
        for col in categorical_df.columns[:5]:
            top_value = self.df[col].value_counts().idxmax() if not self.df[col].value_counts().empty else 'N/A'
            top_count = self.df[col].value_counts().max() if not self.df[col].value_counts().empty else 0
            top_percentage = round((top_count / len(self.df)) * 100, 2)
            
            top_insights[col] = {
                'most_common_value': str(top_value),
                'frequency': int(top_count),
                'percentage': top_percentage,
            }
        
        business_summary['top_value_insights'] = top_insights
        
        self.report['business_summary'] = business_summary

    # ========================================================
    # 9. TREND DETECTION
    # ========================================================

    def _detect_trends(self) -> None:
        """Detect trends in numeric columns."""
        logger.info("Detecting trends...")
        
        trends = {}
        numeric_df = self.df.select_dtypes(include=[np.number])
        
        for col in numeric_df.columns:
            col_data = numeric_df[col].dropna()
            
            if len(col_data) > 2:
                # Simple linear regression for trend detection
                x = np.arange(len(col_data))
                y = col_data.values
                
                # Calculate trend
                z = np.polyfit(x, y, 1)
                slope = z[0]
                
                # Calculate R-squared
                p = np.poly1d(z)
                yhat = p(x)
                ybar = np.mean(y)
                ssreg = np.sum((yhat - ybar) ** 2)
                sstot = np.sum((y - ybar) ** 2)
                r_squared = ssreg / sstot if sstot != 0 else 0
                
                # Determine trend direction
                if abs(slope) < 0.0001:
                    trend_direction = 'STABLE'
                elif slope > 0:
                    trend_direction = 'UPWARD'
                else:
                    trend_direction = 'DOWNWARD'
                
                trends[col] = {
                    'trend_direction': trend_direction,
                    'slope': round(float(slope), 6),
                    'r_squared': round(float(r_squared), 4),
                    'trend_strength': 'STRONG' if r_squared > 0.7 else 'MODERATE' if r_squared > 0.4 else 'WEAK',
                    'average_value': round(float(col_data.mean()), 4),
                    'trend_magnitude': round(abs(float(slope)), 6),
                }
        
        self.report['trend_analysis'] = trends

    # ========================================================
    # 10. DASHBOARD METRICS
    # ========================================================

    def _prepare_dashboard_metrics(self) -> None:
        """Prepare metrics optimized for dashboard visualization."""
        logger.info("Preparing dashboard metrics...")
        
        dashboard_metrics = {
            'cards': {},
            'charts': {},
            'tables': {},
        }
        
        # KPI Cards
        kpis = self.report.get('kpis', {})
        dashboard_metrics['cards'] = {
            'total_records': {
                'value': self.report.get('overview', {}).get('total_rows', 0),
                'label': 'Total Records',
                'unit': 'rows',
            },
            'data_quality': {
                'value': kpis.get('data_quality_score', 0),
                'label': 'Data Quality Score',
                'unit': '%',
                'threshold_good': 80,
                'threshold_warning': 60,
            },
            'completeness': {
                'value': kpis.get('data_completeness_rate', 0),
                'label': 'Data Completeness',
                'unit': '%',
                'threshold_good': 90,
                'threshold_warning': 70,
            },
            'duplicate_count': {
                'value': self.report.get('data_quality', {}).get('duplicate_rows', 0),
                'label': 'Duplicate Rows',
                'unit': 'rows',
            },
        }
        
        # Distribution Charts
        distributions = self.report.get('distributions', {})
        dashboard_metrics['charts']['categorical_distributions'] = (
            distributions.get('categorical_distributions', {})
        )
        dashboard_metrics['charts']['numeric_distributions'] = (
            distributions.get('numeric_distributions', {})
        )
        
        # Statistical Summary Table
        stats = self.report.get('statistics', {})
        if 'statistics' in stats:
            dashboard_metrics['tables']['statistical_summary'] = stats['statistics']
        
        # Column Health Table
        column_health = kpis.get('column_health_scores', {})
        dashboard_metrics['tables']['column_health'] = {
            col: {'health_score': score}
            for col, score in column_health.items()
        }
        
        # Trend Analysis for Charts
        trends = self.report.get('trend_analysis', {})
        dashboard_metrics['charts']['trends'] = trends
        
        self.report['dashboard_metrics'] = dashboard_metrics

    # ========================================================
    # 11. ANOMALY DETECTION
    # ========================================================

    def _detect_anomalies(self) -> None:
        """Detect anomalies in the dataset using statistical methods."""
        logger.info("Detecting anomalies...")
        
        anomalies = {
            'outliers': {},
            'unusual_patterns': [],
            'statistical_anomalies': {},
        }
        
        numeric_df = self.df.select_dtypes(include=[np.number])
        
        for col in numeric_df.columns:
            col_data = numeric_df[col].dropna()
            
            if len(col_data) > 3:
                # Z-score method
                z_scores = np.abs(stats.zscore(col_data))
                outlier_indices = np.where(z_scores > 3)[0]
                
                if len(outlier_indices) > 0:
                    outlier_values = col_data.iloc[outlier_indices].tolist()
                    anomalies['outliers'][col] = {
                        'count': len(outlier_indices),
                        'percentage': round((len(outlier_indices) / len(col_data)) * 100, 2),
                        'sample_outliers': [round(float(v), 4) for v in outlier_values[:5]],
                        'method': 'z_score',
                    }
                
                # IQR method
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                iqr_outliers = col_data[
                    (col_data < lower_bound) | (col_data > upper_bound)
                ]
                
                if len(iqr_outliers) > 0:
                    anomalies['statistical_anomalies'][col] = {
                        'outlier_count': len(iqr_outliers),
                        'lower_bound': round(float(lower_bound), 4),
                        'upper_bound': round(float(upper_bound), 4),
                        'iqr': round(float(IQR), 4),
                    }
        
        # Categorical anomalies
        categorical_df = self.df.select_dtypes(include=['object', 'category'])
        for col in categorical_df.columns:
            value_counts = self.df[col].value_counts()
            
            if len(value_counts) > 1:
                # Check for highly imbalanced categories
                max_count = value_counts.max()
                min_count = value_counts.min()
                
                if max_count > 0:
                    imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')
                    
                    if imbalance_ratio > 10:
                        anomalies['unusual_patterns'].append({
                            'column': col,
                            'issue': 'highly_imbalanced_categories',
                            'imbalance_ratio': round(imbalance_ratio, 2),
                            'dominant_value': str(value_counts.idxmax()),
                        })
        
        self.report['anomalies'] = anomalies

    # ========================================================
    # 12. CORRELATION ANALYSIS
    # ========================================================

    def _analyze_correlations(self) -> None:
        """Analyze correlations between numeric columns."""
        logger.info("Analyzing correlations...")
        
        correlation_analysis = {
            'correlation_matrix': {},
            'strong_correlations': [],
        }
        
        numeric_df = self.df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) > 1:
            # Calculate correlation matrix
            corr_matrix = numeric_df.corr()
            
            # Convert to dictionary
            correlation_analysis['correlation_matrix'] = (
                corr_matrix.round(4).to_dict()
            )
            
            # Find strong correlations (absolute value > 0.7)
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    corr_value = corr_matrix.iloc[i, j]
                    
                    if abs(corr_value) > 0.7:
                        correlation_analysis['strong_correlations'].append({
                            'column_1': col1,
                            'column_2': col2,
                            'correlation': round(float(corr_value), 4),
                            'correlation_type': 'positive' if corr_value > 0 else 'negative',
                            'strength': 'very_strong' if abs(corr_value) > 0.9 else 'strong',
                        })
        
        self.report['correlation_analysis'] = correlation_analysis

    # ========================================================
    # 13. COMPILE FINAL REPORT
    # ========================================================

    def _compile_final_report(self) -> None:
        """Compile all analyses into a final comprehensive report."""
        logger.info("Compiling final comprehensive report...")
        
        self.report['summary_metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'total_sections': len(self.report),
            'sections_included': list(self.report.keys()),
            'report_version': '2.0',
            'analysis_layers': [
                'Overview',
                'Data Quality',
                'Statistics',
                'Distributions',
                'Column Summaries',
                'Insights',
                'KPIs',
                'Business Summary',
                'Trend Analysis',
                'Dashboard Metrics',
                'Anomaly Detection',
                'Correlation Analysis',
            ],
        }

    # ========================================================
    # HELPER METHOD - GET SUMMARY AS JSON
    # ========================================================

    def get_report(self) -> Dict[str, Any]:
        """
        Return the generated report.
        
        Returns:
            Dict: The comprehensive data summary report
        """
        return self.report

    # ========================================================
    # HELPER METHOD - GET SPECIFIC REPORT SECTION
    # ========================================================

    def get_report_section(self, section: str) -> Dict[str, Any]:
        """
        Get a specific section of the report.
        
        Args:
            section (str): Section name ('overview', 'data_quality', 'statistics', etc.)
            
        Returns:
            Dict: Specific report section or empty dict if not found
        """
        return self.report.get(section, {})

    # ========================================================
    # EXECUTIVE SUMMARY
    # ========================================================

    def get_executive_summary(self) -> Dict[str, Any]:
        """
        Get a high-level executive summary of the analysis.
        
        Returns:
            Dict: Executive summary with key metrics and insights
        """
        kpis = self.report.get('kpis', {})
        business = self.report.get('business_summary', {})
        anomalies = self.report.get('anomalies', {})
        
        executive_summary = {
            'data_health': {
                'quality_score': kpis.get('data_quality_score', 0),
                'completeness': kpis.get('data_completeness_rate', 0),
                'duplicate_rate': kpis.get('duplicate_rate_percentage', 0),
            },
            'data_profile': {
                'total_records': self.report.get('overview', {}).get('total_rows', 0),
                'total_attributes': self.report.get('overview', {}).get('total_columns', 0),
                'maturity_level': business.get('data_maturity', {}).get('level', 'UNKNOWN'),
            },
            'data_issues': {
                'total_anomalies': len(anomalies.get('outliers', {})),
                'unusual_patterns': len(anomalies.get('unusual_patterns', [])),
            },
            'recommendations': self._generate_recommendations(),
        }
        
        return executive_summary

    # ========================================================
    # RECOMMENDATIONS ENGINE
    # ========================================================

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        kpis = self.report.get('kpis', {})
        anomalies = self.report.get('anomalies', {})
        insights = self.report.get('insights', {})
        
        # Data Quality Recommendations
        quality_score = kpis.get('data_quality_score', 0)
        if quality_score < 70:
            recommendations.append(
                'CRITICAL: Data quality is below acceptable threshold. '
                'Recommend comprehensive data cleaning.'
            )
        
        completeness = kpis.get('data_completeness_rate', 0)
        if completeness < 80:
            recommendations.append(
                'WARNING: Data completeness is low. '
                'Consider imputation or data collection strategies.'
            )
        
        # Duplicate Data
        duplicate_rate = kpis.get('duplicate_rate_percentage', 0)
        if duplicate_rate > 5:
            recommendations.append(
                f'ALERT: {duplicate_rate}% duplicate rows detected. '
                'Review deduplication strategy.'
            )
        
        # Sparse Columns
        sparse_cols = insights.get('highly_sparse_columns', [])
        if len(sparse_cols) > 3:
            recommendations.append(
                f'WARNING: {len(sparse_cols)} highly sparse columns detected. '
                'Consider column removal or data collection.'
            )
        
        # Anomalies
        total_outliers = len(anomalies.get('outliers', {}))
        if total_outliers > 0:
            recommendations.append(
                f'INFO: {total_outliers} columns with outliers detected. '
                'Review for data entry errors or domain-specific phenomena.'
            )
        
        # Missing Recommendations
        if not recommendations:
            recommendations.append(
                'PASS: Dataset quality is good. '
                'Ready for analytical modeling.'
            )
        
        return recommendations

    # ========================================================
    # ADVANCED FILTERING
    # ========================================================

    def get_insights_by_severity(self) -> Dict[str, List[str]]:
        """
        Get insights organized by severity level.
        
        Returns:
            Dict: Insights categorized by CRITICAL, WARNING, INFO
        """
        insights_by_severity = {
            'CRITICAL': [],
            'WARNING': [],
            'INFO': [],
        }
        
        kpis = self.report.get('kpis', {})
        
        # Critical issues
        if kpis.get('data_quality_score', 0) < 60:
            insights_by_severity['CRITICAL'].append(
                f"Data quality score critically low: {kpis.get('data_quality_score', 0)}%"
            )
        
        if kpis.get('data_completeness_rate', 0) < 70:
            insights_by_severity['CRITICAL'].append(
                f"Data completeness critically low: {kpis.get('data_completeness_rate', 0)}%"
            )
        
        # Warnings
        if kpis.get('duplicate_rate_percentage', 0) > 5:
            insights_by_severity['WARNING'].append(
                f"High duplicate rate: {kpis.get('duplicate_rate_percentage', 0)}%"
            )
        
        sparse_cols = self.report.get('insights', {}).get('highly_sparse_columns', [])
        if sparse_cols:
            insights_by_severity['WARNING'].append(
                f"Sparse columns detected: {[col['column'] for col in sparse_cols]}"
            )
        
        # Informational
        insights_by_severity['INFO'].append(
            f"Dataset contains {self.report.get('overview', {}).get('total_rows', 0)} records"
        )
        insights_by_severity['INFO'].append(
            f"Average column health: {kpis.get('average_column_health', 0)}%"
        )
        
        return {k: v for k, v in insights_by_severity.items() if v}

    # ========================================================
    # EXPORT UTILITIES
    # ========================================================

    def get_summary_for_dashboard(self) -> Dict[str, Any]:
        """
        Get a streamlined version optimized for dashboard rendering.
        
        Returns:
            Dict: Dashboard-ready metrics and visualizations
        """
        return {
            'metrics': self.report.get('dashboard_metrics', {}),
            'kpis': self.report.get('kpis', {}),
            'trends': self.report.get('trend_analysis', {}),
            'anomalies': self.report.get('anomalies', {}),
            'recommendations': self._generate_recommendations(),
            'generated_at': self.report.get('summary_metadata', {}).get('generated_at'),
        }

    def get_data_quality_report(self) -> Dict[str, Any]:
        """
        Get detailed data quality and completeness report.
        
        Returns:
            Dict: Data quality metrics and issues
        """
        return {
            'overview': self.report.get('data_quality', {}),
            'kpis': {
                'quality_score': self.report.get('kpis', {}).get('data_quality_score', 0),
                'completeness': self.report.get('kpis', {}).get('data_completeness_rate', 0),
            },
            'column_health': self.report.get('kpis', {}).get('column_health_scores', {}),
            'anomalies': self.report.get('anomalies', {}),
            'insights': self.report.get('insights', {}),
        }


# ========================================================
# CONVENIENCE FUNCTION - LEGACY SUPPORT
# ========================================================

def generate_dataset_summary(file_path: str) -> Dict[str, Any]:
    """
    Convenience function for generating a basic dataset summary from a file.
    Supports both CSV and XLSX formats.
    
    Args:
        file_path (str): Path to the dataset file
        
    Returns:
        Dict: Basic dataset summary
    """
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            logger.error(f"Unsupported file format: {file_path}")
            return {}
        
        service = SummaryService()
        return service.generate_complete_summary(df)
    
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return {}