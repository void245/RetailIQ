import pandas as pd
import numpy as np
import logging
from datetime import datetime
from app.services.retail_analytics_service.modules.revenue_analytics import RevenueAnalytics

logger = logging.getLogger(__name__)

class TimeSeriesAnalytics:
    def __init__(self, df):
        self.df = df 
        self.results = {}
        self.revenue_analytics = RevenueAnalytics(df)

    #=======================================================
    # COLUMN DETECTION
    #=======================================================

    def _find_date_column(self):
        """Identify the date column in the dataset."""
        return self.revenue_analytics._ensure_date_column()
    
    #=======================================================
    # TIME SERIES ANALYTICS
    #=======================================================

    def _calculate_daily_metrics(self):
        """Calculate daily revenue and growth metrics."""
        try :
            date_col = self._find_date_column()
            if not date_col:
                logger.warning("No date column found. Cannot perform time series analysis.")
                return None
            
            self.df[date_col] = pd.to_datetime(self.df[date_col])

            revenue = self.revenue_analytics._get_revenue_series()

            # group by date and calculate daily revenue

            daily_data = self.df.groupby(date_col).agg({
                revenue.name: 'sum',
                self.df.column[0]: 'count'
            }).reset_index()

            daily_data.columns = ['date', 'revenue', 'order_count']
            daily_data['avg_order_value'] = daily_data['revenue'] / daily_data['order_count']
            daily_data = daily_data.sort_values('date')

            result = {
                'date_range': {
                        'start_date': daily_data[date_col].min().strftime('%Y-%m-%d'),
                        'end_date': daily_data[date_col].max().strftime('%Y-%m-%d'),
                        'total_days': len(daily_data)
                    },
                    'daily_statistics': {
                        'avg_daily_revenue': float(round(daily_data['revenue'].mean(), 2)),
                        'median_daily_revenue': float(round(daily_data['revenue'].median(), 2)),
                        'max_daily_revenue': float(round(daily_data['revenue'].max(), 2)),
                        'min_daily_revenue': float(round(daily_data['revenue'].min(), 2)),
                        'std_daily_revenue': float(round(daily_data['revenue'].std(), 2)),
                        'avg_daily_orders': float(round(daily_data['order_count'].mean(), 2)),
                        'avg_aov': float(round(daily_data['avg_order_value'].mean(), 2))
                    },
                    'top_sales_days': [
                        {
                            'date': row[date_col].strftime('%Y-%m-%d'),
                            'revenue': float(round(row['revenue'], 2)),
                            'order_count': int(row['order_count']),
                            'avg_order_value': float(round(row['avg_order_value'], 2))
                        }
                        for _, row in daily_data.nlargest(10, 'revenue').iterrows()
                    ]
            }
            logger.info(f"Daily metrics calculated : {len(daily_data)} days , avg daily revenue ${result['daily_statistics']['avg_daily_revenue']:.2f}")
            return result
        except Exception as e:
            logger.error(f"Error calculating daily metrics: {e}", exc_info=True)
            return None
        
    def _calculate_weekly_metrics(self):
        """Calculate weekly revenue and growth metrics."""
        logger.info("Calculating weekly metrics...")

        try:
            date_col = self._find_date_column()
            if not date_col:
                logger.warning("No date column found. Cannot perform time series analysis.")
                return None
            self.df[date_col] = pd.to_datetime(self.df[date_col])
            revenue = self.revenue_analytics._get_revenue_series()

            weekly_data = self.df.groupby(pd.Grouper(key=date_col, freq='W')).agg({
                revenue.name: 'sum',
                self.df.column[0]: 'count'
            }).reset_index()

            weekly_data.columns = [date_col  , 'revenue', 'order_count']
            weekly_data['avg_order_value'] = weekly_data['revenue'] / weekly_data['order_count']
            weekly_data = weekly_data[weekly_data['revenue'] > 0].sort_values(date_col)

            weekly_data['wow_growth_pct'] = weekly_data['revenue'].pct_change() * 100
            
            result = {
                'total_weeks': len(weekly_data),
                'weekly_statistics': {
                    'avg_weekly_revenue': float(round(weekly_data['revenue'].mean(), 2)),
                    'median_weekly_revenue': float(round(weekly_data['revenue'].median(), 2)),
                    'max_weekly_revenue': float(round(weekly_data['revenue'].max(), 2)),
                    'min_weekly_revenue': float(round(weekly_data['revenue'].min(), 2)),
                    'std_weekly_revenue': float(round(weekly_data['revenue'].std(), 2))
                },
                'growth_metrics': {
                    'avg_wow_growth': float(round(weekly_data['wow_growth_pct'].mean(), 2)),
                    'positive_growth_weeks': int((weekly_data['wow_growth_pct'] > 0).sum()),
                    'negative_growth_weeks': int((weekly_data['wow_growth_pct'] < 0).sum())
                },
                'top_weeks': [
                    {
                        'week_start': row[date_col].strftime('%Y-%m-%d'),
                        'revenue': float(round(row['revenue'], 2)),
                        'order_count': int(row['order_count']),
                        'wow_growth': float(round(row['wow_growth_pct'], 2)) if not pd.isna(row['wow_growth_pct']) else None
                    }
                    for _, row in weekly_data.nlargest(10, 'revenue').iterrows()
                ]
            }
            logger.info(f"Weekly metrics calculated : {len(weekly_data)} weeks , avg weekly revenue ${result['weekly_statistics']['avg_weekly_revenue']:.2f}")
            return result
        
        except Exception as e:
            logger.error("Calculating weekly metrics: {e}", exc_info=True)
            return None
        
    def _calculate_monthly_metrics(self):
        logger.info("Calculating monthly metrics....")

        try:
            date_col = self.revenue_analytics._find_date_column()
            if not date_col:
                logger.warning("No date column found. Cannot perform time series analysis.")
                return None
            self.df[date_col] = pd.to_datetime(self.df[date_col])

            revenue = self.revenue_analytics._get_revenue_series()

            monthly_data = self.df.groupby(pd.Grouper(key=date_col, freq='M')).agg({
                revenue.name: 'sum',
                self.df.column[0]: 'count'
            }).reset_index()

            monthly_data.columns = [date_col, 'revenue', 'order_count']
            monthly_data['avg_order_value'] = monthly_data['revenue'] / monthly_data['order_count']
            monthly_data = monthly_data[monthly_data['revenue'] > 0].sort_values(date_col)

            monthly_data['mom_growth_pct'] = monthly_data['revenue'].pct_change() * 100

            result = {
                'total_months': len(monthly_data),
                'monthly_statistics': {
                    'avg_monthly_revenue': float(round(monthly_data['revenue'].mean(), 2)),
                    'median_monthly_revenue': float(round(monthly_data['revenue'].median(), 2)),
                    'max_monthly_revenue': float(round(monthly_data['revenue'].max(), 2)),
                    'min_monthly_revenue': float(round(monthly_data['revenue'].min(), 2)),
                    'std_monthly_revenue': float(round(monthly_data['revenue'].std(), 2)),
                    'total_revenue': float(round(monthly_data['revenue'].sum(), 2))
                },
                'growth_metrics': {
                    'avg_mom_growth': float(round(monthly_data['mom_growth_pct'].mean(), 2)),
                    'positive_growth_months': int((monthly_data['mom_growth_pct'] > 0).sum()),
                    'negative_growth_months': int((monthly_data['mom_growth_pct'] < 0).sum())
                },
                'monthly_breakdown': [
                    {
                        'month': row[date_col].strftime('%Y-%m'),
                        'revenue': float(round(row['revenue'], 2)),
                        'order_count': int(row['order_count']),
                        'avg_order_value': float(round(row['avg_order_value'], 2)),
                        'mom_growth': float(round(row['mom_growth_pct'], 2)) if not pd.isna(row['mom_growth_pct']) else None
                    }
                    for _, row in monthly_data.iterrows()
                ]
            }
            logger.info(f"Monthly metrics calculated : {len(monthly_data)} months , avg monthly revenue ${result['monthly_statistics']['avg_monthly_revenue']:.2f}")
            return result
        
        except Exception as e:
            logger.error(f"Error calculating monthly metrics: {e}", exc_info=True)
            return None
        
    def _calculate_seasonality(self):
        """Detect seasonality patterns in the data."""
        logger.info("Calculating seasonality metrics...")
        
        try:
            date_col = self._find_date_column()
            if not date_col:
                logger.warning("No date column found. Cannot perform seasonality analysis.")
                return None
            self.df[date_col]= pd.to_datetime(self.df[date_col])
            revenue = self.revenue_analytics._get_revenue_series()
            
            #DAY OF WEEK ANALYSIS
            self.df['day_of_week'] = self.df[date_col].dt.day_name()
            dow_data = self.df.groupby('day_of_week').agg(['sum','count', 'mean'])
            # MONTH ANALYSIS
            self.df['month'] = self.df[date_col].dt.month 
            self.df['month_name'] = self.df[date_col].dt.month_name()
            month_data = self.df.groupby(['month','month_name']).agg(['sum','count', 'mean'])

            #DAY OF MONTH ANALYSIS
            self.df['day_of_month'] = self.df[date_col].dt.day
            dom_data = self.df.groupby('day_of_month').agg(['sum','count', 'mean'])

            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dow_data = dow_data.reindex(d for d in day_order if d in dow_data.index)

            result = {
                'day_of_week_seasonality': [
                    {
                        'day': day,
                        'total_revenue': float(round(dow_data.loc[day, 'sum'], 2)),
                        'avg_revenue': float(round(dow_data.loc[day, 'mean'], 2)),
                        'order_count': int(dow_data.loc[day, 'count'])
                    }
                    for day in dow_data.index
                ],
                'monthly_seasonality': [
                    {
                        'month_number': int(idx[0]),
                        'month_name': idx[1],
                        'total_revenue': float(round(month_data.loc[idx, 'sum'], 2)),
                        'avg_revenue': float(round(month_data.loc[idx, 'mean'], 2)),
                        'order_count': int(month_data.loc[idx, 'count'])
                    }
                    for idx in month_data.index
                ],
                'best_day_of_week': dow_data['sum'].idxmax(),
                'best_month': dict(month_data.loc[month_data['sum'].idxmax()].to_dict()),
                'worst_day_of_week': dow_data['sum'].idxmin(),
                'worst_month': dict(month_data.loc[month_data['sum'].idxmin()].to_dict())
            
            }
            logger.info("Seasonality metrics calculated successfully.")
            return result
        except Exception as e:
            logger.error(f"Error calculating seasonality metrics: {e}", exc_info=True)
            return None
        
    def _calculate_volatility(self):
        """Calculate revenue volatility and trend stability."""
        logger.info("Calculating volatility metrics...")

        try:
            date_col = self._find_date_column()
            if not date_col:
                logger.warning("No date column found. Cannot perform volatility analysis.")
                return None
            self.df[date_col] = pd.to_datetime(self.df[date_col])
            revenue = self.revenue_analytics._get_revenue_series()

            daily_revenue = self.df.groupby(date_col)[revenue.name].sum()

            # volatility metrics
            daily_returns = daily_revenue.pct_change().dropna()

            result = {
                'daily_volatility': {
                    'std_deviation': float(round(daily_revenue.std(), 2)),
                    'coefficient_of_variation': float(round(daily_revenue.std() / daily_revenue.mean() * 100, 2)),
                    'range': float(round(daily_revenue.max() - daily_revenue.min(), 2))
                },
                'return_volatility': {
                    'daily_return_std': float(round(daily_returns.std() * 100, 2)),
                    'daily_return_mean': float(round(daily_returns.mean() * 100, 2)),
                    'sharpe_ratio_proxy': float(round((daily_returns.mean() / daily_returns.std()) if daily_returns.std() > 0 else 0, 2))
                },
                'trend_stability': {
                    'stable_days': int((daily_returns.abs() < 0.1).sum()),  # Less than 10% change
                    'volatile_days': int((daily_returns.abs() >= 0.1).sum()),
                    'extreme_days': int((daily_returns.abs() >= 0.25).sum())  # More than 25% change
                }
            }
            logger.info("Volatility metrics calculated successfully.")
            return result
        except Exception as e:
            logger.error(f"Error calculating volatility metrics: {e}", exc_info=True)
            return None
    
    def _calculate_growth_trajectory(self):
         logger.info("Calculating growth trajectory...")

         try:
             date_col = self._find_date_column()
             if not date_col:
                 logger.warning("No date column found. Cannot perform growth trajectory analysis.")
                 return None
             
             self.df[date_col] = pd.to_datetime(self.df[date_col])
             revenue = self.revenue_analytics._get_revenue_series()

             # weekly revenue for growth trajectory
             weekly_revenue = self.df.groupby(pd.Grouper(key=date_col,freq='W'))[revenue.name].sum().reset_index()
             weekly_revenue.columns = [date_col,'revenue']
             weekly_revenue = weekly_revenue[weekly_revenue['revenue'] > 0].sort_values(date_col)

             if len(weekly_revenue) < 2:
                 logger.warning("Not enough data points for growth trajectory analysis.")
                 return None
             
             midpoint = len(weekly_revenue) // 2
             first_half = weekly_revenue.iloc[:midpoint]['revenue'].sum()
             second_half = weekly_revenue.iloc[midpoint:]['revenue'].sum()

             growth_rate = ((second_half - first_half) / first_half * 100) if first_half > 0 else None

             #linear regression for growth trajectory

             from scipy import stats
             x = np.arange(len(weekly_revenue))
             y = weekly_revenue['revenue'].values
             slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)

             # trend classification
             if slope > 0 :
                trend = "growing" if abs(r_value) > 0.5 else "fluctuating_upward"
             elif slope < 0 :
                 trend = "declining" if abs(r_value) > 0.5 else "fluctuating_downward"
             else:
                 trend = "stable"

             result = {
                 'overall_growth_rate': float(round(growth_rate, 2)) if growth_rate is not None else None,
                 'first_half_revenue': float(round(first_half, 2)),
                 'second_half_revenue': float(round(second_half, 2)),
                 'trend': trend,
                 'trend_strenght':float(round(abs(r_value),2)),
                 'weekly_slope':float(round(slope,2)),
                 'projected_next_week':float(round(slope * len(weekly_revenue) + intercept, 2))

             }
             logger.info("Growth trajectory calculated successfully.")
             return result
         except Exception as e:
                logger.error(f"Error calculating growth trajectory: {e}", exc_info=True)
                return None
    
    def analyze(self):
        """Execute complete time-series analysis."""

        logger.info("Starting comprehensive time-series analytics...")

        try:
            date_col = self._find_date_column()
            if not date_col:
                logger.warning("No date column found. Time-series analytics will be limited.")
                return None
            
            self.results = {
                'daily_metrics':self._calculate_daily_metrics(),
                'weekly_metrics': self._calculate_weekly_metrics(),
                'monthly_metrics': self._calculate_monthly_metrics(),
                'seasonality': self._calculate_seasonality(),
                'volatility': self._calculate_volatility(),
                'growth_trajectory': self._calculate_growth_trajectory()
            }

            logger.info("Time-series analytics completed successfully.")
            return self.results
        except Exception as e:
            logger.error(f"Error in comprehensive time-series analytics: {e}", exc_info=True)
            return {'error': str(e)}
        
    