import pandas as pd 
from datetime import datetime , timedelta
import logging
from app.services.retail_analytics_service.modules.revenue_analytics import RevenueAnalytics

logger = logging.getLogger(__name__)

class CustomerAnalytics :
    """ Module for customer analytics in retail datasets. """

    def __init__(self,df):
        self.df = df
        self.results = {}
        self.revenue_analytics = RevenueAnalytics(df)

    #================================================================
    # COLUMN DETECTION
    #================================================================

    def _find_customer_id_column(self):
        """Detect the customer ID column in the dataset."""
        possible_names = ['customer_id', 'customerid', 'cust_id', 'client_id', 'user_id', 'buyer_id','account_id']

        df_col_lower = {col.lower(): col for col in self.df.columns}
        for name in possible_names :
            if name in df_col_lower:
                col = df_col_lower[name]
                logger.info(f"Customer ID column detected: {col}")
                return col
            
        logger.warning("Customer ID column not found.")
        return None
    
    def _find_customer_email_column(self):
        """Detect the customer email column in the dataset."""
        email_names = ['email', 'customer_email', 'user_email', 'buyer_email']
        
        df_col_lower = {col.lower(): col for col in self.df.columns}

        for name in email_names :
            if name in df_col_lower:
                col = df_col_lower[name]
                logger.info(f"Customer email column detected: {col}")
                return col
        logger.warning("Customer email column not found.")
        return None
    
    def _find_customer_name_column(self):
        """Detect the customer name column in the dataset."""
        name_names = ['name', 'customer_name', 'user_name', 'buyer_name','account_name']
        
        df_col_lower = {col.lower(): col for col in self.df.columns}

        for name in name_names :
            if name in df_col_lower:
                col = df_col_lower[name]
                logger.info(f"Customer name column detected: {col}")
                return col
        logger.warning("Customer name column not found.")
        return None
    
    def _find_date_column(self):
        """Detect the date column in the dataset."""
        return self.revenue_analytics._ensure_date_column()
    

    #================================================================
    # ANALYTICS METHODS
    #================================================================

    def _calculate_customer_counts(self):
        """Calculate total unique customers."""
        try:
            customer_id_col = self._find_customer_id_column()
            if not customer_id_col:
                logger.error("Cannot calculate customer counts without a customer ID column.")
                return None
            
            total_unique_customers = self.df[customer_id_col].nunique()

            # transaction per customer
            transactions_per_customer = self.df.groupby(customer_id_col).size()

            new_customers = (transactions_per_customer == 1).sum()

            returning_customers = (transactions_per_customer > 1).sum()

            avg_transactions_per_customer =  transactions_per_customer.mean()

            result = {
                'total_unique_customers' : int(total_unique_customers),
                'new_customers': int(new_customers),
                'returning_customers': int(returning_customers),
                'new_customer_percentage': float(round((new_customers / total_unique_customers) * 100, 2)),
                'returning_customer_percentage': float(round((returning_customers / total_unique_customers) * 100, 2)),
                'avg_transactions_per_customer': float(round(avg_transactions_per_customer, 2))
            }

            logger.info(f"Customer counts calculated: {total_unique_customers} total customers, {new_customers} new, {returning_customers} returning.")
            return result
        except Exception as e:
            logger.error(f"Error calculating customer counts: {e}")
            return None
        
    def _calculate_customer_lifetime_value(self):
        """ Calculate customer lifetime value (CLV) using a simple revenue-based approach."""
        try :
            customer_id_col = self._find_customer_id_column()
            if not customer_id_col:
                logger.warning("No customer ID column found.")
                return None
            
            revenue = self.revenue_analytics._get_revenue_series()

            # revenue per customer
            customer_revenue = self.df.groupby(customer_id_col)[revenue.name].sum()

            # CLV STATISTICS
            total_clv = customer_revenue.sum()
            avg_clv = customer_revenue.sum()
            median_clv = customer_revenue.median()
            max_clv = customer_revenue.max()
            min_clv = customer_revenue.min()
            std_clv = customer_revenue.std()

            # top 10% clv customers

            top_10_percent_count = max(1, int(len(customer_revenue)*0.10))
            top_10_percent_clv = customer_revenue.nlargest(top_10_percent_count).sum()
            top_10_percent_contribution = (top_10_percent_clv / total_clv) * 100 if total_clv > 0 else 0

            result = {
                'total_clv': float(round(total_clv, 2)),
                'avg_clv': float(round(avg_clv, 2)),
                'median_clv': float(round(median_clv, 2)),
                'max_clv': float(round(max_clv, 2)),
                'min_clv': float(round(min_clv, 2)),
                'std_clv': float(round(std_clv, 2)),
                'top_10_percent_customers': int(top_10_percent_count),
                'top_10_percent_contribute': float(round(top_10_percent_contribution, 2)),
                'clv_distribution': {
                    'p25': float(round(customer_revenue.quantile(0.25), 2)),
                    'p50': float(round(customer_revenue.quantile(0.50), 2)),
                    'p75': float(round(customer_revenue.quantile(0.75), 2)),
                    'p90': float(round(customer_revenue.quantile(0.90), 2))
                }
            }
            logger.info(f"Customer lifetime value calculated: Total CLV={total_clv}, Avg CLV={avg_clv}, Top 10% contribution={top_10_percent_contribution}%")
            return result
        except Exception as e:
            logger.error(f"error calculating customer lifetime value: {e}")
            return None
        
    
    def _calculate_repeat_purchase_rate(self):
        """ Calculate percentage of customers who make repeat purchase."""
        logger.info("Calculating repeat purchase rate...")

        try:
            customer_id_col = self._find_customer_id_column()
            if not customer_id_col:
                logger.warning("No customer ID column found.")
                return None
            
            transactions_per_customer = self.df.groupby(customer_id_col).size()

            repeat_customers = (transactions_per_customer > 1).sum()
            total_customers = len(transactions_per_customer)

            repeat_purchase_rate = (repeat_customers / total_customers) * 100 if total_customers > 0 else 0

            avg_repeat_purchase = transactions_per_customer[transactions_per_customer] >= 2 .mean()

            purchase_frequency = transactions_per_customer.value_counts().sort_index()

            frequency_buckets = {
                '1_purchase': int(purchase_frequency.get(1,0)),
                '2_purchase': int(purchase_frequency.get(2,0)),
                '3_5_purchases': int((purchase_frequency[(purchase_frequency.index >= 3) & (purchase_frequency.index <= 5)]).sum()),
                '6_10_purchases': int((purchase_frequency[(purchase_frequency.index > 5) & (purchase_frequency.index <= 10)]).sum()),
                '11_plus_purchases': int((purchase_frequency[purchase_frequency.index > 10]).sum())
            }

            result = {
                'total_customers': int(total_customers),
                'repeat_customers': int(repeat_customers),
                'repeat_purchase_rate':float(round(repeat_purchase_rate,2)),
                'one_time_buyers':int(total_customers - repeat_customers),
                'avg_repeat_purchases_per_repeat_customers' :float(round(avg_repeat_purchase)),
                'purchase_frequency_distribution': frequency_buckets
            }

            logger.info(f"Repeat purchase rate : {repeat_purchase_rate:.2f}%")
            return result
        except Exception as e :
            logger.error(f"Error calculating repeat purchase rate : {e}")
            return None
        
    
    def _calculate_customer_retention(self):
        """ Calculate customer retention rate between periods."""

        logger.info("Calculating customer retention.")

        try:
            customer_id_col = self._find_customer_id_column()
            date_col = self._find_date_column()

            if not customer_id_col or not date_col :
                logger.warning("Missing customer ID or date column.")
                return None
            
            self.df[date_col] = pd.to_datetime(self.df[date_col])

            # get date range

            min_date = self.df[date_col].min()
            max_date = self.df[date_col].max()
            total_period = (min_date - max_date).days

            # split into period: first and last
            midpoint_date = min_date + timedelta(days=total_period/2)

            # customer in first period
            period_1_df = self.df[self.df[date_col] < midpoint_date]
            period_2_df = self.df[self.df[date_col] >= midpoint_date]

            customers_period_1 = set(period_1_df[customer_id_col].unique())
            customers_period_2 = set(period_2_df[customer_id_col].unique())

            retained_customers = customers_period_1 & customers_period_2

            new_customers = customers_period_2 - customers_period_1

            churned_customers = customers_period_1 - customers_period_2

            retention_rate = (len(retained_customers) / len(customers_period_1) * 100) if customers_period_1 else 0
            
            # Churn rate
            churn_rate = (len(churned_customers) / len(customers_period_1) * 100) if customers_period_1 else 0
            
            result = {
                'period_1': {
                    'start_date': min_date.strftime('%Y-%m-%d'),
                    'end_date': midpoint_date.strftime('%Y-%m-%d'),
                    'customers': int(len(customers_period_1))
                },
                'period_2': {
                    'start_date': midpoint_date.strftime('%Y-%m-%d'),
                    'end_date': max_date.strftime('%Y-%m-%d'),
                    'customers': int(len(customers_period_2))
                },
                'retained_customers': int(len(retained_customers)),
                'retention_rate': float(round(retention_rate, 2)),
                'churn_rate': float(round(churn_rate, 2)),
                'new_customers_period_2': int(len(new_customers)),
                'churned_customers': int(len(churned_customers))
            }
            logger.info(f"Retention calculated : {retention_rate:.2f}% retention, {churn_rate:.2f}% churn")
            return result
        except Exception as e:
            logger.error(f"Error calculating retention : {e}")
            return None
        
    def _calculate_cohort_analysis(self):
        """ calculating cohort analysis by cutomer id """

        logger.info("Calculating cohort analysis.")

        try :
            customer_id_col = self._find_customer_id_column()
            date_col= self._find_date_column()

            if not customer_id_col or not date_col :
                logger.warning("Missing customer_id or Date col")
                return None
            
            # ensure data is datetime
            self.df[date_col] = pd.to_datetime(self.df[date_col])

            # first purchase date per customer

            first_purchase_date = self.df.groupby(customer_id_col)[date_col].min()

            # create cohort (month of first purchase)

            first_purchase_date_copy = first_purchase_date.copy()
            cohort_month = first_purchase_date_copy.df.to_period('M')

            # add cohort to dataframe
            customer_cohort = pd.DataFrame({
                'customer_id':first_purchase_date.index,
                'cohort_month':cohort_month.values
            })
            # merge with original data
            df_with_cohort = self.df.merge(customer_cohort, left_on = customer_id_col, right_on='customer_id', how = 'left')

            # transaction month
            df_with_cohort['transaction_month'] = df_with_cohort[date_col].dt.to_peroid('M')

            # Calculate customer age in months
            df_with_cohort['customer_age_months'] = (df_with_cohort['transaction_month'] - df_with_cohort['cohort_month']).apply(lambda x: x.n)
            
            # cohort analysis
            revenue = self.revenue_analytics._get_revenue_series()
            df_with_cohort[revenue.name] = revenue.values

            cohort_data = df_with_cohort.groupby(['cohort_month','customer_age_months'])

            cohorts = cohort_data['cohort_month'].unique()
            cohort_list = []
            
            for cohort in sorted(cohorts)[-12:]:  # Last 12 months
                cohort_subset = cohort_data[cohort_data['cohort_month'] == cohort]
                cohort_info = {
                    'cohort_month': str(cohort),
                    'initial_customers': int(cohort_subset[cohort_subset['customer_age_months'] == 0]['customer_count'].values[0] if len(cohort_subset[cohort_subset['customer_age_months'] == 0]) > 0 else 0),
                    'total_revenue': float(round(cohort_subset['revenue'].sum(), 2)),
                    'customer_age_progression': cohort_subset[['customer_age_months', 'customer_count', 'revenue']].to_dict('records')
                }
                cohort_list.append(cohort_info)
            
            result = {
                'total_cohorts': len(cohorts),
                'cohort_analysis': cohort_list
            }
            
            logger.info(f"Cohort analysis calculated: {len(cohorts)} cohorts analyzed")
            return result
        
        except Exception as e:
            logger.error(f"Error calculating cohort analysis: {e}", exc_info=True)
            return None

    def _get_top_customers(self, metric='revenue', top_n=10):
        """GET TOP CUSTOMER BY SPECIFIED METRIC."""
        logger.info(f"Calculating top {top_n} customers by {metric}.")

        try:
            customer_id_col = self._find_customer_id_column()
            if not customer_id_col:
                logger.warning("No customer id column .")
                return None
            
            if metric == 'revenue' :
                revenue = self.revenue_analytics._get_revenue_series()
                customer_metrics = self.df.groupby(customer_id_col)[revenue.name].sum()
            elif metric == 'transactions':
                customer_metrics = self.df.groupby(customer_id_col).size()
            else:
                logger.warning(f"Unknown metric: {metric}")
                return None
            top_customers = customer_metrics.nlargest(top_n)

            result = []

            for rank,(customer_id, value) in enumerate(top_customers.items(),1):
                result.append(
                    {
                        'rank':rank,
                        'customer_id':str(customer_id),
                        'value': float(round(value,2)),
                        'metric': metric
                    }
                )
            return result
        except Exception as e:
            logger.error(f"Error calculating top customers: {e}")
            return None
        

    def analyze(self):
        """Execute complete customer analysis"""

        logger.info("Starting customer analytics")

        try:
            customer_id_col = self._find_customer_id_column()
            if not customer_id_col:
                raise ValueError("Customer ID column is required for customer analytics.")
            
            self.results = {
                'customer_counts': self._calculate_customer_counts(),
                'customer_lifetime_value': self._calculate_customer_lifetime_value(),
                'repeat_purchase_analysis': self._calculate_repeat_purchase_rate(),
                'retention': self._calculate_customer_retention(),
                'cohort_analysis': self._calculate_cohort_analysis(),
                'top_customers_by_revenue': self._get_top_customers('revenue', 10),
                'top_customers_by_transactions': self._get_top_customers('transactions', 10)
            
            }

            logger.info("Customer analytics completed successfully.")
            return self.results
        except Exception as e:
            logger.error(f"Error during customer analytics: {e}")
            return {'error': str(e)}
        