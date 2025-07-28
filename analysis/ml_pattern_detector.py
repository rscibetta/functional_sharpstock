import streamlit as st
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report

class MLPatternDetector:
    def __init__(self):
        self.trend_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.demand_clusterer = KMeans(n_clusters=5, random_state=42)
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def extract_features(self, sales_series: pd.Series) -> np.array:
        """Extract time series features for ML models"""
        if len(sales_series) < 14:
            return np.zeros(10)  # Return zeros for insufficient data
        
        features = []
        
        # Rolling statistics
        features.append(sales_series.mean())  # Average
        features.append(sales_series.std())   # Volatility
        features.append(sales_series.skew())  # Skewness
        features.append(sales_series.kurt())  # Kurtosis
        
        # Trend features
        x = np.arange(len(sales_series))
        slope = np.polyfit(x, sales_series.values, 1)[0]
        features.append(slope)  # Linear trend
        
        # Seasonality (weekly)
        if len(sales_series) >= 14:
            weekly_pattern = []
            for day in range(7):
                day_sales = sales_series.iloc[day::7]
                weekly_pattern.append(day_sales.mean() if len(day_sales) > 0 else 0)
            features.append(np.std(weekly_pattern))  # Weekly seasonality strength
        else:
            features.append(0)
        
        # Recent vs historical comparison
        mid_point = len(sales_series) // 2
        recent_avg = sales_series.iloc[mid_point:].mean()
        historical_avg = sales_series.iloc[:mid_point].mean()
        features.append(recent_avg / max(historical_avg, 1))  # Recent momentum
        
        # Additional statistical features
        features.append(len(sales_series[sales_series > 0]) / len(sales_series))  # Activity ratio
        features.append(sales_series.max() / max(sales_series.mean(), 1))  # Peak ratio
        features.append(np.percentile(sales_series, 75) - np.percentile(sales_series, 25))  # IQR
        
        return np.array(features)
    
    def train_trend_classifier(self, training_data: List[Tuple[pd.Series, str]]):
        """Train the trend classification model"""
        X = []
        y = []
        
        for sales_series, trend_label in training_data:
            features = self.extract_features(sales_series)
            X.append(features)
            y.append(trend_label)
        
        X = np.array(X)
        X_scaled = self.scaler.fit_transform(X)
        
        self.trend_classifier.fit(X_scaled, y)
        self.is_fitted = True
        
        return self.trend_classifier.score(X_scaled, y)
    
    def predict_trend(self, sales_series: pd.Series) -> Tuple[str, float]:
        """Predict trend classification and confidence"""
        if not self.is_fitted:
            return "Unknown", 0.0
        
        features = self.extract_features(sales_series).reshape(1, -1)
        features_scaled = self.scaler.transform(features)
        
        prediction = self.trend_classifier.predict(features_scaled)[0]
        confidence = np.max(self.trend_classifier.predict_proba(features_scaled))
        
        return prediction, confidence
    
    def cluster_demand_patterns(self, all_sales_data: Dict[int, pd.Series]) -> Dict[int, int]:
        """Cluster products by demand patterns"""
        features_matrix = []
        product_ids = []
        
        for product_id, sales_series in all_sales_data.items():
            features = self.extract_features(sales_series)
            features_matrix.append(features)
            product_ids.append(product_id)
        
        features_matrix = np.array(features_matrix)
        features_scaled = StandardScaler().fit_transform(features_matrix)
        
        clusters = self.demand_clusterer.fit_predict(features_scaled)
        
        return dict(zip(product_ids, clusters))
