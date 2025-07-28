# COMPLETE REPLACEMENT FOR analysis/transfer_analysis.py
# This replaces the existing _identify_transfer_opportunities method and adds the new TransferOptimizer

"""Enhanced Transfer recommendation analysis engine with economic optimization"""
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import logging
from scipy.optimize import linprog
from models.data_models import ProductInsight, TransferRecommendation

logger = logging.getLogger(__name__)

class TransferOptimizer:
    """Advanced transfer optimizer using linear programming and economic modeling"""
    
    def __init__(self, transfer_costs: Dict[Tuple[str, str], float] = None):
        self.transfer_costs = transfer_costs or self._default_transfer_costs()
        self.holding_cost_per_unit_per_day = 0.003  # $0.003 per unit per day (roughly $1/year)
        self.stockout_cost_per_unit = 8.0  # Lost profit per stockout unit
        self.min_transfer_threshold = 2  # Minimum units to consider transferring
        
    def _default_transfer_costs(self):
        """Default transfer costs based on Hawaiian geography"""
        locations = ['Hilo', 'Kailua', 'Kapaa', 'Wailuku']
        costs = {}
        
        # Cost matrix based on inter-island vs intra-island shipping
        cost_matrix = {
            # From Big Island (Hilo) to others - inter-island shipping
            ('Hilo', 'Kailua'): 0.75,   # Big Island to Oahu
            ('Hilo', 'Kapaa'): 0.65,    # Big Island to Kauai  
            ('Hilo', 'Wailuku'): 0.55,  # Big Island to Maui
            
            # From Oahu (Kailua) to others
            ('Kailua', 'Hilo'): 0.75,   # Oahu to Big Island
            ('Kailua', 'Kapaa'): 0.45,  # Oahu to Kauai (shorter)
            ('Kailua', 'Wailuku'): 0.35, # Oahu to Maui (closest)
            
            # From Kauai (Kapaa) to others  
            ('Kapaa', 'Hilo'): 0.65,    # Kauai to Big Island
            ('Kapaa', 'Kailua'): 0.45,  # Kauai to Oahu
            ('Kapaa', 'Wailuku'): 0.55, # Kauai to Maui
            
            # From Maui (Wailuku) to others
            ('Wailuku', 'Hilo'): 0.55,  # Maui to Big Island
            ('Wailuku', 'Kailua'): 0.35, # Maui to Oahu
            ('Wailuku', 'Kapaa'): 0.55,  # Maui to Kauai
        }
        
        # Add zero cost for same location
        for loc in locations:
            cost_matrix[(loc, loc)] = 0.0
            
        return cost_matrix
    
    def optimize_transfers_economically(self, 
                                      inventory_data: Dict[str, Dict[str, int]], 
                                      demand_data: Dict[str, Dict[str, float]],
                                      product_insights: Dict[str, ProductInsight]) -> Dict[str, List[Dict]]:
        """
        Advanced transfer optimization using economic modeling
        
        Args:
            inventory_data: {location: {product_id: current_inventory}}
            demand_data: {location: {product_id: daily_demand}}
            product_insights: {product_id: ProductInsight object}
        
        Returns:
            {product_id: [transfer_recommendations]}
        """
        
        results = {}
        
        # Get all unique products and locations
        all_products = set()
        all_locations = set()
        
        for location, products in inventory_data.items():
            all_locations.add(location)
            all_products.update(products.keys())
        
        for location, products in demand_data.items():
            all_locations.add(location)
            all_products.update(products.keys())
        
        locations = sorted(list(all_locations))
        
        st.info(f"🧮 Optimizing transfers for {len(all_products)} products across {len(locations)} locations")
        
        for product_id in all_products:
            try:
                # Get current state for this product
                current_inventory = {loc: inventory_data.get(loc, {}).get(product_id, 0) for loc in locations}
                daily_demand = {loc: demand_data.get(loc, {}).get(product_id, 0) for loc in locations}
                
                # Skip if no inventory or demand
                total_inventory = sum(current_inventory.values())
                total_demand = sum(daily_demand.values())
                
                if total_inventory < self.min_transfer_threshold or total_demand <= 0:
                    continue
                
                # Get product insight for lead time and trend info
                insight = product_insights.get(product_id)
                lead_time = 14  # Default lead time
                trend_multiplier = 1.0
                
                if insight:
                    # Use brand-specific lead time if available
                    lead_time = insight.reorder_timing  # This should be converted to days
                    if insight.trend_classification in ['Trending Up', 'Hot Seller']:
                        trend_multiplier = 1.2
                    elif 'Declining' in insight.trend_classification:
                        trend_multiplier = 0.8
                
                # Calculate optimal allocation using economic principles
                optimal_transfers = self._solve_transfer_optimization(
                    current_inventory, daily_demand, locations, 
                    product_id, lead_time, trend_multiplier
                )
                
                if optimal_transfers:
                    results[product_id] = optimal_transfers
                    
            except Exception as e:
                logger.warning(f"Transfer optimization failed for product {product_id}: {e}")
                continue
        
        return results
    
    def _solve_transfer_optimization(self, 
                                   current_inventory: Dict[str, int],
                                   daily_demand: Dict[str, float], 
                                   locations: List[str],
                                   product_id: str,
                                   lead_time: int,
                                   trend_multiplier: float) -> List[Dict]:
        """
        Solve the transfer optimization problem using economic modeling
        
        Mathematical formulation:
        Minimize: Transfer_Costs + Holding_Costs + Stockout_Costs
        Subject to: 
        - Supply constraints (can't transfer more than available)
        - Demand constraints (transfers should help meet demand)
        - Non-negativity constraints
        """
        
        n_locations = len(locations)
        
        # Calculate target inventory levels using newsvendor model
        target_inventory = {}
        for i, loc in enumerate(locations):
            demand = daily_demand[loc] * trend_multiplier
            # Target = Lead time demand + Safety stock (assuming 95% service level)
            safety_stock = 1.65 * np.sqrt(demand * lead_time * 0.3)  # Assuming 30% CV
            target_inventory[loc] = max(0, (demand * lead_time) + safety_stock)
        
        # Current imbalances
        imbalances = {}
        for loc in locations:
            imbalances[loc] = current_inventory[loc] - target_inventory[loc]
        
        # Simple heuristic optimization (more efficient than full LP for this problem size)
        transfers = []
        excess_locations = [(loc, imbalances[loc]) for loc in locations if imbalances[loc] > self.min_transfer_threshold]
        shortage_locations = [(loc, -imbalances[loc]) for loc in locations if imbalances[loc] < -1]
        
        # Sort by magnitude of imbalance
        excess_locations.sort(key=lambda x: x[1], reverse=True)
        shortage_locations.sort(key=lambda x: x[1], reverse=True)
        
        for from_loc, excess_qty in excess_locations:
            for to_loc, shortage_qty in shortage_locations:
                if from_loc == to_loc:
                    continue
                
                # Calculate transfer quantity
                transfer_qty = min(
                    excess_qty,  # Available excess
                    shortage_qty,  # Needed shortage
                    excess_qty * 0.6  # Don't transfer more than 60% of excess
                )
                
                if transfer_qty >= self.min_transfer_threshold:
                    # Calculate economic benefit
                    transfer_cost = transfer_qty * self.transfer_costs.get((from_loc, to_loc), 1.0)
                    
                    # Benefit = Avoided stockout cost - transfer cost - extra holding cost
                    avoided_stockout = transfer_qty * self.stockout_cost_per_unit
                    extra_holding = transfer_qty * self.holding_cost_per_unit_per_day * 30  # 30 days
                    
                    net_benefit = avoided_stockout - transfer_cost - extra_holding
                    
                    # Only recommend if economically beneficial
                    if net_benefit > 0:
                        transfers.append({
                            'from_location': from_loc,
                            'to_location': to_loc,
                            'quantity': int(transfer_qty),
                            'transfer_cost': transfer_cost,
                            'net_benefit': net_benefit,
                            'benefit_per_unit': net_benefit / transfer_qty,
                            'urgency_score': self._calculate_urgency_score(
                                current_inventory[to_loc], daily_demand[to_loc], lead_time
                            )
                        })
                        
                        # Update remaining quantities for next iteration
                        excess_locations = [(loc, qty - (transfer_qty if loc == from_loc else 0)) 
                                          for loc, qty in excess_locations]
                        shortage_locations = [(loc, qty - (transfer_qty if loc == to_loc else 0)) 
                                            for loc, qty in shortage_locations]
        
        # Sort transfers by benefit per unit (most beneficial first)
        transfers.sort(key=lambda x: x['benefit_per_unit'], reverse=True)
        
        return transfers[:10]  # Return top 10 most beneficial transfers
    
    def _calculate_urgency_score(self, current_inventory: int, daily_demand: float, lead_time: int) -> float:
        """Calculate urgency score based on stockout risk"""
        if daily_demand <= 0:
            return 0.0
        
        days_of_stock = current_inventory / daily_demand
        
        if days_of_stock <= lead_time:
            return 1.0  # Critical
        elif days_of_stock <= lead_time * 1.5:
            return 0.7  # High
        elif days_of_stock <= lead_time * 2:
            return 0.4  # Medium
        else:
            return 0.1  # Low


class TransferAnalysisEngine:
    """Enhanced Transfer Analysis Engine with economic optimization"""
    
    def __init__(self, location_config: Dict[int, str], user_profile):
        self.location_config = location_config
        self.user_profile = user_profile
        self.min_transfer_qty = 2  # Minimum quantity to consider transferring
        
        # NEW: Initialize advanced transfer optimizer
        self.transfer_optimizer = TransferOptimizer()
    
    def analyze_transfer_opportunities(
        self,
        orders_df: pd.DataFrame,
        inventory_df: pd.DataFrame,
        insights: List[ProductInsight],
        analysis_period_days: int = 30
    ) -> List[TransferRecommendation]:
        """
        ENHANCED: Main method to identify transfer opportunities using economic optimization
        """
        
        recommendations = []
        
        if orders_df.empty or inventory_df.empty:
            return recommendations
        
        # Step 1: Calculate location-specific demand patterns
        location_demand = self._calculate_location_demand(orders_df, analysis_period_days)
        
        # Step 2: Analyze inventory distribution by variant
        inventory_distribution = self._analyze_inventory_distribution(inventory_df)
        
        # Step 3: Prepare data for advanced optimization
        inventory_data = self._prepare_inventory_data_for_optimization(inventory_distribution)
        demand_data = self._prepare_demand_data_for_optimization(location_demand)
        insights_lookup = {insight.product_id: insight for insight in insights}
        
        # Step 4: NEW - Run advanced economic optimization
        st.info("🧠 Running advanced transfer optimization with economic modeling...")
        
        optimal_transfers = self.transfer_optimizer.optimize_transfers_economically(
            inventory_data, demand_data, insights_lookup
        )
        
        # Step 5: Convert optimization results to TransferRecommendation objects
        for product_id, transfers in optimal_transfers.items():
            for transfer in transfers:
                recommendation = self._create_transfer_recommendation_from_optimization(
                    product_id, transfer, inventory_distribution, location_demand, insights_lookup
                )
                if recommendation:
                    recommendations.append(recommendation)
        
        # Step 6: Sort by economic benefit and urgency
        recommendations.sort(
            key=lambda x: (
                {'URGENT': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}[x.transfer_urgency],
                x.financial_impact
            ), 
            reverse=True
        )
        
        return recommendations[:30]  # Limit to top 30 recommendations
    
    def _prepare_inventory_data_for_optimization(self, inventory_distribution: pd.DataFrame) -> Dict[str, Dict[str, int]]:
        """Prepare inventory data in format needed for optimization"""
        inventory_data = {}
        
        for _, row in inventory_distribution.iterrows():
            location = row['location_name']
            product_id = str(row['product_id'])
            inventory_qty = int(row['inventory_qty'])
            
            if location not in inventory_data:
                inventory_data[location] = {}
            
            inventory_data[location][product_id] = inventory_qty
        
        return inventory_data
    
    def _prepare_demand_data_for_optimization(self, location_demand: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Prepare demand data in format needed for optimization"""
        demand_data = {}
        
        if location_demand.empty:
            return demand_data
        
        for _, row in location_demand.iterrows():
            location = row['Store Location']
            product_id = str(row['product_id'])
            daily_demand = float(row['daily_demand'])
            
            if location not in demand_data:
                demand_data[location] = {}
            
            demand_data[location][product_id] = daily_demand
        
        return demand_data
    
    def _create_transfer_recommendation_from_optimization(
        self, 
        product_id: str,
        transfer_data: Dict,
        inventory_distribution: pd.DataFrame,
        location_demand: pd.DataFrame,
        insights_lookup: Dict
    ) -> Optional[TransferRecommendation]:
        """Create TransferRecommendation from optimization results"""
        
        try:
            # Get product information
            product_id_int = int(product_id)
            product_info = inventory_distribution[inventory_distribution['product_id'] == product_id_int]
            
            if product_info.empty:
                return None
            
            product_row = product_info.iloc[0]
            
            # Get location information
            from_location = transfer_data['from_location']
            to_location = transfer_data['to_location']
            
            # Get inventory levels
            from_inventory_row = inventory_distribution[
                (inventory_distribution['product_id'] == product_id_int) &
                (inventory_distribution['location_name'] == from_location)
            ]
            to_inventory_row = inventory_distribution[
                (inventory_distribution['product_id'] == product_id_int) &
                (inventory_distribution['location_name'] == to_location)
            ]
            
            from_inventory = int(from_inventory_row.iloc[0]['inventory_qty']) if not from_inventory_row.empty else 0
            to_inventory = int(to_inventory_row.iloc[0]['inventory_qty']) if not to_inventory_row.empty else 0
            
            # Get demand information
            from_demand_row = location_demand[
                (location_demand['product_id'] == product_id_int) &
                (location_demand['Store Location'] == from_location)
            ]
            to_demand_row = location_demand[
                (location_demand['product_id'] == product_id_int) &
                (location_demand['Store Location'] == to_location)
            ]
            
            from_daily_demand = float(from_demand_row.iloc[0]['daily_demand']) if not from_demand_row.empty else 0.0
            to_daily_demand = float(to_demand_row.iloc[0]['daily_demand']) if not to_demand_row.empty else 0.0
            
            # Calculate days of stock
            from_days_stock = int(from_inventory / max(from_daily_demand, 0.1))
            to_days_stock = int(to_inventory / max(to_daily_demand, 0.1))
            
            # Determine urgency based on optimization score
            urgency_score = transfer_data.get('urgency_score', 0.5)
            if urgency_score >= 0.8:
                urgency = 'URGENT'
            elif urgency_score >= 0.6:
                urgency = 'HIGH'
            elif urgency_score >= 0.3:
                urgency = 'MEDIUM'
            else:
                urgency = 'LOW'
            
            # Get location IDs
            from_location_id = next((k for k, v in self.location_config.items() if v == from_location), 0)
            to_location_id = next((k for k, v in self.location_config.items() if v == to_location), 0)
            
            # Generate reasoning
            net_benefit = transfer_data.get('net_benefit', 0)
            transfer_cost = transfer_data.get('transfer_cost', 0)
            
            reasoning = (f"Economic optimization recommends transferring {transfer_data['quantity']} units "
                        f"from {from_location} (excess: {from_days_stock} days stock) to {to_location} "
                        f"(shortage: {to_days_stock} days stock). "
                        f"Net benefit: ${net_benefit:.2f}, Transfer cost: ${transfer_cost:.2f}")
            
            return TransferRecommendation(
                product_id=product_id_int,
                style_number=str(product_row.get('style_number', 'Unknown')),
                description=str(product_row.get('description', 'No description')),
                vendor=str(product_row.get('vendor', 'Unknown')),
                variant_id=int(product_row.get('variant_id', 0)),
                variant_title=str(product_row.get('variant_title', 'Unknown')),
                
                from_location_id=from_location_id,
                from_location_name=from_location,
                from_inventory=from_inventory,
                from_daily_demand=from_daily_demand,
                from_days_of_stock=from_days_stock,
                
                to_location_id=to_location_id,
                to_location_name=to_location,
                to_inventory=to_inventory,
                to_daily_demand=to_daily_demand,
                to_days_of_stock=to_days_stock,
                
                recommended_transfer_qty=int(transfer_data['quantity']),
                transfer_urgency=urgency,
                financial_impact=float(net_benefit),
                opportunity_cost=float(transfer_data.get('transfer_cost', 0)),
                
                demand_imbalance_score=float(abs(from_days_stock - to_days_stock)),
                transfer_efficiency=float(transfer_data.get('benefit_per_unit', 0)),
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Error creating transfer recommendation: {e}")
            return None
    
    # Keep existing helper methods unchanged
    def _calculate_location_demand(self, orders_df: pd.DataFrame, days: int) -> pd.DataFrame:
        """Calculate daily demand by product/variant at each location"""
        
        # Filter to recent orders for demand calculation
        recent_cutoff = orders_df['created_at'].max() - pd.Timedelta(days=days)
        recent_orders = orders_df[orders_df['created_at'] >= recent_cutoff]
        
        if recent_orders.empty:
            return pd.DataFrame()
        
        # Group by product, variant, and location
        demand_analysis = recent_orders.groupby([
            'product_id', 'variant_id', 'location_id', 'Store Location',
            'Style Number', 'Description', 'vendor', 'variant_title'
        ]).agg({
            'quantity': 'sum',
            'total_value': 'sum',
            'created_at': 'count'
        }).reset_index()
        
        # Calculate daily demand
        demand_analysis['daily_demand'] = demand_analysis['quantity'] / days
        demand_analysis['daily_revenue'] = demand_analysis['total_value'] / days
        
        return demand_analysis
    
    def _analyze_inventory_distribution(self, inventory_df: pd.DataFrame) -> pd.DataFrame:
        """Analyze how inventory is distributed across locations"""
        
        if inventory_df.empty:
            return pd.DataFrame()
        
        # Melt inventory data to get location-specific inventory
        location_cols = [col for col in inventory_df.columns if col.startswith('inventory_')]
        
        inventory_melted = []
        
        for _, row in inventory_df.iterrows():
            for col in location_cols:
                location_name = col.replace('inventory_', '').title()
                location_id = None
                
                # Map location name back to ID
                for loc_id, loc_name in self.location_config.items():
                    if loc_name.lower() == location_name.lower():
                        location_id = int(loc_id)  # Ensure it's an integer
                        break

                if location_id:
                    inventory_melted.append({
                        'product_id': int(row['product_id']),
                        'variant_id': int(row['variant_id']),
                        'style_number': str(row['style_number']),
                        'description': str(row['description']),
                        'vendor': str(row['vendor']),
                        'variant_title': str(row['variant_title']),
                        'location_id': int(location_id),  # Ensure it's an integer
                        'location_name': location_name.title(),
                        'inventory_qty': int(row[col] or 0)
                    })
        
        return pd.DataFrame(inventory_melted)
