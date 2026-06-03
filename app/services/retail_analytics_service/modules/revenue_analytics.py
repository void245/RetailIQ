import pandas as pd
import logging 
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

class RevenueAnalytics:
    """
    Comprehensive revenue analytics module.
    Handles multiple data structures and calculates all revenue-related metrics.
    """

    def __init__(self, df):
        """
        Initialize with dataframe.
        
        Args:
            df: Pandas DataFrame with transaction data
        """
        self.df = df 
        self.results = {}
        self.revenue_method = None
        self.revenue_series = None  # Cache revenue calculations

    # =====================================================
    # STEP 1: COLUMN DETECTION & VALIDATION
    # =====================================================

    def _find_revenue_column(self):
        """
        Identify pre-calculated revenue column in dataset.
        Handles flexible column naming.
        """
        possible_names = [
            'amount', 'revenue', 'total', 'sales', 
            'sale_amount', 'order_amount', 'net_revenue',
            'gross_revenue', 'price', 'total_price',
            'total_revenue', 'sales_amount', 'sales_revenue'
        ]
        
        # Case-insensitive column matching
        df_cols_lower = {col.lower(): col for col in self.df.columns}

        for possible_name in possible_names:
            if possible_name in df_cols_lower:
                actual_col = df_cols_lower[possible_name] 
                logger.info(f"Found revenue column: {actual_col}")
                return actual_col
        
        return None
    
    def _find_quantity_price_columns(self):
        """Find quantity and price columns for calculated revenue."""
        
        df_cols_lower = {col.lower(): col for col in self.df.columns}

        # Find quantity column
        quantity_names = [
            'quantity', 'qty', 'units', 'units_sold', 
            'order_quantity', 'item_quantity', 'unit_count'
        ]
        quantity_col = None
        for name in quantity_names:
            if name in df_cols_lower:
                quantity_col = df_cols_lower[name]
                logger.info(f"Found quantity column: {quantity_col}")
                break

        # Find price column 
        price_names = [
            'price', 'unit_price', 'price_per_unit', 
            'unit_cost', 'product_price', 'sale_price'
        ]
        price_col = None
        for name in price_names:
            if name in df_cols_lower:
                price_col = df_cols_lower[name]
                logger.info(f"Found price column: {price_col}")
                break
        
        return quantity_col, price_col
    
    def _find_date_column(self):
        """Find date column for time-series analysis."""
        
        df_cols_lower = {col.lower(): col for col in self.df.columns}
        
        date_names = [
            'date', 'order_date', 'transaction_date', 'sales_date',
            'timestamp', 'created_at', 'purchase_date'
        ]
        
        for name in date_names:
            if name in df_cols_lower:
                col = df_cols_lower[name]
                logger.info(f"Found date column: {col}")
                return col
        
        return None
    
    def _find_customer_column(self):
        """Find customer identifier column."""
        
        df_cols_lower = {col.lower(): col for col in self.df.columns}
        
        customer_names = [
            'customer_id', 'customer', 'cust_id', 'user_id',
            'buyer_id', 'account_id'
        ]
        
        for name in customer_names:
            if name in df_cols_lower:
                col = df_cols_lower[name]
                logger.info(f"Found customer column: {col}")
                return col
        
        return None

    # =====================================================
    # STEP 2: DATA QUALITY & VALIDATION
    # =====================================================

    def _validate_revenue_data(self, revenue_series):
        """
        Validate revenue data quality.
        
        Returns:
            dict: Quality metrics and warnings
        """
        
        report = {
            'valid_count': 0,
            'null_count': 0,
            'negative_count': 0,
            'zero_count': 0,
            'warnings': []
        }
        
        # Count nulls
        null_count = revenue_series.isnull().sum()
        report['null_count'] = int(null_count)
        
        # Remove nulls for further analysis
        revenue_clean = revenue_series.dropna()
        
        # Count negatives (refunds, returns)
        negative_count = (revenue_clean < 0).sum()
        report['negative_count'] = int(negative_count)
        
        # Count zeros
        zero_count = (revenue_clean == 0).sum()
        report['zero_count'] = int(zero_count)
        
        # Valid records
        report['valid_count'] = len(revenue_clean)
        
        # Generate warnings
        if null_count > 0:
            percentage = (null_count / len(revenue_series)) * 100
            report['warnings'].append(
                f"Found {null_count} ({percentage:.2f}%) null values in revenue"
            )
        
        if negative_count > 0:
            percentage = (negative_count / len(revenue_clean)) * 100
            report['warnings'].append(
                f"Found {negative_count} ({percentage:.2f}%) negative values (refunds/returns)"
            )
        
        if zero_count > 0:
            report['warnings'].append(
                f"Found {zero_count} zero-value transactions"
            )
        
        return report

    # =====================================================
    # STEP 3: CORE REVENUE CALCULATION
    # =====================================================

    def _calculate_revenue_series(self):
        """
        Calculate or retrieve revenue for each transaction.
        
        Returns:
            pandas.Series: Revenue values
        """
        
        logger.info("Calculating revenue series...")
        
        # METHOD 1: Pre-calculated revenue column
        revenue_col = self._find_revenue_column()
        
        if revenue_col:
            logger.info(f"Using pre-calculated column: {revenue_col}")
            revenue_series = pd.to_numeric(
                self.df[revenue_col], 
                errors='coerce'
            )
            
            self.revenue_method = {
                'method': 'pre_calculated',
                'column': revenue_col
            }
            
            return revenue_series
        
        # METHOD 2: Calculate from Quantity × Price
        qty_col, price_col = self._find_quantity_price_columns()
        
        if qty_col and price_col:
            logger.info(f"Computing revenue: {qty_col} × {price_col}")
            
            quantity = pd.to_numeric(
                self.df[qty_col], 
                errors='coerce'
            )
            price = pd.to_numeric(
                self.df[price_col], 
                errors='coerce'
            )
            
            revenue_series = quantity * price
            
            self.revenue_method = {
                'method': 'calculated',
                'quantity_column': qty_col,
                'price_column': price_col
            }
            
            return revenue_series
        
        # METHOD 3: FAIL with helpful error
        error_msg = (
            f"Cannot calculate revenue!\n"
            f"Available columns: {list(self.df.columns)}\n"
            f"Need one of:\n"
            f"  1) Pre-calculated: amount, revenue, total, sales\n"
            f"  2) Quantity + Price: (qty) × (price)\n"
        )
        
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    def _get_revenue_series(self):
        """Get cached revenue series or calculate it."""
        if self.revenue_series is None:
            self.revenue_series = self._calculate_revenue_series()
        return self.revenue_series

    # =====================================================
    # STEP 4: AGGREGATE METRICS
    # =====================================================

    def _calculate_total_revenue(self):
        """Total revenue across all transactions."""
        revenue = self._get_revenue_series()
        return float(revenue.sum())
    
    def _calculate_order_count(self):
        """Count of unique orders/transactions."""
        return int(len(self.df))
    
    def _calculate_aov(self):
        """
        Average Order Value (AOV).
        Total Revenue / Number of Orders
        """
        total_revenue = self._calculate_total_revenue()
        order_count = self._calculate_order_count()
        
        if order_count == 0:
            return 0
        
        aov = total_revenue / order_count
        return float(round(aov, 2))
    
    def _calculate_revenue_stats(self):
        """Statistical breakdown of revenue."""
        revenue = self._get_revenue_series().dropna()
        
        return {
            'min': float(revenue.min()),
            'max': float(revenue.max()),
            'mean': float(revenue.mean()),
            'median': float(revenue.median()),
            'std_dev': float(revenue.std()),
            'q1': float(revenue.quantile(0.25)),
            'q3': float(revenue.quantile(0.75))
        }

    # =====================================================
    # STEP 5: TIME-SERIES REVENUE BREAKDOWN
    # =====================================================

    def _ensure_date_column(self):
        """Ensure we have a date column for time analysis."""
        date_col = self._find_date_column()
        
        if date_col is None:
            logger.warning("No date column found. Skipping time-series analysis.")
            return None
        
        # Convert to datetime
        try:
            self.df[date_col] = pd.to_datetime(
                self.df[date_col], 
                errors='coerce'
            )
        except Exception as e:
            logger.error(f"Error converting date column: {e}")
            return None
        
        return date_col
    
    def _calculate_revenue_by_date(self):
        """Revenue breakdown by date."""
        date_col = self._ensure_date_column()
        
        if date_col is None:
            return None
        
        revenue = self._get_revenue_series()
        
        revenue_by_date = self.df.groupby(date_col)[revenue.name].sum()
        revenue_by_date.index = revenue_by_date.index.strftime('%Y-%m-%d')
        
        return revenue_by_date.to_dict()
    
    def _calculate_revenue_by_period(self, period='D'):
        """
        Revenue grouped by time period.
        
        Args:
            period: 'D' for daily, 'W' for weekly, 'M' for monthly, 'Y' for yearly
        """
        date_col = self._ensure_date_column()
        
        if date_col is None:
            return None
        
        revenue = self._get_revenue_series()
        
        # Group by period
        grouped = self.df.groupby(
            pd.Grouper(key=date_col, freq=period)
        )[revenue.name].agg(['sum', 'count'])
        
        result = []
        for idx, row in grouped.iterrows():
            result.append({
                'period': idx.strftime('%Y-%m-%d') if period == 'D' else idx.strftime('%Y-%m'),
                'revenue': float(row['sum']),
                'order_count': int(row['count']),
                'avg_order_value': float(row['sum'] / row['count']) if row['count'] > 0 else 0
            })
        
        return result
    
    def _calculate_top_days(self, limit=10):
        """Top revenue-generating days."""
        revenue_by_date = self._calculate_revenue_by_date()
        
        if revenue_by_date is None:
            return None
        
        # Sort and get top N
        sorted_days = sorted(
            revenue_by_date.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [
            {'date': date, 'revenue': float(rev)}
            for date, rev in sorted_days[:limit]
        ]
    
    def _calculate_revenue_growth(self):
        """
        Month-over-month revenue growth rate.
        
        Returns:
            dict: Growth percentages by month
        """
        
        monthly_data = self._calculate_revenue_by_period('M')
        
        if monthly_data is None or len(monthly_data) < 2:
            return None
        
        growth = []
        for i in range(1, len(monthly_data)):
            current = monthly_data[i]['revenue']
            previous = monthly_data[i-1]['revenue']
            
            if previous == 0:
                growth_rate = 0
            else:
                growth_rate = ((current - previous) / previous) * 100
            
            growth.append({
                'period': monthly_data[i]['period'],
                'revenue': current,
                'previous_revenue': previous,
                'growth_rate': float(round(growth_rate, 2))
            })
        
        return growth

    # =====================================================
    # STEP 6: CUSTOMER-BASED METRICS
    # =====================================================

    def _calculate_revenue_per_customer(self):
        """Average revenue per unique customer."""
        customer_col = self._find_customer_column()
        
        if customer_col is None:
            logger.warning("No customer column found. Skipping customer metrics.")
            return None
        
        revenue = self._get_revenue_series()
        
        revenue_by_customer = self.df.groupby(customer_col)[revenue.name].sum()
        
        avg_revenue_per_customer = float(revenue_by_customer.mean())
        
        return {
            'avg_revenue_per_customer': avg_revenue_per_customer,
            'total_unique_customers': int(len(revenue_by_customer)),
            'median_revenue_per_customer': float(revenue_by_customer.median()),
            'max_customer_revenue': float(revenue_by_customer.max()),
            'min_customer_revenue': float(revenue_by_customer.min())
        }

    # =====================================================
    # STEP 7: CONCENTRATION & PARETO ANALYSIS
    # =====================================================

    def _calculate_revenue_concentration(self):
        """
        Pareto analysis: What percentage of revenue comes from top customers/orders?
        """
        
        revenue = self._get_revenue_series().dropna().sort_values(ascending=False)
        
        total_revenue = revenue.sum()
        cumulative_revenue = revenue.cumsum()
        cumulative_pct = (cumulative_revenue / total_revenue) * 100
        
        # Find 80/20 breakpoint
        top_20_pct_count = int(len(revenue) * 0.20)
        top_20_pct_revenue = cumulative_pct.iloc[top_20_pct_count] if top_20_pct_count < len(cumulative_pct) else cumulative_pct.iloc[-1]
        
        return {
            'top_20_percent_orders_generate': float(round(top_20_pct_revenue, 2)),
            'pareto_principle': f"Top 20% of orders generate {round(top_20_pct_revenue, 2)}% of revenue",
            'concentration_analysis': {
                'top_10_orders_pct': float(round(cumulative_pct.iloc[9] if len(cumulative_pct) > 9 else cumulative_pct.iloc[-1], 2)),
                'top_25_orders_pct': float(round(cumulative_pct.iloc[24] if len(cumulative_pct) > 24 else cumulative_pct.iloc[-1], 2)),
                'top_50_orders_pct': float(round(cumulative_pct.iloc[49] if len(cumulative_pct) > 49 else cumulative_pct.iloc[-1], 2))
            }
        }

    # =====================================================
    # MAIN ANALYZE METHOD
    # =====================================================

    def analyze(self):
        """
        Execute complete revenue analysis.
        
        Returns:
            dict: Comprehensive revenue metrics
        """
        
        logger.info("Starting revenue analytics...")
        
        try:
            # Calculate revenue series
            revenue_series = self._get_revenue_series()
            data_quality = self._validate_revenue_data(revenue_series)
            
            # Core metrics
            self.results = {
                'total_revenue': self._calculate_total_revenue(),
                'order_count': self._calculate_order_count(),
                'average_order_value': self._calculate_aov(),
                'calculation_method': self.revenue_method,
                'data_quality': data_quality,
                'revenue_statistics': self._calculate_revenue_stats()
            }
            
            # Time-series metrics
            self.results['revenue_by_date'] = self._calculate_revenue_by_date()
            self.results['revenue_by_month'] = self._calculate_revenue_by_period('M')
            self.results['top_days'] = self._calculate_top_days(10)
            self.results['growth_analysis'] = self._calculate_revenue_growth()
            
            # Customer metrics
            customer_metrics = self._calculate_revenue_per_customer()
            if customer_metrics:
                self.results['customer_metrics'] = customer_metrics
            
            # Concentration analysis
            self.results['pareto_analysis'] = self._calculate_revenue_concentration()
            
            logger.info("Revenue analytics completed successfully")
            return self.results
        
        except Exception as e:
            logger.error(f"Revenue calculation error: {e}", exc_info=True)
            return {'error': str(e)}