"""Variant demand analysis engine"""
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from models.data_models import ProductInsight, VariantDemand

class VariantDemandAnalyzer:
    """Analyzes demand patterns at the variant and store level"""
    
    def __init__(self, location_config: Dict[int, str]):
        self.location_config = location_config
        self.location_name_to_id = {v: k for k, v in location_config.items()}
    
    def analyze_variant_demand(
        self, 
        orders_df: pd.DataFrame, 
        inventory_df: pd.DataFrame,
        insights: List[ProductInsight],
        analysis_days: int = 30
    ) -> List[VariantDemand]:
        """Analyze demand patterns for all variants with store-level distribution"""
        
        if orders_df.empty or inventory_df.empty:
            return []
        
        st.info("🔍 Analyzing variant-level demand patterns...")
        
        # Create insights lookup
        insights_lookup = {insight.product_id: insight for insight in insights}
        
        # Filter to recent orders for demand calculation
        recent_cutoff = orders_df['created_at'].max() - pd.Timedelta(days=analysis_days)
        recent_orders = orders_df[orders_df['created_at'] >= recent_cutoff]
        
        # Group by variant and store to calculate demand
        if recent_orders.empty:
            st.warning("No recent orders found for variant analysis")
            return []
        
        # Calculate demand by variant and store
        variant_store_demand = recent_orders.groupby([
            'product_id', 'variant_id', 'Store Location', 
            'Style Number', 'Description', 'vendor', 'variant_title'
        ]).agg({
            'quantity': 'sum'
        }).reset_index()
        
        # Calculate daily demand
        variant_store_demand['daily_demand'] = variant_store_demand['quantity'] / analysis_days
        
        # Get unique variants
        unique_variants = variant_store_demand[[
            'product_id', 'variant_id', 'Style Number', 'Description', 'vendor', 'variant_title'
        ]].drop_duplicates()
        
        variant_demands = []
        
        for _, variant_row in unique_variants.iterrows():
            product_id = variant_row['product_id']
            variant_id = variant_row['variant_id']
            
            # Get demand for this variant across all stores
            variant_demand_data = variant_store_demand[
                (variant_store_demand['product_id'] == product_id) &
                (variant_store_demand['variant_id'] == variant_id)
            ]
            
            # Get inventory for this variant
            variant_inventory = inventory_df[
                (inventory_df['product_id'] == product_id) &
                (inventory_df['variant_id'] == variant_id)
            ]
            
            if variant_inventory.empty:
                continue
            
            variant_info = variant_inventory.iloc[0]
            
            # Parse color and size from variant title
            variant_title = str(variant_info.get('variant_title', ''))
            if ' / ' in variant_title:
                color, size = variant_title.split(' / ', 1)
            else:
                color, size = variant_title, ''
            
            # Build store demand and inventory dictionaries
            store_demand = {}
            store_inventory = {}
            total_current_inventory = 0
            total_daily_demand = 0
            
            for store_name in self.location_config.values():
                # Get demand for this store
                store_demand_row = variant_demand_data[
                    variant_demand_data['Store Location'] == store_name
                ]
                daily_demand = store_demand_row['daily_demand'].sum() if not store_demand_row.empty else 0
                store_demand[store_name] = daily_demand
                total_daily_demand += daily_demand
                
                # Get inventory for this store
                inventory_column = f'inventory_{store_name.lower()}'
                inventory_qty = variant_info.get(inventory_column, 0) or 0
                store_inventory[store_name] = int(inventory_qty)
                total_current_inventory += int(inventory_qty)
            
            # Calculate store-specific recommendations
            store_recommended = self._calculate_store_recommendations(
                store_demand, store_inventory, product_id, insights_lookup
            )
            
            total_recommended = sum(store_recommended.values())
            
            # Calculate priority score
            product_insight = insights_lookup.get(product_id)
            priority_score = self._calculate_variant_priority(
                product_insight, total_daily_demand, total_current_inventory
            )
            
            # Create VariantDemand object
            variant_demand = VariantDemand(
                product_id=int(product_id),
                variant_id=int(variant_id),
                style_number=str(variant_row['Style Number']),
                description=str(variant_row['Description']),
                vendor=str(variant_row['vendor']),
                variant_title=variant_title,
                color=color,
                size=size,
                store_demand=store_demand,
                store_inventory=store_inventory,
                store_recommended=store_recommended,
                total_recommended=total_recommended,
                total_current_inventory=total_current_inventory,
                total_daily_demand=total_daily_demand,
                priority_score=priority_score
            )
            
            variant_demands.append(variant_demand)
        
        # Sort by priority score and total demand
        variant_demands.sort(key=lambda x: (x.priority_score, x.total_daily_demand), reverse=True)
        
        st.success(f"✅ Analyzed {len(variant_demands)} variants")
        return variant_demands
    
    def _calculate_store_recommendations(
        self, 
        store_demand: Dict[str, float], 
        store_inventory: Dict[str, int],
        product_id: int,
        insights_lookup: Dict[int, ProductInsight]
    ) -> Dict[str, int]:
        """Calculate recommended quantities for each store"""
        
        # Get product insight for overall recommendation logic
        product_insight = insights_lookup.get(product_id)
        
        # Base calculation: 30 days supply per store
        target_days = 30
        store_recommended = {}
        total_demand = sum(store_demand.values())
        
        if total_demand == 0:
            # No demand - minimal orders
            for store_name in store_demand.keys():
                store_recommended[store_name] = 0
            return store_recommended
        
        # Calculate base recommendations
        for store_name, daily_demand in store_demand.items():
            current_inventory = store_inventory[store_name]
            
            if daily_demand > 0:
                # Calculate needed inventory
                target_inventory = daily_demand * target_days
                needed = max(0, target_inventory - current_inventory)
                
                # Apply trend adjustments from product insight
                if product_insight:
                    if product_insight.trend_classification in ['Trending Up', 'Hot Seller']:
                        needed *= 1.2  # 20% more for trending products
                    elif 'Declining' in product_insight.trend_classification:
                        needed *= 0.7  # 30% less for declining products
                
                # Minimum order logic
                if needed > 0 and needed < 1:
                    needed = 1  # Minimum 1 unit if any demand
                elif needed > 0 and needed < 2 and daily_demand > 0.1:
                    needed = 2  # Minimum 2 units for meaningful demand
                
                store_recommended[store_name] = int(needed)
            else:
                # No demand at this store
                store_recommended[store_name] = 0
        
        return store_recommended
    
    def _calculate_variant_priority(
        self, 
        product_insight: Optional[ProductInsight], 
        total_daily_demand: float,
        total_current_inventory: int
    ) -> int:
        """Calculate priority score for variant (0-100)"""
        
        score = 0
        
        # Base score from daily demand
        if total_daily_demand >= 1.0:
            score += 40
        elif total_daily_demand >= 0.5:
            score += 30
        elif total_daily_demand >= 0.2:
            score += 20
        elif total_daily_demand > 0:
            score += 10
        
        # Score from product insight
        if product_insight:
            if product_insight.reorder_priority == 'CRITICAL':
                score += 30
            elif product_insight.reorder_priority == 'HIGH':
                score += 20
            elif product_insight.reorder_priority == 'MEDIUM':
                score += 10
            
            # Trend bonus
            if product_insight.trend_classification in ['Trending Up', 'Hot Seller']:
                score += 15
            elif product_insight.trend_classification in ['New Strong Seller']:
                score += 10
        
        # Inventory urgency
        if total_daily_demand > 0:
            days_of_stock = total_current_inventory / total_daily_demand
            if days_of_stock <= 14:
                score += 15
            elif days_of_stock <= 30:
                score += 10
            elif days_of_stock <= 60:
                score += 5
        
        return min(score, 100)

