import streamlit as st
import numpy as np
from scipy import stats

class ServiceLevelOptimizer:
    def __init__(self, target_service_level=0.975):
        self.target_service_level = target_service_level
        self.z_score = stats.norm.ppf(target_service_level)
    
    def calculate_optimal_stock(self, daily_demand, demand_std, lead_time, 
                              holding_cost_per_unit=1.0, stockout_cost_per_unit=10.0):
        """Calculate optimal stock level using newsvendor model"""
        
        # Lead time demand statistics
        ltd_mean = daily_demand * lead_time
        ltd_std = demand_std * np.sqrt(lead_time)
        
        # Safety stock
        safety_stock = self.z_score * ltd_std
        
        # Optimal stock level
        optimal_stock = ltd_mean + safety_stock
        
        # Economic justification
        critical_ratio = stockout_cost_per_unit / (stockout_cost_per_unit + holding_cost_per_unit)
        economic_service_level = critical_ratio
        
        return {
            'optimal_stock_level': optimal_stock,
            'safety_stock': safety_stock,
            'service_level': self.target_service_level,
            'economic_service_level': economic_service_level,
            'expected_stockouts_per_cycle': ltd_std * stats.norm.pdf(self.z_score)
        }
