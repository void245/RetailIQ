import logging
import pandas as pd 
from datetime import datetime, timedelta
from app.services.retail_analytics_service.modules.revenue_analytics import RevenueAnalytics

logger = logging.getLogger(__name__)

class RetailAnalyticsService :
    """ Main service for retail analytics - orchestrates different analyses"""

    def __init__(self, df, config=None):
        self.df = df 
        self.config = config or {}
        self.results = {}
        
        # initialize analysis modules
        self.revenue_analytics = RevenueAnalytics(df)