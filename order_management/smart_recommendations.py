"""Smart recommendation algorithms for order sheet generation - PRODUCTION"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any
from models.data_models import OrderSheetItem, ProductInsight, VariantDemand
from order_management.order_sheet_manager import OrderSheetManager

def add_all_variants_for_product_with_smart_recommendations(
    product_id: int, 
    style_number: str,
    brand: str,
    orders_df: pd.DataFrame, 
    inventory_df: pd.DataFrame, 
    location_config: Dict[int, str], 
    order_manager: OrderSheetManager,
    product_insight: ProductInsight = None,
    analysis_days: int = 30
) -> int:
    """Add all variants with SMART store-specific recommendations based on actual demand patterns"""
    
    # Get all variants for this product
    product_variants = inventory_df[inventory_df['product_id'] == product_id]
    
    if product_variants.empty:
        st.warning(f"No variants found for {style_number}")
        return 0
    
    # Calculate recent demand patterns by variant and store
    recent_cutoff = orders_df['created_at'].max() - pd.Timedelta(days=analysis_days)
    recent_orders = orders_df[
        (orders_df['product_id'] == product_id) & 
        (orders_df['created_at'] >= recent_cutoff)
    ]
    
    # Get total product recommendation from insight
    total_product_recommendation = product_insight.recommended_qty if product_insight else 20
    total_product_recent_sales = recent_orders['quantity'].sum()
    
    # Show progress info
    st.info(f"🔍 Analyzing {len(product_variants)} variants for {style_number} (Total recommendation: {total_product_recommendation} units)")
    
    added_count = 0
    
    for _, variant_row in product_variants.iterrows():
        variant_id = variant_row['variant_id']
        variant_title = variant_row.get('variant_title', 'Unknown')
        
        # Calculate variant-specific demand by store
        variant_orders = recent_orders[recent_orders['variant_id'] == variant_id]
        variant_recent_sales = variant_orders['quantity'].sum()
        
        # Determine variant proportion
        if total_product_recent_sales > 0:
            variant_proportion = variant_recent_sales / total_product_recent_sales
        else:
            # If no recent sales, distribute equally among variants
            variant_proportion = 1.0 / len(product_variants)
        
        # Calculate base recommendation for this variant
        variant_base_recommendation = max(1, int(total_product_recommendation * variant_proportion))
        
        # Calculate store-specific recommendations
        store_recommendations = {}
        
        # Check for Unknown store issue and handle it
        unknown_store_sales = 0
        if not variant_orders.empty and 'Unknown' in variant_orders['Store Location'].values:
            unknown_store_sales = variant_orders[variant_orders['Store Location'] == 'Unknown']['quantity'].sum()
        
        # If all sales are attributed to "Unknown" store, distribute intelligently
        if variant_recent_sales > 0 and unknown_store_sales == variant_recent_sales:
            # All sales are "Unknown" - distribute based on inventory levels and business logic
            total_current_inventory = sum([variant_row.get(f'inventory_{store.lower()}', 0) for store in location_config.values()])
            
            for store_name in location_config.values():
                inventory_col = f'inventory_{store_name.lower()}'
                current_inventory = variant_row.get(inventory_col, 0) or 0
                
                # Calculate need based on inventory levels and total recommendation
                if total_current_inventory > 0:
                    inventory_proportion = current_inventory / total_current_inventory
                    # Invert proportion so low inventory gets more allocation
                    need_factor = max(0.1, 1 - inventory_proportion)
                else:
                    need_factor = 0.25  # Equal distribution if no inventory data
                
                # Calculate recommendation based on product total and need factor
                recommended = max(0, int(variant_base_recommendation * need_factor))
                
                # Apply minimum logic for critical items
                if recommended == 0 and product_insight and product_insight.reorder_priority in ['CRITICAL', 'HIGH']:
                    if current_inventory < 3:
                        recommended = 1  # Minimum 1 for critical items with low inventory
                
                store_recommendations[store_name] = recommended
        
        else:
            # Normal logic: Use store-specific sales data
            if total_product_recent_sales == 0:
                # No recent sales for entire product - use insight-based distribution
                base_per_variant = max(1, total_product_recommendation // max(len(product_variants), 1))
                
                for store_name in location_config.values():
                    inventory_col = f'inventory_{store_name.lower()}'
                    current_inventory = variant_row.get(inventory_col, 0) or 0
                    
                    # Smart allocation based on inventory levels
                    if current_inventory == 0:
                        store_recommendations[store_name] = max(2, base_per_variant)
                    elif current_inventory < 3:
                        store_recommendations[store_name] = max(1, base_per_variant)
                    elif current_inventory < 6:
                        store_recommendations[store_name] = max(1, base_per_variant // 2)
                    else:
                        store_recommendations[store_name] = 0
                        
            elif variant_recent_sales == 0:
                # This specific variant has no recent sales, but product overall does
                conservative_allocation = max(1, total_product_recommendation // (len(product_variants) * 2))
                
                for store_name in location_config.values():
                    inventory_col = f'inventory_{store_name.lower()}'
                    current_inventory = variant_row.get(inventory_col, 0) or 0
                    
                    # Only allocate if inventory is very low
                    if current_inventory < 2:
                        store_recommendations[store_name] = max(1, conservative_allocation // 4)
                    else:
                        store_recommendations[store_name] = 0
            
            else:
                # Normal demand-based logic
                for store_name in location_config.values():
                    # Get current inventory for this store
                    inventory_col = f'inventory_{store_name.lower()}'
                    current_inventory = variant_row.get(inventory_col, 0) or 0
                    
                    # Get recent sales for this store and variant
                    store_variant_orders = variant_orders[variant_orders['Store Location'] == store_name]
                    store_recent_sales = store_variant_orders['quantity'].sum()
                    store_daily_demand = store_recent_sales / analysis_days if store_recent_sales > 0 else 0
                    
                    if store_daily_demand > 0:
                        # Calculate target inventory (45 days supply for active variants)
                        target_inventory = store_daily_demand * 45
                        needed = max(0, target_inventory - current_inventory)
                        
                        # Apply minimum order logic
                        if needed > 0:
                            if needed < 1 and store_daily_demand > 0.03:
                                needed = 1
                            elif needed < 2 and store_daily_demand > 0.1:
                                needed = 2
                            elif needed < 3 and store_daily_demand > 0.2:
                                needed = 3
                            
                            store_recommendations[store_name] = int(needed)
                        else:
                            store_recommendations[store_name] = 0
                    else:
                        # No recent demand at this store for this variant
                        if variant_recent_sales >= 5 and current_inventory < 2:
                            store_recommendations[store_name] = 1
                        else:
                            store_recommendations[store_name] = 0
        
        # Ensure at least some distribution if variant has overall demand
        total_distributed = sum(store_recommendations.values())
        if total_distributed == 0 and variant_recent_sales > 0:
            # If no distribution but variant sells, give minimal equal distribution
            per_store = max(1, variant_base_recommendation // 4)
            store_recommendations = {store: per_store for store in location_config.values()}
        
        # Apply trend multipliers from product insight
        if product_insight:
            if product_insight.trend_classification in ['Trending Up', 'Hot Seller']:
                multiplier = 1.3
                for store in store_recommendations:
                    store_recommendations[store] = int(store_recommendations[store] * multiplier)
            elif 'Declining' in product_insight.trend_classification:
                multiplier = 0.7
                for store in store_recommendations:
                    store_recommendations[store] = int(store_recommendations[store] * multiplier)
        
        # Create and add to order manager
        final_total = sum(store_recommendations.values())
        
        if final_total > 0:
            # Parse color and size from variant_title or individual fields
            color = str(variant_row.get('color', ''))
            size = str(variant_row.get('size', ''))
            if not color and not size:
                # Try to parse from variant_title
                if ' / ' in str(variant_title):
                    color, size = str(variant_title).split(' / ', 1)
                else:
                    color = str(variant_title)
                    size = ''
            
            # Create VariantDemand object with proper recommendations
            variant_demand = VariantDemand(
                product_id=int(product_id),
                variant_id=int(variant_row['variant_id']),
                style_number=style_number,
                description=str(variant_row.get('description', '')),
                vendor=brand,
                variant_title=str(variant_title),
                color=color,
                size=size,
                store_demand={},  # Not needed for order creation
                store_inventory={},  # Not needed for order creation
                store_recommended=store_recommendations,  # THE KEY - actual smart recommendations
                total_recommended=final_total,
                total_current_inventory=0,  # Not needed for order creation
                total_daily_demand=0,  # Not needed for order creation
                priority_score=0  # Not needed for order creation
            )
            
            # Use the order manager's add method
            was_added = order_manager.add_variant_to_order(variant_demand)
            if was_added:
                added_count += 1
    
    # Show final summary
    total_recommended_units = sum([
        item.qty_hilo + item.qty_kailua + item.qty_kapaa + item.qty_wailuku 
        for item in order_manager.selected_items.get(brand, [])
        if item.product_id == product_id
    ])
    
    st.success(f"✅ Smart recommendations complete!")
    st.info(f"📦 {style_number}: Added {added_count} variants with {total_recommended_units} total units")
    
    return added_count