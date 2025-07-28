import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

class BacktestingEngine:
    def __init__(self, forecast_horizon=30, training_window=90):
        self.forecast_horizon = forecast_horizon
        self.training_window = training_window
    
    def walk_forward_validation(self, sales_data: pd.DataFrame, 
                               forecasting_model) -> Dict[str, float]:
        """Perform walk-forward validation"""
        results = []
        
        # Sort by date
        sales_data = sales_data.sort_values('created_at')
        start_date = sales_data['created_at'].min()
        end_date = sales_data['created_at'].max()
        
        # Create daily aggregated data
        daily_sales = sales_data.groupby([
            sales_data['created_at'].dt.date, 'product_id'
        ])['quantity'].sum().reset_index()
        
        current_date = start_date + timedelta(days=self.training_window)
        
        while current_date + timedelta(days=self.forecast_horizon) <= end_date:
            # Training period
            train_end = current_date
            train_start = train_end - timedelta(days=self.training_window)
            
            # Test period  
            test_start = current_date + timedelta(days=1)
            test_end = test_start + timedelta(days=self.forecast_horizon)
            
            # Get training data
            train_data = daily_sales[
                (daily_sales['created_at'] >= train_start) & 
                (daily_sales['created_at'] <= train_end)
            ]
            
            # Get test data (actual sales)
            test_data = daily_sales[
                (daily_sales['created_at'] >= test_start) & 
                (daily_sales['created_at'] <= test_end)
            ]
            
            # Make predictions for each product
            for product_id in train_data['product_id'].unique():
                product_train = train_data[train_data['product_id'] == product_id]
                product_test = test_data[test_data['product_id'] == product_id]
                
                if len(product_train) >= 7 and len(product_test) >= 7:  # Minimum data
                    # Generate forecast
                    train_series = product_train.set_index('created_at')['quantity']
                    predicted = forecasting_model.forecast(train_series, self.forecast_horizon)
                    
                    # Calculate actual
                    actual = product_test['quantity'].sum()
                    predicted_total = sum(predicted)
                    
                    results.append({
                        'product_id': product_id,
                        'test_start': test_start,
                        'actual': actual,
                        'predicted': predicted_total,
                        'error': abs(actual - predicted_total),
                        'percentage_error': abs(actual - predicted_total) / max(actual, 1) * 100
                    })
            
            # Move window forward
            current_date += timedelta(days=7)  # Weekly steps
        
        # Calculate aggregate metrics
        results_df = pd.DataFrame(results)
        
        if len(results_df) > 0:
            metrics = {
                'mae': results_df['error'].mean(),
                'mape': results_df['percentage_error'].mean(),
                'rmse': np.sqrt((results_df['error'] ** 2).mean()),
                'hit_rate': self._calculate_hit_rate(results_df),
                'bias': (results_df['predicted'] - results_df['actual']).mean(),
                'total_tests': len(results_df)
            }
        else:
            metrics = {'error': 'Insufficient data for backtesting'}
        
        return metrics
    
    def _calculate_hit_rate(self, results_df: pd.DataFrame) -> float:
        """Calculate directional accuracy (hit rate)"""
        # Compare predicted vs actual direction from previous period
        # This would need historical baseline for comparison
        correct_direction = 0
        total_comparisons = 0
        
        for product_id in results_df['product_id'].unique():
            product_results = results_df[results_df['product_id'] == product_id].sort_values('test_start')
            
            for i in range(1, len(product_results)):
                current = product_results.iloc[i]
                previous = product_results.iloc[i-1]
                
                actual_direction = current['actual'] - previous['actual']
                predicted_direction = current['predicted'] - previous['predicted']
                
                if (actual_direction >= 0 and predicted_direction >= 0) or \
                   (actual_direction < 0 and predicted_direction < 0):
                    correct_direction += 1
                
                total_comparisons += 1
        
        return correct_direction / max(total_comparisons, 1) * 100
