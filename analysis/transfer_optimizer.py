import streamlit as st
import numpy as np
from scipy.optimize import linprog
from typing import Dict, List, Tuple

class TransferOptimizer:
    def __init__(self, transfer_costs: Dict[Tuple[str, str], float] = None):
        self.transfer_costs = transfer_costs or self._default_transfer_costs()
        self.holding_cost_per_unit = 0.1  # Daily holding cost
        self.stockout_cost_per_unit = 5.0  # Lost sale cost
    
    def _default_transfer_costs(self):
        """Default transfer costs based on distance"""
        locations = ['Hilo', 'Kailua', 'Kapaa', 'Wailuku']
        costs = {}
        # Simplified: cost = $0.50 per unit for inter-island, $0.25 intra-island
        for i in locations:
            for j in locations:
                if i != j:
                    if (i == 'Hilo' and j in ['Kailua', 'Kapaa', 'Wailuku']) or \
                       (j == 'Hilo' and i in ['Kailua', 'Kapaa', 'Wailuku']):
                        costs[(i, j)] = 0.50  # Inter-island
                    else:
                        costs[(i, j)] = 0.25  # Intra-island
                else:
                    costs[(i, j)] = 0
        return costs
    
    def optimize_transfers(self, inventory_data: Dict[str, Dict[str, int]], 
                          demand_data: Dict[str, Dict[str, float]]) -> Dict:
        """Solve transfer optimization using linear programming"""
        
        locations = list(inventory_data.keys())
        products = list(inventory_data[locations[0]].keys())
        
        results = {}
        
        for product in products:
            # Current inventory by location
            current_inv = [inventory_data[loc].get(product, 0) for loc in locations]
            # Daily demand by location  
            daily_demand = [demand_data[loc].get(product, 0) for loc in locations]
            
            # Calculate optimal allocation
            total_inventory = sum(current_inv)
            total_demand = sum(daily_demand)
            
            if total_demand > 0:
                # Optimal allocation proportional to demand
                optimal_allocation = [(d / total_demand) * total_inventory for d in daily_demand]
                
                # Transfer recommendations
                transfers = {}
                for i, from_loc in enumerate(locations):
                    for j, to_loc in enumerate(locations):
                        if i != j:
                            excess_at_i = current_inv[i] - optimal_allocation[i]
                            shortage_at_j = optimal_allocation[j] - current_inv[j]
                            
                            if excess_at_i > 1 and shortage_at_j > 1:
                                transfer_qty = min(excess_at_i, shortage_at_j, excess_at_i * 0.5)
                                if transfer_qty >= 1:
                                    transfers[(from_loc, to_loc)] = {
                                        'quantity': int(transfer_qty),
                                        'cost': transfer_qty * self.transfer_costs.get((from_loc, to_loc), 0),
                                        'benefit': transfer_qty * self.stockout_cost_per_unit
                                    }
                
                results[product] = transfers
        
        return results
