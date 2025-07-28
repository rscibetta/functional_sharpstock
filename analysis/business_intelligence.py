"""
Fixed Business Intelligence Engine - Daily Demand Column Issue
"""
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import logging
from models.data_models import UserProfile, ProductInsight, SeasonalInsight

logger = logging.getLogger(__name__)

class EnhancedBusinessIntelligenceEngine:
    """Enhanced BI engine with user-specific configurations - FIXED VERSION"""
    
    def __init__(self, user_profile: UserProfile, brand_lead_times: Dict[str, int]):
        self.user_profile = user_profile
        self.brand_lead_times = brand_lead_times
        self.default_lead_time = user_profile.default_lead_time if user_profile else 14
    
    def get_lead_time_for_brand(self, brand: str) -> int:
        """Get lead time for specific brand, fallback to default"""
        return self.brand_lead_times.get(brand, self.default_lead_time)
    
    def analyze_comprehensive_performance(
        self, 
        recent_orders_df: pd.DataFrame, 
        historical_orders_df: pd.DataFrame, 
        inventory_df: pd.DataFrame,
        cached_historical_df: pd.DataFrame = None
    ) -> Tuple[List[ProductInsight], List[SeasonalInsight], Dict]:
        """
        FIXED: Comprehensive analysis with proper daily_demand calculation
        """
        
        if recent_orders_df.empty and historical_orders_df.empty and (cached_historical_df is None or cached_historical_df.empty):
            return [], [], {}
        
        st.info("🧠 **Running Advanced Business Intelligence Analysis...**")
        
        with st.spinner("Analyzing trends and generating insights..."):
            
            try:
                # Step 1: Analyze recent performance
                recent_analysis = self._analyze_period_performance(recent_orders_df, "recent")
                
                # Step 2: Analyze historical baseline - FIXED to use cached data
                if cached_historical_df is not None and not cached_historical_df.empty:
                    st.info("📚 Using cached historical data for trend analysis...")
                    historical_analysis = self._analyze_period_performance(cached_historical_df, "historical")
                    seasonal_data = cached_historical_df
                else:
                    historical_analysis = self._analyze_period_performance(historical_orders_df, "historical")
                    seasonal_data = historical_orders_df
                
                # Step 3: Combine with inventory data
                inventory_analysis = self._analyze_inventory_status(inventory_df)
                
                # Step 4: Generate product insights
                product_insights = self._generate_product_insights(
                    recent_analysis, historical_analysis, inventory_analysis
                )
                
                # Step 5: Seasonal analysis
                seasonal_insights = self._analyze_seasonality(seasonal_data)
                
                # Step 6: Business summary metrics
                summary_metrics = self._calculate_summary_metrics(
                    recent_orders_df, seasonal_data, product_insights
                )
                
            except Exception as e:
                st.error(f"❌ Error in comprehensive analysis: {e}")
                logger.error(f"Comprehensive analysis failed: {e}")
                return [], [], {}
        
        return product_insights, seasonal_insights, summary_metrics
    
    def _analyze_period_performance(self, orders_df: pd.DataFrame, period_name: str) -> pd.DataFrame:
        """FIXED: Analyze performance for a specific time period with proper daily_demand calculation"""
        
        if orders_df.empty:
            return pd.DataFrame()
        
        try:
            # Group by product and calculate metrics
            analysis = orders_df.groupby('product_id').agg({
                'quantity': ['sum', 'count'],
                'total_value': 'sum',
                'created_at': ['min', 'max', 'count'],
                'Style Number': 'first',
                'Description': 'first',
                'vendor': 'first',
                'order_number': 'nunique'
            }).reset_index()
            
            # Flatten columns - FIXED column naming
            analysis.columns = [
                'product_id', 'total_qty', 'order_count', 'total_revenue', 
                'first_sale', 'last_sale', 'line_items', 'style_number', 
                'description', 'vendor', 'unique_orders'
            ]
            
            # FIXED: Calculate time-based metrics with proper error handling
            analysis['period_days'] = (analysis['last_sale'] - analysis['first_sale']).dt.days + 1
            analysis['period_days'] = analysis['period_days'].fillna(1).clip(lower=1)  # Ensure at least 1 day
            
            # FIXED: Calculate daily_demand properly
            analysis['daily_demand'] = analysis['total_qty'] / analysis['period_days']
            analysis['daily_revenue'] = analysis['total_revenue'] / analysis['period_days']
            
            # FIXED: Add forecasting with better error handling
            try:
                from analysis.demand_forecasting import AdvancedDemandForecaster
                forecaster = AdvancedDemandForecaster()
                
                # Initialize forecasting columns
                analysis['forecast_daily_demand'] = analysis['daily_demand']
                analysis['demand_volatility'] = 0.0
                
                for idx, row in analysis.iterrows():
                    try:
                        # Get time series data for this product
                        product_orders = orders_df[orders_df['product_id'] == row['product_id']]
                        if len(product_orders) >= 14:  # Minimum data requirement
                            daily_sales = product_orders.groupby(product_orders['created_at'].dt.date)['quantity'].sum()
                            if len(daily_sales) >= 7:  # Additional safety check
                                forecasts = forecaster.holt_winters_forecast(daily_sales.values, 30)
                                analysis.loc[idx, 'forecast_daily_demand'] = np.mean(forecasts) if forecasts else row['daily_demand']
                                analysis.loc[idx, 'demand_volatility'] = np.std(daily_sales.values) if len(daily_sales) > 1 else 0
                            else:
                                analysis.loc[idx, 'forecast_daily_demand'] = row['daily_demand']
                                analysis.loc[idx, 'demand_volatility'] = 0
                        else:
                            analysis.loc[idx, 'forecast_daily_demand'] = row['daily_demand']
                            analysis.loc[idx, 'demand_volatility'] = 0
                    except Exception as forecast_error:
                        # Fallback to basic calculation if forecasting fails
                        analysis.loc[idx, 'forecast_daily_demand'] = row['daily_demand']
                        analysis.loc[idx, 'demand_volatility'] = 0
                        logger.warning(f"Forecasting failed for product {row['product_id']}: {forecast_error}")
                        
            except ImportError:
                # Fallback if forecasting module not available
                analysis['forecast_daily_demand'] = analysis['daily_demand']
                analysis['demand_volatility'] = 0.0
                logger.warning("Advanced forecasting not available, using basic calculations")
            except Exception as e:
                # General forecasting error fallback
                analysis['forecast_daily_demand'] = analysis['daily_demand']
                analysis['demand_volatility'] = 0.0
                logger.error(f"Forecasting module error: {e}")
            
            # Add period identifier
            analysis['period'] = period_name
            
            # FIXED: Ensure all numeric columns are properly typed
            numeric_columns = ['total_qty', 'total_revenue', 'period_days', 'daily_demand', 
                             'daily_revenue', 'forecast_daily_demand', 'demand_volatility']
            
            for col in numeric_columns:
                if col in analysis.columns:
                    analysis[col] = pd.to_numeric(analysis[col], errors='coerce').fillna(0)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in period performance analysis: {e}")
            st.error(f"❌ Error analyzing {period_name} performance: {e}")
            return pd.DataFrame()
    
    def _analyze_inventory_status(self, inventory_df: pd.DataFrame) -> pd.DataFrame:
        """FIXED: Analyze current inventory status with error handling"""
        
        if inventory_df.empty:
            return pd.DataFrame()
        
        try:
            inventory_analysis = inventory_df.groupby('product_id').agg({
                'total_inventory': 'sum',
                'total_sold': 'sum',
                'style_number': 'first'
            }).reset_index()
            
            # FIXED: Calculate inventory metrics with safe division
            inventory_analysis['inventory_turnover'] = np.where(
                inventory_analysis['total_inventory'] > 0,
                inventory_analysis['total_sold'] / inventory_analysis['total_inventory'],
                0
            )
            
            return inventory_analysis
            
        except Exception as e:
            logger.error(f"Error in inventory analysis: {e}")
            st.error(f"❌ Error analyzing inventory: {e}")
            return pd.DataFrame()
    
    def _generate_product_insights(
        self, 
        recent_df: pd.DataFrame, 
        historical_df: pd.DataFrame, 
        inventory_df: pd.DataFrame
    ) -> List[ProductInsight]:
        """FIXED: Generate comprehensive product insights with proper error handling"""
        
        insights = []
        
        try:
            # Merge recent and historical data
            if not recent_df.empty and not historical_df.empty:
                # Products with both recent and historical data
                combined = recent_df.merge(
                    historical_df, 
                    on='product_id', 
                    how='outer', 
                    suffixes=('_recent', '_historical')
                )
            elif not recent_df.empty:
                # Only recent data
                combined = recent_df.copy()
                combined.columns = [col + '_recent' if col != 'product_id' else col for col in combined.columns]
            elif not historical_df.empty:
                # Only historical data  
                combined = historical_df.copy()
                combined.columns = [col + '_historical' if col != 'product_id' else col for col in combined.columns]
            else:
                return insights
            
            # Merge with inventory
            if not inventory_df.empty:
                combined = combined.merge(inventory_df, on='product_id', how='left')
            
            # Generate insights for each product
            for _, row in combined.iterrows():
                try:
                    insight = self._create_product_insight(row)
                    if insight:
                        insights.append(insight)
                except Exception as e:
                    logger.error(f"Error creating insight for product {row.get('product_id')}: {e}")
                    continue
            
            # Sort by priority and performance
            insights.sort(key=lambda x: (
                {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}[x.reorder_priority],
                x.recent_daily_demand
            ), reverse=True)
            
        except Exception as e:
            logger.error(f"Error generating product insights: {e}")
            st.error(f"❌ Error generating insights: {e}")
        
        return insights
    
    def _create_product_insight(self, row) -> Optional[ProductInsight]:
        """FIXED: Create individual product insight with pending orders support"""
        
        try:
            product_id = row.get('product_id')
            if pd.isna(product_id):
                return None
            
            # FIXED: Better NaN handling with explicit fillna and safe conversions
            recent_daily = float(row.get('daily_demand_recent', 0) or 0)
            recent_total = int(row.get('total_qty_recent', 0) or 0)
            recent_revenue = float(row.get('total_revenue_recent', 0) or 0)
            recent_days = int(row.get('period_days_recent', 1) or 1)
            
            historical_daily = float(row.get('daily_demand_historical', 0) or 0)
            historical_total = int(row.get('total_qty_historical', 0) or 0)
            historical_revenue = float(row.get('total_revenue_historical', 0) or 0)
            historical_days = int(row.get('period_days_historical', 1) or 1)
            
            current_inventory = int(row.get('total_inventory', 0) or 0)
            inventory_turnover = float(row.get('inventory_turnover', 0) or 0)
            
            # FIXED: Better string handling with explicit conversion and fallbacks
            style_number = str(row.get('style_number_recent') or row.get('style_number_historical') or row.get('style_number') or 'Unknown')
            if style_number in ['nan', 'None', 'null']:
                style_number = f'Product_{int(product_id)}'
            
            description = str(row.get('description_recent') or row.get('description_historical') or row.get('description') or 'No description')
            if description in ['nan', 'None', 'null']:
                description = 'No description'
            
            vendor = str(row.get('vendor_recent') or row.get('vendor_historical') or row.get('vendor') or 'Unknown')
            if vendor in ['nan', 'None', 'null']:
                vendor = 'Unknown'
            
            # Calculate velocity change
            if historical_daily > 0 and recent_daily > 0:
                velocity_change = ((recent_daily - historical_daily) / historical_daily) * 100
            else:
                velocity_change = 0
            
            # ENHANCED TREND CLASSIFICATION with volume filters
            MIN_RECENT_TOTAL_SALES = 3
            MIN_DAILY_DEMAND = 0.1
            MIN_HISTORICAL_SALES = 2
            
            if recent_total < MIN_RECENT_TOTAL_SALES:
                if historical_total == 0:
                    trend_classification = 'New Product'
                    trend_strength = 'Low Volume'
                elif recent_total == 0:
                    trend_classification = 'No Recent Sales'
                    trend_strength = 'Inactive'
                else:
                    trend_classification = 'Low Volume'
                    trend_strength = 'Insufficient Data'
            elif recent_daily < MIN_DAILY_DEMAND:
                trend_classification = 'Slow Moving'
                trend_strength = 'Low Volume'
            elif historical_total < MIN_HISTORICAL_SALES:
                if recent_daily >= 1.0:
                    trend_classification = 'New Strong Seller'
                    trend_strength = 'Emerging'
                elif recent_daily >= 0.5:
                    trend_classification = 'New Moderate Seller'
                    trend_strength = 'Emerging'
                else:
                    trend_classification = 'New Product'
                    trend_strength = 'Limited Data'
            else:
                # Products with sufficient volume for trend analysis
                if velocity_change > 50 and recent_daily >= 0.5:
                    trend_classification = 'Trending Up'
                    trend_strength = 'Strong'
                elif velocity_change > 20 and recent_daily >= 0.3:
                    trend_classification = 'Trending Up'
                    trend_strength = 'Moderate'
                elif velocity_change > 5 and recent_daily >= 0.2:
                    trend_classification = 'Growing'
                    trend_strength = 'Weak'
                elif velocity_change > -5:
                    if recent_daily >= 1.0:
                        trend_classification = 'Hot Seller'
                        trend_strength = 'Stable'
                    elif recent_daily >= 0.5:
                        trend_classification = 'Steady Seller'
                        trend_strength = 'Stable'
                    else:
                        trend_classification = 'Stable'
                        trend_strength = 'Low Volume'
                elif velocity_change > -20:
                    trend_classification = 'Declining'
                    trend_strength = 'Weak'
                else:
                    trend_classification = 'Declining'
                    trend_strength = 'Strong'
            
            # Inventory calculations
            days_until_stockout = int(current_inventory / recent_daily) if recent_daily > 0 else 999
            
            # NEW: Check if pending orders are included in analysis
            analysis_includes_pending = getattr(st.session_state, 'analysis_includes_pending', False)
            
            # NEW: Calculate pending inventory for this product if available
            pending_inventory = 0
            if analysis_includes_pending:
                pending_inventory = self._calculate_pending_inventory_for_product(style_number)
            
            # Calculate reorder recommendation - USE PENDING-AWARE METHOD IF PENDING ORDERS EXIST
            if pending_inventory > 0:
                reorder_priority, recommended_qty, reorder_timing, reasoning = self._calculate_reorder_recommendation_with_pending(
                    trend_classification, recent_daily, recent_total, current_inventory, 
                    pending_inventory, days_until_stockout, velocity_change, historical_daily, vendor
                )
            else:
                reorder_priority, recommended_qty, reorder_timing, reasoning = self._calculate_reorder_recommendation_improved(
                    trend_classification, recent_daily, recent_total, current_inventory, 
                    days_until_stockout, velocity_change, historical_daily, vendor
                )
            
            return ProductInsight(
                product_id=int(product_id),
                style_number=style_number,
                description=description,
                vendor=vendor,
                recent_daily_demand=float(recent_daily),
                recent_total_sales=int(recent_total),
                recent_revenue=float(recent_revenue),
                recent_days=int(recent_days),
                historical_daily_demand=float(historical_daily),
                historical_total_sales=int(historical_total),
                historical_revenue=float(historical_revenue),
                historical_days=int(historical_days),
                trend_classification=trend_classification,
                velocity_change=float(velocity_change),
                trend_strength=trend_strength,
                current_inventory=int(current_inventory),
                days_until_stockout=int(days_until_stockout),
                inventory_turnover=float(inventory_turnover),
                reorder_priority=reorder_priority,
                recommended_qty=int(recommended_qty),
                reorder_timing=reorder_timing,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Failed to create insight for product {row.get('product_id', 'unknown')}: {e}")
            return None

    def _calculate_pending_inventory_for_product(self, style_number: str) -> int:
        """Calculate total pending inventory for a specific product style"""
        
        try:
            # Get pending orders from session state
            pending_orders_data = st.session_state.get('pending_orders', [])
            
            if not pending_orders_data:
                return 0
            
            total_pending = 0
            
            for order_data in pending_orders_data:
                if str(order_data.get('style_number', '')) == str(style_number):
                    quantity = int(order_data.get('quantity', 0))
                    total_pending += quantity
            
            return total_pending
            
        except Exception as e:
            logger.warning(f"Error calculating pending inventory for {style_number}: {e}")
            return 0

    def _calculate_reorder_recommendation_improved(
        self, 
        trend_classification: str, 
        daily_demand: float, 
        total_recent_sales: int,
        current_inventory: int, 
        days_until_stockout: int, 
        velocity_change: float,
        historical_daily: float,
        brand: str = "Unknown"
    ) -> Tuple[str, int, str, str]:
        """FIXED: Calculate smart reorder recommendations with brand-specific lead times"""
        
        try:
            # Use brand-specific lead time
            lead_time = self.get_lead_time_for_brand(brand)
            
            # Use service level optimizer if available
            try:
                from analysis.service_level_optimizer import ServiceLevelOptimizer
                optimizer = ServiceLevelOptimizer()
                optimal_data = optimizer.calculate_optimal_stock(
                    daily_demand=daily_demand,
                    demand_std=historical_daily * 0.3 if historical_daily > 0 else daily_demand * 0.5,
                    lead_time=lead_time,
                    holding_cost_per_unit=1.0,
                    stockout_cost_per_unit=10.0
                )
                base_qty = optimal_data['optimal_stock_level']
            except (ImportError, Exception):
                # Fallback calculation if optimizer not available
                base_qty = max(1, daily_demand * lead_time * 1.5)  # 1.5x lead time demand
            
            # Volume-based adjustments
            if total_recent_sales < 3:
                multiplier = 0.5
                volume_note = "Low recent sales volume. "
            elif daily_demand < 0.1:
                multiplier = 0.3
                volume_note = "Very slow moving item. "
            elif trend_classification in ['Trending Up', 'Hot Seller'] and daily_demand >= 0.5:
                if velocity_change > 50:
                    multiplier = 1.8
                elif velocity_change > 20:
                    multiplier = 1.5
                else:
                    multiplier = 1.3
                volume_note = ""
            elif trend_classification in ['Declining'] and daily_demand >= 0.2:
                if velocity_change < -30:
                    multiplier = 0.4
                else:
                    multiplier = 0.6
                volume_note = ""
            elif trend_classification in ['New Strong Seller', 'New Moderate Seller']:
                multiplier = 1.2
                volume_note = "New product with promising sales. "
            else:
                multiplier = 1.0
                volume_note = ""
            
            recommended_qty = max(1, int(base_qty * multiplier))
            
            # Brand-specific lead time note
            brand_note = f"Lead time for {brand}: {lead_time} days. " if brand != "Unknown" else f"Default lead time: {lead_time} days. "
            
            # Determine priority and timing with volume considerations
            if total_recent_sales < 2:
                priority = 'LOW'
                timing = 'Monitor'
                reasoning = f"{volume_note}{brand_note}Only {total_recent_sales} recent sales. Monitor before reordering."
            elif days_until_stockout <= lead_time:
                if trend_classification in ['Trending Up', 'Hot Seller', 'New Strong Seller'] and daily_demand >= 0.3:
                    priority = 'CRITICAL'
                    timing = 'Order Now'
                    reasoning = f"{volume_note}{brand_note}Will stock out in {days_until_stockout} days. {trend_classification} with {daily_demand:.1f} daily demand."
                elif daily_demand >= 0.1:
                    priority = 'HIGH'
                    timing = 'Order Now'
                    reasoning = f"{volume_note}{brand_note}Will stock out in {days_until_stockout} days. Reorder needed."
                else:
                    priority = 'MEDIUM'
                    timing = 'Order This Week'
                    reasoning = f"{volume_note}{brand_note}Low demand ({daily_demand:.2f}/day) but stockout in {days_until_stockout} days."
            elif days_until_stockout <= lead_time * 2:
                if trend_classification in ['Trending Up', 'Hot Seller'] and daily_demand >= 0.5:
                    priority = 'HIGH'
                    timing = 'Order This Week'
                    reasoning = f"{volume_note}{brand_note}{trend_classification} with {days_until_stockout} days inventory. Strong sales justify proactive restock."
                elif daily_demand >= 0.2:
                    priority = 'MEDIUM'
                    timing = 'Order This Week'
                    reasoning = f"{volume_note}{brand_note}{days_until_stockout} days inventory remaining. Plan reorder soon."
                else:
                    priority = 'LOW'
                    timing = 'Monitor'
                    reasoning = f"{volume_note}{brand_note}Low demand product. {days_until_stockout} days inventory sufficient."
            elif trend_classification == 'Trending Up' and velocity_change > 30 and daily_demand >= 0.5:
                priority = 'MEDIUM'
                timing = 'Monitor'
                reasoning = f"{volume_note}{brand_note}Strong upward trend (+{velocity_change:.0f}%) with solid volume. Consider increasing stock levels."
            elif trend_classification in ['Declining'] and velocity_change < -20 and daily_demand >= 0.1:
                priority = 'LOW'
                timing = 'No Action'
                reasoning = f"{volume_note}{brand_note}Declining sales (-{abs(velocity_change):.0f}%). Reduce future orders."
            elif trend_classification in ['Low Volume', 'Slow Moving']:
                priority = 'LOW'
                timing = 'Monitor'
                reasoning = f"{volume_note}{brand_note}Low volume product. Current stock sufficient."
            else:
                priority = 'LOW'
                timing = 'Monitor'
                reasoning = f"{volume_note}{brand_note}{trend_classification}. Current stock sufficient for {days_until_stockout} days."
            
            return priority, max(1, recommended_qty), timing, reasoning
            
        except Exception as e:
            logger.error(f"Error calculating reorder recommendation: {e}")
            return 'LOW', 1, 'Monitor', f"Error in calculation: {str(e)}"
    
    def _analyze_seasonality(self, historical_orders_df: pd.DataFrame) -> List[SeasonalInsight]:
        """FIXED: Analyze seasonal patterns with proper error handling"""
        
        if historical_orders_df is None or historical_orders_df.empty:
            return []
        
        try:
            # Create a copy to avoid modifying original data
            df_copy = historical_orders_df.copy()
            
            # Ensure created_at is datetime
            if not pd.api.types.is_datetime64_any_dtype(df_copy['created_at']):
                df_copy['created_at'] = pd.to_datetime(df_copy['created_at'])
            
            # Remove any rows with invalid dates
            df_copy = df_copy.dropna(subset=['created_at'])
            
            if df_copy.empty or 'quantity' not in df_copy.columns:
                return []
            
            # Add month column
            df_copy['month'] = df_copy['created_at'].dt.month
            
            # Calculate monthly metrics
            monthly_stats = df_copy.groupby('month').agg({
                'quantity': 'sum',
                'created_at': 'count'
            }).reset_index()
            
            # Only proceed if we have data for multiple months
            if len(monthly_stats) < 2:
                return []
            
            # Calculate daily averages per month
            days_per_month = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 
                            7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
            
            monthly_stats['avg_daily_demand'] = monthly_stats['quantity'] / monthly_stats['month'].map(days_per_month)
            
            # Calculate seasonal multipliers
            overall_avg = monthly_stats['avg_daily_demand'].mean()
            if overall_avg > 0:
                monthly_stats['seasonal_multiplier'] = monthly_stats['avg_daily_demand'] / overall_avg
            else:
                monthly_stats['seasonal_multiplier'] = 1.0
            
            # Generate seasonal insights
            seasonal_insights = []
            month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 
                          5: 'May', 6: 'June', 7: 'July', 8: 'August', 
                          9: 'September', 10: 'October', 11: 'November', 12: 'December'}
            
            for _, row in monthly_stats.iterrows():
                month = row['month']
                
                # Get seasonally elevated products for this month
                elevated_products = []
                
                # Calculate product elevation if we have proper data
                if 'Style Number' in df_copy.columns and 'Description' in df_copy.columns:
                    month_data = df_copy[df_copy['month'] == month]
                    month_data_clean = month_data[
                        month_data['Style Number'].notna() & 
                        (month_data['Style Number'] != '') &
                        month_data['Description'].notna() & 
                        (month_data['Description'] != '')
                    ]
                    
                    if not month_data_clean.empty:
                        # Get top products for this month
                        month_products = month_data_clean.groupby(['Style Number', 'Description', 'product_id']).agg({
                            'quantity': 'sum'
                        }).reset_index().sort_values('quantity', ascending=False).head(5)
                        
                        for _, product_row in month_products.iterrows():
                            elevated_products.append({
                                'style_number': str(product_row['Style Number']),
                                'description': str(product_row['Description'])[:50] + "..." if len(str(product_row['Description'])) > 50 else str(product_row['Description']),
                                'product_id': int(product_row['product_id']),
                                'quantity': int(product_row['quantity']),
                                'seasonal_elevation': 1.5,  # Simplified for now
                                'daily_avg_month': float(product_row['quantity'] / days_per_month[month]),
                                'daily_avg_overall': float(product_row['quantity'] / 365)  # Simplified
                            })
                
                insight = SeasonalInsight(
                    month=month,
                    month_name=month_names[month],
                    avg_daily_demand=float(row['avg_daily_demand']),
                    peak_products=elevated_products,
                    seasonal_multiplier=float(row['seasonal_multiplier'])
                )
                seasonal_insights.append(insight)
            
            return seasonal_insights
            
        except Exception as e:
            logger.error(f"Seasonality analysis failed: {e}")
            st.error(f"❌ Error in seasonal analysis: {e}")
            return []
    
    def _calculate_summary_metrics(
        self, 
        recent_orders_df: pd.DataFrame, 
        historical_orders_df: pd.DataFrame, 
        insights: List[ProductInsight]
    ) -> Dict:
        """FIXED: Calculate high-level business metrics with error handling"""
        
        summary = {
            'recent_period_days': 0,
            'historical_period_days': 0,
            'total_recent_revenue': 0,
            'total_historical_revenue': 0,
            'revenue_growth_rate': 0,
            'trending_up_count': 0,
            'declining_count': 0,
            'critical_reorders': 0,
            'high_priority_reorders': 0,
            'avg_days_until_stockout': 0,
            'inventory_at_risk': 0
        }
        
        try:
            # Recent period metrics
            if not recent_orders_df.empty and 'created_at' in recent_orders_df.columns:
                recent_days = (recent_orders_df['created_at'].max() - recent_orders_df['created_at'].min()).days + 1
                summary['recent_period_days'] = recent_days
                if 'total_value' in recent_orders_df.columns:
                    summary['total_recent_revenue'] = recent_orders_df['total_value'].sum()
            
            # Historical period metrics
            if not historical_orders_df.empty and 'created_at' in historical_orders_df.columns:
                historical_days = (historical_orders_df['created_at'].max() - historical_orders_df['created_at'].min()).days + 1
                summary['historical_period_days'] = historical_days
                if 'total_value' in historical_orders_df.columns:
                    summary['total_historical_revenue'] = historical_orders_df['total_value'].sum()
            
            # Revenue growth rate (annualized)
            if summary['total_historical_revenue'] > 0 and summary['recent_period_days'] > 0:
                recent_daily_revenue = summary['total_recent_revenue'] / summary['recent_period_days']
                historical_daily_revenue = summary['total_historical_revenue'] / summary['historical_period_days']
                if historical_daily_revenue > 0:
                    summary['revenue_growth_rate'] = ((recent_daily_revenue - historical_daily_revenue) / historical_daily_revenue) * 100
            
            # Insights summary
            if insights:
                summary['trending_up_count'] = len([i for i in insights if 'Trending Up' in i.trend_classification])
                summary['declining_count'] = len([i for i in insights if 'Declining' in i.trend_classification])
                summary['critical_reorders'] = len([i for i in insights if i.reorder_priority == 'CRITICAL'])
                summary['high_priority_reorders'] = len([i for i in insights if i.reorder_priority == 'HIGH'])
                
                stockout_days = [i.days_until_stockout for i in insights if i.days_until_stockout < 999]
                summary['avg_days_until_stockout'] = sum(stockout_days) / len(stockout_days) if stockout_days else 999
                summary['inventory_at_risk'] = len([i for i in insights if i.days_until_stockout <= 30])
        
        except Exception as e:
            logger.error(f"Summary metrics calculation failed: {e}")
            st.error(f"❌ Error calculating summary metrics: {e}")
        
        return summary
    
    def _calculate_reorder_recommendation_with_pending(
        self, 
        trend_classification: str, 
        daily_demand: float, 
        total_recent_sales: int,
        current_inventory: int, 
        pending_inventory: int,  # NEW: Expected inventory from pending orders
        days_until_stockout: int, 
        velocity_change: float,
        historical_daily: float,
        brand: str = "Unknown"
    ) -> Tuple[str, int, str, str]:
        """ENHANCED: Calculate smart reorder recommendations accounting for pending orders"""
        
        try:
            # Use brand-specific lead time
            lead_time = self.get_lead_time_for_brand(brand)
            
            # Calculate projected inventory (current + pending)
            projected_inventory = current_inventory + pending_inventory
            projected_days_until_stockout = int(projected_inventory / daily_demand) if daily_demand > 0 else 999
            
            # Use service level optimizer if available
            try:
                from analysis.service_level_optimizer import ServiceLevelOptimizer
                optimizer = ServiceLevelOptimizer()
                optimal_data = optimizer.calculate_optimal_stock(
                    daily_demand=daily_demand,
                    demand_std=historical_daily * 0.3 if historical_daily > 0 else daily_demand * 0.5,
                    lead_time=lead_time,
                    holding_cost_per_unit=1.0,
                    stockout_cost_per_unit=10.0
                )
                base_qty = max(0, optimal_data['optimal_stock_level'] - pending_inventory)  # Reduce by pending
            except (ImportError, Exception):
                # Fallback calculation accounting for pending orders
                target_inventory = max(1, daily_demand * lead_time * 1.5)
                base_qty = max(0, target_inventory - pending_inventory)
            
            # Volume-based adjustments
            if total_recent_sales < 3:
                multiplier = 0.5
                volume_note = "Low recent sales volume. "
            elif daily_demand < 0.1:
                multiplier = 0.3 if pending_inventory == 0 else 0.1  # Reduce further if pending orders exist
                volume_note = "Very slow moving item. "
            elif trend_classification in ['Trending Up', 'Hot Seller'] and daily_demand >= 0.5:
                if velocity_change > 50:
                    multiplier = 1.8 if pending_inventory < daily_demand * 30 else 1.2  # Consider pending stock
                elif velocity_change > 20:
                    multiplier = 1.5 if pending_inventory < daily_demand * 20 else 1.0
                else:
                    multiplier = 1.3 if pending_inventory < daily_demand * 15 else 0.8
                volume_note = ""
            elif trend_classification in ['Declining'] and daily_demand >= 0.2:
                if velocity_change < -30:
                    multiplier = 0.2 if pending_inventory > 0 else 0.4  # Much lower if pending orders exist
                else:
                    multiplier = 0.4 if pending_inventory > 0 else 0.6
                volume_note = ""
            elif trend_classification in ['New Strong Seller', 'New Moderate Seller']:
                multiplier = 1.2 if pending_inventory < daily_demand * 10 else 0.6
                volume_note = "New product with promising sales. "
            else:
                multiplier = 1.0 if pending_inventory == 0 else 0.5
                volume_note = ""
            
            recommended_qty = max(0, int(base_qty * multiplier))  # Can be 0 if pending orders cover needs
            
            # Enhanced notes about pending orders
            pending_note = ""
            if pending_inventory > 0:
                pending_note = f"Pending orders: {pending_inventory} units. "
                if projected_days_until_stockout > days_until_stockout:
                    pending_note += f"Projected stock after pending: {projected_days_until_stockout} days. "
            
            brand_note = f"Lead time for {brand}: {lead_time} days. " if brand != "Unknown" else f"Default lead time: {lead_time} days. "
            
            # Determine priority and timing accounting for pending orders
            if total_recent_sales < 2:
                priority = 'LOW'
                timing = 'Monitor'
                reasoning = f"{volume_note}{pending_note}{brand_note}Only {total_recent_sales} recent sales. Monitor before reordering."
            elif projected_days_until_stockout <= lead_time:  # Use projected stockout time
                if trend_classification in ['Trending Up', 'Hot Seller', 'New Strong Seller'] and daily_demand >= 0.3:
                    priority = 'HIGH' if pending_inventory > 0 else 'CRITICAL'  # Lower priority if pending orders exist
                    timing = 'Order This Week' if pending_inventory > 0 else 'Order Now'
                    reasoning = f"{volume_note}{pending_note}{brand_note}Will stock out in {projected_days_until_stockout} days (including pending). {trend_classification} with {daily_demand:.1f} daily demand."
                elif daily_demand >= 0.1:
                    priority = 'MEDIUM' if pending_inventory > 0 else 'HIGH'
                    timing = 'Order This Week' if pending_inventory > 0 else 'Order Now'
                    reasoning = f"{volume_note}{pending_note}{brand_note}Will stock out in {projected_days_until_stockout} days (including pending). Reorder needed."
                else:
                    priority = 'LOW' if pending_inventory > 0 else 'MEDIUM'
                    timing = 'Monitor' if pending_inventory > 0 else 'Order This Week'
                    reasoning = f"{volume_note}{pending_note}{brand_note}Low demand ({daily_demand:.2f}/day) but stockout in {projected_days_until_stockout} days."
            elif pending_inventory > daily_demand * lead_time:
                # Sufficient pending inventory
                priority = 'LOW'
                timing = 'No Action'
                reasoning = f"{volume_note}{pending_note}{brand_note}Pending orders sufficient to cover {int(pending_inventory/daily_demand)} days demand."
            elif projected_days_until_stockout <= lead_time * 2:
                if trend_classification in ['Trending Up', 'Hot Seller'] and daily_demand >= 0.5:
                    priority = 'MEDIUM' if pending_inventory > 0 else 'HIGH'
                    timing = 'Monitor' if pending_inventory > daily_demand * 10 else 'Order This Week'
                    reasoning = f"{volume_note}{pending_note}{brand_note}{trend_classification} with {projected_days_until_stockout} days projected inventory. {'Monitor pending orders arrival.' if pending_inventory > 0 else 'Strong sales justify proactive restock.'}"
                elif daily_demand >= 0.2:
                    priority = 'LOW' if pending_inventory > daily_demand * 7 else 'MEDIUM'
                    timing = 'Monitor' if pending_inventory > daily_demand * 7 else 'Order This Week'
                    reasoning = f"{volume_note}{pending_note}{brand_note}{projected_days_until_stockout} days projected inventory remaining. {'Pending orders should help.' if pending_inventory > 0 else 'Plan reorder soon.'}"
                else:
                    priority = 'LOW'
                    timing = 'Monitor'
                    reasoning = f"{volume_note}{pending_note}{brand_note}Low demand product. {projected_days_until_stockout} days projected inventory sufficient."
            else:
                # Sufficient inventory even without pending orders
                priority = 'LOW'
                timing = 'Monitor' if recommended_qty > 0 else 'No Action'
                reasoning = f"{volume_note}{pending_note}{brand_note}Sufficient inventory. {'Consider reducing future orders.' if pending_inventory > daily_demand * 45 else 'Current levels appropriate.'}"
            
            return priority, max(0, recommended_qty), timing, reasoning
            
        except Exception as e:
            logger.error(f"Error calculating reorder recommendation with pending orders: {e}")
            return 'LOW', 0, 'Monitor', f"Error in calculation (with pending orders): {str(e)}"