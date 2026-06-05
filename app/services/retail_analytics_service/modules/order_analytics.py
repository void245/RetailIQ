import pandas as pd
import logging
from app.services.retail_analytics_service.modules.revenue_analytics import RevenueAnalytics

logger = logging.getLogger(__name__)

class OrderAnalytics:
    def __init__(self, df):
        self.df = df
        self.results = {}
        self.revenue_analytics = RevenueAnalytics(df)

    def _find_order_id_column(self):
        order_id_names = ['order_id', 'orderid', 'order_number', 'transaction_id']
        df_col_lower = {col.lower(): col for col in self.df.columns}
        for name in order_id_names:
            if name in df_col_lower:
                return df_col_lower[name]
        return None

    def _find_customer_id_column(self):
        customer_id_names = ['customer_id', 'customer', 'user_id', 'buyer_id', 'account_id']
        df_col_lower = {col.lower(): col for col in self.df.columns}
        for name in customer_id_names:
            if name in df_col_lower:
                return df_col_lower[name]
        return None

    def _calculate_order_metrics(self):
        logger.info('Calculating order metrics...')
        try:
            order_id_col = self._find_order_id_column()
            if not order_id_col:
                return None
            revenue = self.revenue_analytics._get_revenue_series()
            total_orders = self.df[order_id_col].nunique()
            items_per_order = self.df.groupby(order_id_col).size()
            revenue_per_order = self.df.groupby(order_id_col)[revenue.name].sum()
            
            return {
                'total_orders': int(total_orders),
                'avg_items_per_order': float(round(items_per_order.mean(), 2)),
                'avg_order_value': float(round(revenue_per_order.mean(), 2)),
                'median_order_value': float(round(revenue_per_order.median(), 2)),
                'max_order_value': float(round(revenue_per_order.max(), 2)),
                'min_order_value': float(round(revenue_per_order.min(), 2))
            }
        except Exception as e:
            logger.error(f'Error: {e}', exc_info=True)
            return None

    def _calculate_order_size_distribution(self):
        try:
            order_id_col = self._find_order_id_column()
            if not order_id_col:
                return None
            items_per_order = self.df.groupby(order_id_col).size()
            return {
                'single_item_orders': int((items_per_order == 1).sum()),
                'two_to_five_items': int(((items_per_order >= 2) & (items_per_order <= 5)).sum()),
                'six_plus_items': int((items_per_order > 5).sum())
            }
        except Exception as e:
            logger.error(f'Error: {e}', exc_info=True)
            return None

    def analyze(self):
        logger.info('Starting order analytics...')
        try:
            order_id_col = self._find_order_id_column()
            if not order_id_col:
                raise ValueError('Cannot find order ID column')
            
            self.results = {
                'order_metrics': self._calculate_order_metrics(),
                'order_size_distribution': self._calculate_order_size_distribution()
            }
            logger.info('Order analytics completed')
            return self.results
        except Exception as e:
            logger.error(f'Order analytics error: {e}', exc_info=True)
            return {'error': str(e)}
