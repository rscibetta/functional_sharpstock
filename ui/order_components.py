import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

from models.data_models import OrderSheetItem, ProductInsight  # FIXED: Added missing import
from order_management.order_sheet_manager import OrderSheetManager
from order_management.smart_recommendations import add_all_variants_for_product_with_smart_recommendations

def display_order_sheet_interface(
    insights: List[ProductInsight],
    orders_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    location_config: Dict[int, str],
    user_profile
):
    """Simplified order sheet interface - style-first approach"""
    
    st.subheader("📋 Order Sheet Generator")
    st.markdown("*Select products to reorder, then view variant breakdowns*")
    
    # Initialize order manager
    if 'order_sheet_manager' not in st.session_state:
        st.session_state['order_sheet_manager'] = OrderSheetManager(location_config)
    
    order_manager = st.session_state['order_sheet_manager']
    
    # Step 1: Brand Selection
    st.markdown("### 1️⃣ Select Brand")
    available_brands = sorted(list(set([i.vendor for i in insights if i.vendor not in ['Unknown', '', 'nan']])))
    
    if not available_brands:
        st.warning("No brands found in the analysis data")
        return
    
    selected_brand = st.selectbox(
        "Choose brand for order sheet:",
        available_brands,
        key="order_sheet_brand_selector"
    )
    
    # Step 2: Show Products Needing Reorder for This Brand
    st.markdown("### 2️⃣ Products to Reorder")
    
    # Filter insights for selected brand
    brand_insights = [i for i in insights if i.vendor == selected_brand]
    
    if not brand_insights:
        st.warning(f"No products found for {selected_brand}")
        return
    
    # Filter for products that actually need reordering
    reorder_insights = [i for i in brand_insights if i.reorder_priority in ['CRITICAL', 'HIGH', 'MEDIUM']]
    
    if not reorder_insights:
        st.info(f"No products currently need reordering for {selected_brand}")
        # Still show all products but with different messaging
        reorder_insights = brand_insights[:20]  # Show top 20
        st.write("Showing all products for this brand:")
    else:
        st.write(f"Found **{len(reorder_insights)}** products needing reorder:")
    
    # Quick filters
    col1, col2 = st.columns(2)
    with col1:
        priority_filter = st.selectbox(
            "Priority Filter:",
            ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
            key="order_priority_filter"
        )
    with col2:
        timing_filter = st.selectbox(
            "Timing Filter:",
            ["All", "Order Now", "Order This Week", "Monitor"],
            key="order_timing_filter"
        )
    
    # Apply filters
    if priority_filter != "All":
        reorder_insights = [i for i in reorder_insights if i.reorder_priority == priority_filter]
    if timing_filter != "All":
        reorder_insights = [i for i in reorder_insights if i.reorder_timing == timing_filter]
    
    if not reorder_insights:
        st.warning("No products match the selected filters")
        return
    
    # Display products as clickable list
    st.write("**Select products to add to order sheet:**")
    
    # Headers
    cols = st.columns([2, 3, 2, 1, 1, 1, 1])
    headers = ["Style", "Description", "Priority", "Daily Demand", "Inventory", "Reorder Qty", "Action"]
    for i, header in enumerate(headers):
        with cols[i]:
            st.markdown(f"**{header}**")
    
    st.markdown("---")
    
    # Display products
    for idx, insight in enumerate(reorder_insights[:20]):  # Limit to 20 for performance
        cols = st.columns([2, 3, 2, 1, 1, 1, 1])
        
        with cols[0]:
            # Make style number clickable for variant breakdown
            if st.button(insight.style_number, key=f"style_{idx}_{insight.product_id}"):
                st.session_state['selected_style_for_variants'] = insight
                st.rerun()
        
        with cols[1]:
            desc = insight.description[:35] + "..." if len(insight.description) > 35 else insight.description
            st.write(desc)
        
        with cols[2]:
            priority_colors = {
                'CRITICAL': '🔴',
                'HIGH': '🟠', 
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }
            st.write(f"{priority_colors.get(insight.reorder_priority, '')} {insight.reorder_priority}")
        
        with cols[3]:
            st.write(f"{insight.recent_daily_demand:.1f}")
        
        with cols[4]:
            st.write(f"{insight.current_inventory:,}")
        
        with cols[5]:
            st.write(f"{insight.recommended_qty:,}")
        
        with cols[6]:
            # Quick add entire product button with ACTUAL recommended quantities
            if st.button("➕ Add Style", key=f"add_style_{idx}_{insight.product_id}"):
                # Add all variants for this product WITH the business intelligence recommendations
                added = add_all_variants_for_product_with_smart_recommendations(
                    insight.product_id, 
                    insight.style_number,
                    selected_brand,
                    orders_df, 
                    inventory_df, 
                    location_config, 
                    order_manager,
                    insight  # Pass the insight for recommended quantities
                )
                if added > 0:
                    total_recommended = sum([
                        item.qty_hilo + item.qty_kailua + item.qty_kapaa + item.qty_wailuku 
                        for item in order_manager.selected_items.get(selected_brand, [])
                        if item.product_id == insight.product_id
                    ])
                    st.success(f"Added {added} variants for {insight.style_number} (Total: {total_recommended} units)")
                    st.rerun()
                else:
                    st.warning("No variants found or already added")
    
    # Step 3: Show Variant Breakdown (if style selected)
    if st.session_state.get('selected_style_for_variants'):
        selected_insight = st.session_state['selected_style_for_variants']
        
        st.markdown("---")
        st.markdown(f"### 3️⃣ Variant Breakdown - {selected_insight.style_number}")
        
        # Back button
        if st.button("← Back to Product List", key="back_to_products"):
            st.session_state.pop('selected_style_for_variants', None)
            st.rerun()
        
        # Show variant details for this product
        display_variant_breakdown_for_product(
            selected_insight,
            orders_df,
            inventory_df,
            location_config,
            order_manager,
            selected_brand
        )
    
    # Step 4: Current Order Sheet
    current_items = order_manager.selected_items.get(selected_brand, [])
    if current_items:
        st.markdown("---")
        st.markdown(f"### 4️⃣ Current Order Sheet - {selected_brand}")
        display_current_order_sheet(current_items, order_manager, selected_brand, location_config)

def display_variant_breakdown_for_product(
    selected_insight: ProductInsight,
    orders_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    location_config: Dict[int, str],
    order_manager: OrderSheetManager,
    selected_brand: str
):
    """Display detailed variant breakdown for a specific product"""
    
    product_id = selected_insight.product_id
    
    # Get variants for this product
    product_variants = inventory_df[inventory_df['product_id'] == product_id]
    
    if product_variants.empty:
        st.warning("No variant data found for this product")
        return
    
    st.write(f"**Product:** {selected_insight.description}")
    st.write(f"**Overall recommendation:** {selected_insight.recommended_qty} units")
    st.write(f"**Priority:** {selected_insight.reorder_priority} - {selected_insight.reorder_timing}")
    
    # Show reasoning
    with st.expander("💡 Why this product needs reordering"):
        st.write(selected_insight.reasoning)
    
    st.markdown("**Variants:**")
    
    # Headers
    cols = st.columns([2, 2, 1, 1, 1, 1, 1, 1])
    headers = ["Color", "Size", "Total Inv", "Hilo", "Kailua", "Kapaa", "Wailuku", "Action"]
    for i, header in enumerate(headers):
        with cols[i]:
            st.markdown(f"**{header}**")
    
    st.markdown("---")
    
    # Display each variant
    for idx, (_, variant) in enumerate(product_variants.iterrows()):
        cols = st.columns([2, 2, 1, 1, 1, 1, 1, 1])
        
        with cols[0]:
            st.write(variant.get('color', 'Unknown'))
        
        with cols[1]:
            st.write(variant.get('size', 'Unknown'))
        
        with cols[2]:
            st.write(f"{variant.get('total_inventory', 0):,}")
        
        # Show current inventory by store
        with cols[3]:
            st.write(f"{variant.get('inventory_hilo', 0)}")
        with cols[4]:
            st.write(f"{variant.get('inventory_kailua', 0)}")
        with cols[5]:
            st.write(f"{variant.get('inventory_kapaa', 0)}")
        with cols[6]:
            st.write(f"{variant.get('inventory_wailuku', 0)}")
        
        with cols[7]:
            # Add individual variant button
            if st.button("➕", key=f"add_variant_{idx}_{variant['variant_id']}"):
                # Calculate basic recommendations for this variant
                base_qty_per_store = max(1, selected_insight.recommended_qty // (4 * len(product_variants)))
                
                order_item = OrderSheetItem(
                    product_id=int(product_id),
                    variant_id=int(variant['variant_id']),
                    style_number=selected_insight.style_number,
                    description=selected_insight.description,
                    color=str(variant.get('color', '')),
                    size=str(variant.get('size', '')),
                    vendor=selected_brand,
                    qty_hilo=base_qty_per_store,
                    qty_kailua=base_qty_per_store,
                    qty_kapaa=base_qty_per_store,
                    qty_wailuku=base_qty_per_store,
                    priority=selected_insight.reorder_priority
                )
                
                if selected_brand not in order_manager.selected_items:
                    order_manager.selected_items[selected_brand] = []
                
                # Check if already exists
                existing = next((item for item in order_manager.selected_items[selected_brand] 
                               if item.variant_id == variant['variant_id']), None)
                
                if not existing:
                    order_manager.selected_items[selected_brand].append(order_item)
                    st.success(f"Added variant to order sheet")
                    st.rerun()
                else:
                    st.warning("Variant already in order sheet")

def display_current_order_sheet(
    current_items: List[OrderSheetItem], 
    order_manager: OrderSheetManager, 
    selected_brand: str,
    location_config: Dict[int, str]
):
    """Display current order sheet in template format - style-based rows with variant columns"""
    
    if not current_items:
        return
    
    # Group items by style number (like the Excel template)
    style_groups = {}
    for item in current_items:
        style = item.style_number
        if style not in style_groups:
            style_groups[style] = {
                'description': item.description,
                'vendor': item.vendor,
                'variants': []
            }
        
        # Create variant identifier (Color / Size)
        variant_name = item.color
        if item.size:
            variant_name += f" / {item.size}"
        
        style_groups[style]['variants'].append({
            'variant_name': variant_name,
            'variant_id': item.variant_id,
            'qty_hilo': item.qty_hilo,
            'qty_kailua': item.qty_kailua,
            'qty_kapaa': item.qty_kapaa,
            'qty_wailuku': item.qty_wailuku
        })
    
    # Summary totals at top
    summary = order_manager.get_order_summary(selected_brand)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Styles", len(style_groups))
    with col2:
        st.metric("Hilo Total", summary['store_totals']['Hilo'])
    with col3:
        st.metric("Kailua Total", summary['store_totals']['Kailua'])
    with col4:
        st.metric("Kapaa Total", summary['store_totals']['Kapaa'])
    with col5:
        st.metric("Wailuku Total", summary['store_totals']['Wailuku'])
    
    st.markdown("---")
    st.markdown("**Order Sheet - Template Format:**")
    st.caption("Style-based rows with variants as columns (matching Excel export format)")
    
    # Create the template-style display
    for style_number, style_data in sorted(style_groups.items()):
        
        # Style header row
        st.markdown(f"### {style_number}")
        st.caption(f"**Description:** {style_data['description'][:60]}...")
        
        # Variants table for this style
        if style_data['variants']:
            # Get all variants for this style
            variants = style_data['variants']
            
            # Create columns: Variant name + 4 stores + Total + Actions
            cols = st.columns([2, 1, 1, 1, 1, 1, 1])
            
            # Headers
            with cols[0]:
                st.markdown("**Variant**")
            with cols[1]:
                st.markdown("**Hilo**")
            with cols[2]:
                st.markdown("**Kailua**")
            with cols[3]:
                st.markdown("**Kapaa**")
            with cols[4]:
                st.markdown("**Wailuku**")
            with cols[5]:
                st.markdown("**Total**")
            with cols[6]:
                st.markdown("**Action**")
            
            # Show each variant for this style
            style_totals = {'Hilo': 0, 'Kailua': 0, 'Kapaa': 0, 'Wailuku': 0}
            
            for idx, variant in enumerate(variants):
                cols = st.columns([2, 1, 1, 1, 1, 1, 1])
                
                with cols[0]:
                    st.write(variant['variant_name'])
                
                # Editable quantities
                with cols[1]:
                    new_hilo = st.number_input("", min_value=0, value=variant['qty_hilo'], 
                                              key=f"hilo_{style_number}_{idx}_{variant['variant_id']}")
                
                with cols[2]:
                    new_kailua = st.number_input("", min_value=0, value=variant['qty_kailua'], 
                                                key=f"kailua_{style_number}_{idx}_{variant['variant_id']}")
                
                with cols[3]:
                    new_kapaa = st.number_input("", min_value=0, value=variant['qty_kapaa'], 
                                               key=f"kapaa_{style_number}_{idx}_{variant['variant_id']}")
                
                with cols[4]:
                    new_wailuku = st.number_input("", min_value=0, value=variant['qty_wailuku'], 
                                                 key=f"wailuku_{style_number}_{idx}_{variant['variant_id']}")
                
                with cols[5]:
                    variant_total = new_hilo + new_kailua + new_kapaa + new_wailuku
                    st.write(f"**{variant_total}**")
                
                with cols[6]:
                    if st.button("🗑️", key=f"remove_{style_number}_{idx}_{variant['variant_id']}"):
                        order_manager.remove_variant_from_order(variant['variant_id'], selected_brand)
                        st.success(f"Removed variant")
                        st.rerun()
                
                # Update quantities if changed
                if (new_hilo != variant['qty_hilo'] or new_kailua != variant['qty_kailua'] or 
                    new_kapaa != variant['qty_kapaa'] or new_wailuku != variant['qty_wailuku']):
                    order_manager.update_variant_quantities(
                        variant['variant_id'], 
                        selected_brand, 
                        {
                            'Hilo': new_hilo,
                            'Kailua': new_kailua,
                            'Kapaa': new_kapaa,
                            'Wailuku': new_wailuku
                        }
                    )
                
                # Track style totals
                style_totals['Hilo'] += new_hilo
                style_totals['Kailua'] += new_kailua
                style_totals['Kapaa'] += new_kapaa
                style_totals['Wailuku'] += new_wailuku
            
            # Style totals row
            cols = st.columns([2, 1, 1, 1, 1, 1, 1])
            with cols[0]:
                st.markdown("**Style Total**")
            with cols[1]:
                st.markdown(f"**{style_totals['Hilo']}**")
            with cols[2]:
                st.markdown(f"**{style_totals['Kailua']}**")
            with cols[3]:
                st.markdown(f"**{style_totals['Kapaa']}**")
            with cols[4]:
                st.markdown(f"**{style_totals['Wailuku']}**")
            with cols[5]:
                total = sum(style_totals.values())
                st.markdown(f"**{total}**")
            with cols[6]:
                if st.button("🗑️ Remove Style", key=f"remove_style_{style_number}"):
                    # Remove all variants for this style
                    for variant in variants:
                        order_manager.remove_variant_from_order(variant['variant_id'], selected_brand)
                    st.success(f"Removed entire style {style_number}")
                    st.rerun()
        
        st.markdown("---")
    
    # Export actions
    st.markdown("### 5️⃣ Export Order Sheets")
    st.markdown("**Generate separate sheets for each store plus a summary sheet**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Generate Multi-Store Excel", type="primary"):
            excel_file = order_manager.export_order_sheet_excel(selected_brand)
            
            if excel_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                filename = f"{selected_brand.replace(' ', '_')}_Multi_Store_Order_{timestamp}.xlsx"
                
                st.download_button(
                    label="📥 Download Multi-Store Order Sheets",
                    data=excel_file,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.success("✅ Multi-store order sheets generated!")
                st.info("📋 Includes: Summary + Hilo + Kailua + Kapaa + Wailuku sheets")
            else:
                st.error("Failed to generate order sheets")
    
    with col2:
        if st.button("🗑️ Clear Order Sheet"):
            order_manager.clear_brand_selections(selected_brand)
            st.success(f"Cleared {selected_brand} order sheet")
            st.rerun()
    
    with col3:
        if st.button("📋 Copy Summary"):
            total_units = sum(summary['store_totals'].values())
            summary_text = f"{selected_brand} Order Summary:\nTotal Styles: {len(style_groups)}\nTotal Units: {total_units}\nHilo: {summary['store_totals']['Hilo']}\nKailua: {summary['store_totals']['Kailua']}\nKapaa: {summary['store_totals']['Kapaa']}\nWailuku: {summary['store_totals']['Wailuku']}"
            
            st.text_area(
                "Summary to copy:",
                value=summary_text,
                height=150,
                key="summary_copy"
            )
