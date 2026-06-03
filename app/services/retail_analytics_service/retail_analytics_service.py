import pandas as pd
import logging
from app.services.retail_analytics_service.modules.revenue_analytics import RevenueAnalytics
from app.services.retail_analytics_service.modules.product_analytics import ProductAnalytics
from app.services.retail_analytics_service.modules.customer_analytics import CustomerAnalytics

logger = logging.getLogger(__name__)

class RetailAnalyticsService:
    """
    Main orchestrator for all retail analytics modules.
    Coordinates analysis across Revenue, Product, and Customer dimensions.
    """

    def __init__(self, df, dataset_id=None):
        """
        Initialize the analytics service with a dataset.
        
        Args:
            df (pd.DataFrame): The dataset to analyze
            dataset_id (str, optional): Dataset identifier for tracking
        """
        self.df = df
        self.dataset_id = dataset_id
        self.results = {}
        
        # Initialize all analytics modules
        self.revenue_analytics = RevenueAnalytics(df)
        self.product_analytics = ProductAnalytics(df)
        self.customer_analytics = CustomerAnalytics(df)
        
        logger.info(f"RetailAnalyticsService initialized with {len(df)} records")

    def analyze(self):
        """
        Execute complete retail analysis across all modules.
        
        Returns:
            dict: Comprehensive analysis results with revenue, product, and customer insights
        """
        logger.info(f"Starting comprehensive retail analytics for dataset {self.dataset_id}")
        
        try:
            # Execute all module analyses
            revenue_results = self.revenue_analytics.analyze()
            product_results = self.product_analytics.analyze()
            customer_results = self.customer_analytics.analyze()
            
            # Aggregate results
            self.results = {
                'metadata': {
                    'dataset_id': self.dataset_id,
                    'records_analyzed': len(self.df),
                    'columns': list(self.df.columns),
                    'date_range': self._get_date_range()
                },
                'revenue_analytics': revenue_results,
                'product_analytics': product_results,
                'customer_analytics': customer_results,
                'executive_summary': self._generate_executive_summary(revenue_results, product_results, customer_results)
            }
            
            logger.info("Comprehensive retail analytics completed successfully")
            return self.results
        
        except Exception as e:
            logger.error(f"Error in comprehensive analytics: {e}", exc_info=True)
            return {'error': str(e), 'dataset_id': self.dataset_id}

    def analyze_revenue_only(self):
        """Execute revenue analysis only."""
        logger.info("Starting revenue analytics...")
        return self.revenue_analytics.analyze()

    def analyze_products_only(self):
        """Execute product analysis only."""
        logger.info("Starting product analytics...")
        return self.product_analytics.analyze()

    def analyze_customers_only(self):
        """Execute customer analysis only."""
        logger.info("Starting customer analytics...")
        return self.customer_analytics.analyze()

    def _get_date_range(self):
        """Get date range from data if available."""
        try:
            date_col = self.revenue_analytics._ensure_date_column()
            if date_col:
                min_date = pd.to_datetime(self.df[date_col]).min()
                max_date = pd.to_datetime(self.df[date_col]).max()
                return {
                    'start_date': min_date.strftime('%Y-%m-%d'),
                    'end_date': max_date.strftime('%Y-%m-%d')
                }
        except:
            pass
        return None

    def _generate_executive_summary(self, revenue_results, product_results, customer_results):
        """Generate high-level executive summary from all analyses."""
        logger.info("Generating executive summary...")
        
        try:
            summary = {}
            
            # Revenue summary
            if revenue_results and 'revenue_statistics' in revenue_results:
                rev_stats = revenue_results['revenue_statistics']
                summary['total_revenue'] = rev_stats.get('total', 0)
                summary['avg_order_value'] = revenue_results.get('average_order_value', 0)
                summary['order_count'] = revenue_results.get('order_count', 0)
            
            # Product summary
            if product_results and 'product_mix' in product_results:
                product_mix = product_results['product_mix']
                summary['unique_products'] = product_mix.get('unique_products', 0)
                summary['top_product'] = product_mix['product_mix'][0]['product_name'] if product_mix.get('product_mix') else None
            
            # Customer summary
            if customer_results and 'customer_counts' in customer_results:
                cust_counts = customer_results['customer_counts']
                summary['total_customers'] = cust_counts.get('total_unique_customers', 0)
                summary['returning_customer_pct'] = cust_counts.get('returning_customer_percentage', 0)
            
            # Insights
            if customer_results and 'retention' in customer_results:
                retention = customer_results['retention']
                summary['retention_rate'] = retention.get('retention_rate', 0)
                summary['churn_rate'] = retention.get('churn_rate', 0)
            
            if customer_results and 'customer_lifetime_value' in customer_results:
                clv = customer_results['customer_lifetime_value']
                summary['avg_customer_lifetime_value'] = clv.get('avg_clv', 0)
            
            return summary
        
        except Exception as e:
            logger.warning(f"Error generating executive summary: {e}")
            return {}
