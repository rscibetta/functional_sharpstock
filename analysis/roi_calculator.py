import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class ROICalculator:
    def __init__(self, holding_cost_rate=0.25, gross_margin_rate=0.40):
        self.holding_cost_rate = holding_cost_rate  # Annual holding cost as % of value
        self.gross_margin_rate = gross_margin_rate  # Gross margin %
        self.daily_holding_rate = holding_cost_rate / 365
    
    def calculate_inventory_optimization_savings(self, 
                                               baseline_inventory: Dict[str, float],
                                               optimized_inventory: Dict[str, float],
                                               unit_costs: Dict[str, float]) -> Dict:
        """Calculate savings from inventory optimization"""
        
        total_baseline_value = 0
        total_optimized_value = 0
        savings_by_product = {}
        
        for product_id in baseline_inventory.keys():
            baseline_units = baseline_inventory.get(product_id, 0)
            optimized_units = optimized_inventory.get(product_id, 0)
            unit_cost = unit_costs.get(product_id, 0)
            
            baseline_value = baseline_units * unit_cost
            optimized_value = optimized_units * unit_cost
            
            total_baseline_value += baseline_value
            total_optimized_value += optimized_value
            
            # Daily savings for this product
            inventory_reduction = baseline_value - optimized_value
            daily_savings = inventory_reduction * self.daily_holding_rate
            annual_savings = daily_savings * 365
            
            savings_by_product[product_id] = {
                'inventory_reduction_units': baseline_units - optimized_units,
                'inventory_reduction_value': inventory_reduction,
                'annual_holding_savings': annual_savings
            }
        
        total_inventory_reduction = total_baseline_value - total_optimized_value
        total_annual_savings = total_inventory_reduction * self.holding_cost_rate
        
        return {
            'total_inventory_reduction_value': total_inventory_reduction,
            'total_annual_holding_savings': total_annual_savings,
            'savings_by_product': savings_by_product,
            'roi_percentage': (total_annual_savings / max(total_baseline_value, 1)) * 100
        }
    
    def calculate_stockout_prevention_savings(self,
                                           prevented_stockouts: Dict[str, int],
                                           unit_selling_prices: Dict[str, float]) -> Dict:
        """Calculate savings from preventing stockouts"""
        
        total_prevented_revenue = 0
        total_gross_margin_saved = 0
        savings_by_product = {}
        
        for product_id, units_prevented in prevented_stockouts.items():
            selling_price = unit_selling_prices.get(product_id, 0)
            revenue_saved = units_prevented * selling_price
            gross_margin_saved = revenue_saved * self.gross_margin_rate
            
            total_prevented_revenue += revenue_saved
            total_gross_margin_saved += gross_margin_saved
            
            savings_by_product[product_id] = {
                'units_prevented': units_prevented,
                'revenue_saved': revenue_saved,
                'gross_margin_saved': gross_margin_saved
            }
        
        return {
            'total_revenue_saved': total_prevented_revenue,
            'total_gross_margin_saved': total_gross_margin_saved,
            'savings_by_product': savings_by_product
        }
    
    def calculate_forecast_accuracy_value(self,
                                        baseline_mape: float,
                                        improved_mape: float,
                                        annual_revenue: float) -> Dict:
        """Calculate value of improved forecast accuracy"""
        
        # Research shows 1% MAPE improvement = 0.5-1% cost reduction
        mape_improvement = baseline_mape - improved_mape
        cost_reduction_factor = 0.007  # Conservative 0.7% cost reduction per 1% MAPE improvement
        
        annual_cost_savings = annual_revenue * mape_improvement * cost_reduction_factor
        
        return {
            'mape_improvement': mape_improvement,
            'annual_cost_savings': annual_cost_savings,
            'cost_reduction_percentage': mape_improvement * cost_reduction_factor * 100
        }
    
    def generate_comprehensive_roi_report(self,
                                        baseline_metrics: Dict,
                                        improved_metrics: Dict,
                                        implementation_costs: float = 50000) -> Dict:
        """Generate comprehensive ROI analysis"""
        
        # Calculate all savings components
        inventory_savings = self.calculate_inventory_optimization_savings(
            baseline_metrics['inventory'],
            improved_metrics['inventory'],
            baseline_metrics['unit_costs']
        )
        
        stockout_savings = self.calculate_stockout_prevention_savings(
            improved_metrics['prevented_stockouts'],
            baseline_metrics['selling_prices']
        )
        
        forecast_savings = self.calculate_forecast_accuracy_value(
            baseline_metrics['forecast_mape'],
            improved_metrics['forecast_mape'],
            baseline_metrics['annual_revenue']
        )
        
        # Total financial impact
        total_annual_savings = (
            inventory_savings['total_annual_holding_savings'] +
            stockout_savings['total_gross_margin_saved'] +
            forecast_savings['annual_cost_savings']
        )
        
        # ROI calculation
        net_benefit = total_annual_savings - implementation_costs
        roi_percentage = (net_benefit / implementation_costs) * 100
        payback_period_months = (implementation_costs / (total_annual_savings / 12))
        
        return {
            'executive_summary': {
                'total_annual_savings': total_annual_savings,
                'implementation_costs': implementation_costs,
                'net_annual_benefit': net_benefit,
                'roi_percentage': roi_percentage,
                'payback_period_months': payback_period_months
            },
            'detailed_savings': {
                'inventory_optimization': inventory_savings,
                'stockout_prevention': stockout_savings,
                'forecast_improvement': forecast_savings
            },
            'business_case': self._generate_business_case_text(total_annual_savings, roi_percentage, payback_period_months)
        }
    
   