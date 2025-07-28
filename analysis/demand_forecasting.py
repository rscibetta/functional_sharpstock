import streamlit as st
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.metrics import mean_absolute_error, mean_squared_error

class AdvancedDemandForecaster:
    def __init__(self):
        self.alpha = 0.3  # Level smoothing
        self.beta = 0.1   # Trend smoothing  
        self.gamma = 0.1  # Seasonal smoothing
        self.seasonality_period = 7  # Weekly seasonality
    
    def holt_winters_forecast(self, data, periods_ahead=30):
        """Triple exponential smoothing with trend and seasonality"""
        # Initialize components
        level = np.mean(data[:self.seasonality_period])
        trend = (np.mean(data[self.seasonality_period:2*self.seasonality_period]) - 
                np.mean(data[:self.seasonality_period])) / self.seasonality_period
        
        seasonal = []
        for i in range(self.seasonality_period):
            seasonal.append(data[i] / level)
        
        # Apply smoothing
        levels, trends, seasonals = [level], [trend], seasonal
        
        for i in range(len(data)):
            if i >= self.seasonality_period:
                level = (self.alpha * data[i] / seasonals[i]) + \
                       (1 - self.alpha) * (levels[-1] + trends[-1])
                trend = self.beta * (level - levels[-1]) + (1 - self.beta) * trends[-1]
                seasonal_val = self.gamma * (data[i] / level) + \
                              (1 - self.gamma) * seasonals[i]
                
                levels.append(level)
                trends.append(trend)
                seasonals.append(seasonal_val)
        
        # Generate forecasts
        forecasts = []
        for h in range(1, periods_ahead + 1):
            seasonal_idx = (len(seasonals) - self.seasonality_period + h - 1) % self.seasonality_period
            forecast = (levels[-1] + h * trends[-1]) * seasonals[seasonal_idx]
            forecasts.append(max(0, forecast))  # Ensure non-negative
        
        return forecasts
    
    def detect_outliers(self, data, threshold=2.5):
        """Statistical outlier detection using modified Z-score"""
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        modified_z_scores = 0.6745 * (data - median) / mad
        return np.abs(modified_z_scores) > threshold
