import pandas as pd
import logging
from app.services.retail_analytics_service.modules.revenue_analytics import RevenueAnalytics

logger = logging.getLogger(__name__)

class ProductAnalytics :
    """ Module for product-level analytics - sales trends, top products, etc."""

    def __init__(self,df):
        self.df = df 
        self.results = {}
        self.revenue_analytics = RevenueAnalytics(df)

    #================================================
    # COLUMN DETECTION
    #================================================

    def _find_product_column(self):
        product_names = ['product', 'item', 'product_name', 'item_name']

        df_col_lower = {col.lower() : col for col in self.df.columns}

        for name in product_names :
            if name in df_col_lower:
                col = df_col_lower[name]
                logger.info(f"Product column detected: {col}")
                return col
        logger.warning("No product column found.")
        return None
    
    def _find_price_column(self):
        """Detect price column using common keywords."""
        price_names = ['price', 'cost', 'unit_price']

        df_col_lower = {col.lower() : col for col in self.df.columns}

        for name in price_names :
            if name in df_col_lower:
                col = df_col_lower[name]
                logger.info(f"Price column detected: {col}")
                return col
        logger.warning("No price column found.")
        return None
    
    def _find_quantity_column(self):
        """Detect quantity column using common keywords."""
        quantity_names = ['quantity', 'qty', 'units_sold']

        df_col_lower = {col.lower() : col for col in self.df.columns}

        for name in quantity_names :
            if name in df_col_lower:
                col = df_col_lower[name]
                logger.info(f"Quantity column detected: {col}")
                return col
        logger.warning("No quantity column found.")
        return None
    
    def _find_product_name_column(self):
        """Detect product name/description column."""
        name_names = ['product_name', 'name', 'product_desc', 'description', 'item_name', 'title']
        
        df_col_lower = {col.lower(): col for col in self.df.columns}
        
        for name in name_names:
            if name in df_col_lower:
                col = df_col_lower[name]
                logger.info(f"Product name column detected: {col}")
                return col
        
        logger.warning("No product name column found.")
        return None
    
    #================================================
    # ANALYTICS METHODS
    #================================================
    def _get_top_products(self, metric='revenue', top_n=10):
        """Get top products by specified metric (revenue or quantity)."""
        product_col = self._find_product_column()
        if not product_col:
            logger.error("Cannot compute top products without product column.")
            return None
        
        revenue = self.revenue_analytics._get_revenue_series()
        if metric == 'revenue' :
            # find revenue for each product
            product_revenue = self.df.groupby(product_col)[revenue.name].sum()
            # sort and get top n
            top_products = product_revenue.nlargest(top_n)
            logger.info(f"Top {top_n} products by revenue computed.")
        elif metric == 'units' or metric == 'quantity' :
            qty_col = self._find_quantity_column()
            if qty_col:
                product_units = self.df.groupby(product_col)[qty_col].sum()
                top_products = product_units.nlargest(top_n)

        result = []
        for product_id , value in top_products.items():
            result.append({
                "product": product_id,
                "value": float(value),
                'metric': metric
            })

        return result
    
    def _get_bottom_products(self, metric='revenue', bottom_n=10):
        """Get bottom products by specified metric (revenue or quantity)."""
        product_col = self._find_product_column()
        if not product_col:
            logger.error("Cannot compute bottom products without product column.")
            return None
        revenue = self.revenue_analytics._get_revenue_series()
        if metric == 'revenue' :
            product_revenue = self.df.groupby(product_col)[revenue.name].sum()
            bottom_products = product_revenue.nsmallest(bottom_n)
            logger.info(f"Bottom {bottom_n} products by revenue computed.")
        elif metric == 'units' or metric == 'quantity' :
            qty_col = self._find_quantity_column()
            if qty_col:
                product_units = self.df.groupby(product_col)[qty_col].sum()
                bottom_products = product_units.nsmallest(bottom_n)
        
        result = []
        for product_id , value in bottom_products.items():
            result.append({
                "product": product_id,
                "value": float(value),
                'metric': metric
            })
        return result
    
    def _calculate_product_mix(self):

            logger.info("Calculating product mix...")
            
            try:
                product_col = self._find_product_column()
                if not product_col:
                    logger.warning("No product column found. Skipping product mix.")
                    return None
                
                # Get revenue series from RevenueAnalytics
                revenue = self.revenue_analytics._get_revenue_series()
                
                # Group by product and sum revenue
                product_revenue = self.df.groupby(product_col)[revenue.name].sum()
                
                # Sort by revenue descending
                product_revenue = product_revenue.sort_values(ascending=False)
                
                # Calculate total revenue
                total_revenue = product_revenue.sum()
                
                # Calculate percentages and cumulative percentages
                product_percentage = (product_revenue / total_revenue) * 100
                cumulative_percentage = product_percentage.cumsum()
                
                # Build product mix list
                product_mix = []
                for rank, (product_id, revenue_val) in enumerate(product_revenue.items(), 1):
                    
                    # Get product name if available
                    product_name = product_id  # Default to product_id
                    product_name_col = self._find_product_name_column()
                    
                    if product_name_col:
                        # Find product name from first occurrence
                        product_mask = self.df[product_col] == product_id
                        if product_mask.any():
                            product_name = self.df[product_mask][product_name_col].iloc[0]
                    
                    product_mix.append({
                        'product_id': str(product_id),
                        'product_name': str(product_name),
                        'revenue': float(revenue_val),
                        'percentage': float(round(product_percentage[product_id], 2)),
                        'cumulative_percentage': float(round(cumulative_percentage[product_id], 2)),
                        'rank': rank
                    })
                
                # Calculate revenue concentration
                num_products = len(product_revenue)
                top_10_pct_count = max(1, int(num_products * 0.10))
                top_20_pct_count = max(1, int(num_products * 0.20))
                top_50_pct_count = max(1, int(num_products * 0.50))
                
                top_10_pct_revenue = product_revenue.head(top_10_pct_count).sum()
                top_20_pct_revenue = product_revenue.head(top_20_pct_count).sum()
                top_50_pct_revenue = product_revenue.head(top_50_pct_count).sum()
                
                # Calculate what % of revenue these account for
                top_10_pct_contribution = (top_10_pct_revenue / total_revenue) * 100
                top_20_pct_contribution = (top_20_pct_revenue / total_revenue) * 100
                top_50_pct_contribution = (top_50_pct_revenue / total_revenue) * 100
                
                result = {
                    'total_revenue': float(total_revenue),
                    'unique_products': int(num_products),
                    'product_mix': product_mix,
                    'revenue_concentration': {
                        'top_10_percent_products_generate_percent': float(round(top_10_pct_contribution, 2)),
                        'top_20_percent_products_generate_percent': float(round(top_20_pct_contribution, 2)),
                        'top_50_percent_products_generate_percent': float(round(top_50_pct_contribution, 2)),
                        'top_10_products_count': top_10_pct_count,
                        'top_20_products_count': top_20_pct_count,
                        'top_50_products_count': top_50_pct_count
                    }
                }
                
                logger.info(f"Product mix calculated: {num_products} unique products")
                return result
            
            except Exception as e:
                logger.error(f"Error calculating product mix: {e}", exc_info=True)
                return None
            
    def analyze(self):
        """Execute complete product analysis."""
        logger.info("Starting product analytics...")
        
        try:
            product_col = self._find_product_column()
            if not product_col:
                raise ValueError("Cannot find product column in data")
            
            self.results = {
                'top_products': self._get_top_products('revenue', 10),
                'bottom_products': self._get_bottom_products('revenue', 10),
                'top_products_by_units': self._get_top_products('quantity', 10),
                'product_mix': self._calculate_product_mix(),
                'diversity': self._calculate_product_diversity(),
                'sales_velocity': self._calculate_sales_velocity(),
                'trends': self._calculate_product_trends()
            }
            
            logger.info("Product analytics completed successfully")
            return self.results
        
        except Exception as e:
            logger.error(f"Product analytics error: {e}", exc_info=True)
            return {'error': str(e)}
        
    
    def _calculate_product_diversity(self):
        """Calculate product diversity metrics
        
           return{
                dict :
                    'total_unique_products': int,
                    'avg_units_per_products': float,
                    'median_units_per_product': float,
                    'diversity_score':float,
                    'concentrtion_herfindahl':float,
                    'description':str
                }
        """
        logger.info("calculating product diversity...")

        try:
            product_col = self._find_product_column()
            qty_col = self._find_quantity_column()

            if not product_col or not qty_col:
                logger.warning("Missing product or quantity column. Skipping diversity calculation.")
                return None
            
            # to get units sold per units
            product_sales = self.df.groupby(product_col)[qty_col].sum()

            # total unique products
            total_unique_products = len(product_sales)

            # avg units per products
            avg_units_per_product = product_sales.mean()

            # median units per products
            median_units_per_product = product_sales.median()

            # calculate herfindalh index for concentration
            total_units = product_sales.sum()

            market_share = (product_sales / total_units) * 100

            HHI = (market_share ** 2).sum()

            diversity_score = max(0, 100 - (HHI / 100))

            if diversity_score >= 80:
                 description = "High diversity - sales distributed across many products"
            elif diversity_score >= 60:
                description = "Moderate diversity - healthy product mix"
            elif diversity_score >= 40:
                description = "Low diversity - some products dominate sales"
            else:
                description = "Very low diversity - heavily dependent on few products"

            result = {
                'total_unique_products': int(total_unique_products),
                'avg_units_per_product': float(round(avg_units_per_product, 2)),
                'median_units_per_product': float(round(median_units_per_product, 2)),
                'diversity_score': float(round(diversity_score, 2)),
                'concentration_herfindahl': float(round(HHI, 2)),
                'description': description
            }
            logger.info(f"Product diversity calculated: {total_unique_products} unique products, diversity score {diversity_score:.2f}")
            return result

        except Exception as e:
            logger.error(f"Error calculating product diversity: {e}", exc_info=True)
            return None
        
    def _calculate_sales_velocity(self):
       """ 
            calculate how fast the product are selling .

            returns : dict
       """

       logger.info("Calculating sales velocity...")
       try :
            product_col = self._find_product_column()
            qty_col = self._find_quantity_column()

            if not product_col or not qty_col:
                logger.warning("Missing product or quantity column. Skipping sales velocity calculation.")
                return None
            
            # get date column from revenue analytics
            sales_date_column = self.revenue_analytics._ensure_date_column()
            
            if not sales_date_column:
                logger.warning("No date column found. Skipping sales velocity calculation.")
                return None

            # Calculate global date range for all sales
            min_date = pd.to_datetime(self.df[sales_date_column]).min()
            max_date = pd.to_datetime(self.df[sales_date_column]).max()
            total_sales_period_days = (max_date - min_date).days + 1

            # Calculate total units and units per day
            total_units = self.df.groupby(product_col)[qty_col].sum()
            product_sales_velocity = total_units / total_sales_period_days

            product_sales_velocity = product_sales_velocity.sort_values(ascending=False)

            # Get 5 fast and slow selling products
            top_velocity_products = product_sales_velocity.head(5)
            bottom_velocity_products = product_sales_velocity.tail(5)

            result = {
                'date_range':  {
                'start_date': min_date.strftime('%Y-%m-%d'), 
                'end_date': max_date.strftime('%Y-%m-%d'), 
                'total_days': int(total_sales_period_days)
                },
                'overall_velocity': {
                    'units_per_day': float(round(product_sales_velocity.mean(), 2)),
                    'units_per_week': float(round(product_sales_velocity.mean() * 7, 2)), # (multiply units_per_day by 7)
                },
                'fastest_moving_products': [
                    # List of dicts with product_id and units_per_day
                    {'product_id': pid, 'units_per_day': float(round(velocity, 2))}
                    for pid, velocity in top_velocity_products.items()
                ],
                'slowest_moving_products': [
                    # List of dicts with product_id and units_per_day
                    {'product_id': pid, 'units_per_day': float(round(velocity, 2))}
                    for pid, velocity in bottom_velocity_products.items()
                ]
            }

            logger.info("Sales velocity calculated successfully.")
            return result
       
       except Exception as e:
            logger.error(f"Error calculating sales velocity: {e}", exc_info=True)
            return None
       
    
    def _calculate_product_trends(self):
        """Calculate product trends by comparing early vs recent period."""
        logger.info("Calculating product trends...")
        try:
            product_col = self._find_product_column()
            qty_col = self._find_quantity_column()
            sales_date_column = self.revenue_analytics._ensure_date_column()

            if not product_col or not qty_col or not sales_date_column:
                logger.warning("Missing required columns. Skipping product trends calculation.")
                return None
            
            # Ensure date column is datetime
            self.df[sales_date_column] = pd.to_datetime(self.df[sales_date_column])
            
            # Get global date range and find midpoint
            min_date = self.df[sales_date_column].min()
            max_date = self.df[sales_date_column].max()
            midpoint_date = min_date + (max_date - min_date) / 2
            
            # Split into early and recent periods
            early_period = self.df[self.df[sales_date_column] < midpoint_date]
            recent_period = self.df[self.df[sales_date_column] >= midpoint_date]
            
            # Get revenue for comparison
            revenue = self.revenue_analytics._get_revenue_series()
            
            # Calculate revenue by product in each period
            early_revenue = early_period.groupby(product_col)[revenue.name].sum()
            recent_revenue = recent_period.groupby(product_col)[revenue.name].sum()
            
            # Calculate growth rate
            all_products = set(early_revenue.index) | set(recent_revenue.index)
            
            growth_rates = []
            for product_id in all_products:
                early_rev = early_revenue.get(product_id, 0)
                recent_rev = recent_revenue.get(product_id, 0)
                
                # Handle edge cases
                if early_rev == 0 and recent_rev > 0:
                    growth_rate = 100.0  # New product in recent period
                elif early_rev == 0 and recent_rev == 0:
                    growth_rate = 0.0  # No sales
                elif early_rev > 0:
                    growth_rate = ((recent_rev - early_rev) / early_rev) * 100
                else:
                    growth_rate = 0.0
                
                growth_rates.append({
                    'product_id': str(product_id),
                    'early_period_revenue': float(early_rev),
                    'recent_period_revenue': float(recent_rev),
                    'growth_rate': float(round(growth_rate, 2))
                })
            
            # Sort by growth rate
            growth_rates = sorted(growth_rates, key=lambda x: x['growth_rate'], reverse=True)
            
            # Get rising stars and declining products
            rising_stars = [p for p in growth_rates if p['growth_rate'] > 5][:10]
            declining_products = [p for p in growth_rates if p['growth_rate'] < -5][:10]
            
            result = {
                'period_1': {
                    'start': min_date.strftime('%Y-%m-%d'),
                    'end': midpoint_date.strftime('%Y-%m-%d')
                },
                'period_2': {
                    'start': midpoint_date.strftime('%Y-%m-%d'),
                    'end': max_date.strftime('%Y-%m-%d')
                },
                'rising_stars': rising_stars,
                'declining_products': declining_products
            }
            
            logger.info("Product trends calculated successfully.")  
            return result
        
        except Exception as e:
            logger.error(f"Error calculating product trends: {e}", exc_info=True)
            return None
            
            