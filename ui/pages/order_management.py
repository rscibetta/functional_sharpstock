"""
SharpStock Order Management Page
Generate and manage order sheets for suppliers
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

from models.data_models import ProductInsight, OrderSheetItem
from ui.components import (
    sharpstock_page_header,
    sharpstock_metric_card_enhanced,
    sharpstock_alert_banner,
    sharpstock_enhanced_table,
    sharpstock_status_indicator
)

def display_order_management_page():
    """Main order management page"""
    
    sharpstock_page_header(
        "📋 Order Management",
        "Generate smart order sheets for your suppliers",
        show_back_button=True
    )
    
    insights = st.session_state.get('insights', [])
    orders_df = st.session_state.get('recent_orders_df', pd.DataFrame())
    inventory_df = st.session_state.get('inventory_df', pd.DataFrame())
    location_config = st.session_state.get('location_config', {})
    
    if not insights:
        sharpstock_alert_banner("No analysis data available. Please run analysis first.", "warning")
        return
    
    # Initialize order manager
    if 'order_manager' not in st.session_state:
        from order_management.order_sheet_manager import OrderSheetManager
        st.session_state['order_manager'] = OrderSheetManager(location_config)
    
    order_manager = st.session_state['order_manager']
    
    # Show order management interface
    _show_brand_selection(insights, orders_df, inventory_df, location_config, order_manager)

def _show_brand_selection(insights: List[ProductInsight], orders_df: pd.DataFrame, 
                         inventory_df: pd.DataFrame, location_config: Dict[int, str], order_manager):
    """Show brand selection and order generation interface"""
    
    # Get available brands
    available_brands = sorted(list(set([i.vendor for i in insights if i.vendor not in ['Unknown', '', 'nan']])))
    
    if not available_brands:
        sharpstock_alert_banner("No brands found in the analysis data", "warning")
        return
    
    # Brand selection section
    st.markdown("### 🏷️ Brand Selection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_brand = st.selectbox(
            "Choose brand for order sheet:",
            available_brands,
            key="order_brand_selector",
            help="Select the brand/supplier you want to create an order sheet for"
        )
    
    with col2:
        st.metric("Available Brands", len(available_brands))
    
    if selected_brand:
        _show_brand_analysis(selected_brand, insights, orders_df, inventory_df, location_config, order_manager)

def _show_brand_analysis(brand: str, insights: List[ProductInsight], orders_df: pd.DataFrame,
                        inventory_df: pd.DataFrame, location_config: Dict[int, str], order_manager):
    """Show analysis for selected brand"""
    
    # Filter insights for selected brand
    brand_insights = [i for i in insights if i.vendor == brand]
    
    if not brand_insights:
        sharpstock_alert_banner(f"No products found for {brand}", "warning")
        return
    
    # Brand overview
    st.markdown("---")
    st.markdown(f"### 📊 {brand} Analysis")
    
    _show_brand_metrics(brand, brand_insights)
    _show_reorder_candidates(brand, brand_insights, orders_df, inventory_df, location_config, order_manager)
    _show_current_order_sheet(brand, order_manager, location_config)

def _show_brand_metrics(brand: str, brand_insights: List[ProductInsight]):
    """Show key metrics for the selected brand"""
    
    total_products = len(brand_insights)
    critical_alerts = len([i for i in brand_insights if i.reorder_priority == 'CRITICAL'])
    high_alerts = len([i for i in brand_insights if i.reorder_priority == 'HIGH'])
    medium_alerts = len([i for i in brand_insights if i.reorder_priority == 'MEDIUM'])
    
    trending_up = len([i for i in brand_insights if 'Trending' in i.trend_classification])
    total_recommended = sum([i.recommended_qty for i in brand_insights if i.reorder_priority in ['CRITICAL', 'HIGH', 'MEDIUM']])
    total_current_inventory = sum([i.current_inventory for i in brand_insights])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sharpstock_metric_card_enhanced(
            "Total Products",
            str(total_products),
            f"{trending_up} trending up",
            "📦",
            "primary"
        )
    
    with col2:
        alert_color = "error" if critical_alerts > 0 else "warning" if high_alerts > 0 else "success"
        sharpstock_metric_card_enhanced(
            "Reorder Alerts",
            str(critical_alerts + high_alerts + medium_alerts),
            f"{critical_alerts} critical, {high_alerts} high",
            "🚨",
            alert_color
        )
    
    with col3:
        sharpstock_metric_card_enhanced(
            "Recommended Units",
            f"{total_recommended:,}",
            "Total units to order",
            "🛒",
            "primary"
        )
    
    with col4:
        sharpstock_metric_card_enhanced(
            "Current Inventory",
            f"{total_current_inventory:,}",
            "Total units in stock",
            "📊",
            "success"
        )

def _show_reorder_candidates(brand: str, brand_insights: List[ProductInsight], orders_df: pd.DataFrame,
                           inventory_df: pd.DataFrame, location_config: Dict[int, str], order_manager):
    """Show products that need reordering for this brand"""
    
    st.markdown("### 🎯 Reorder Candidates")
    
    # Filter for products that need reordering
    reorder_candidates = [i for i in brand_insights if i.reorder_priority in ['CRITICAL', 'HIGH', 'MEDIUM']]
    
    if not reorder_candidates:
        sharpstock_alert_banner(f"No products currently need reordering for {brand}", "success")
        _show_all_brand_products(brand, brand_insights[:10])  # Show top 10 for reference
        return
    
    # Priority filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        priority_filter = st.selectbox(
            "🎚️ Priority Filter",
            ["All", "CRITICAL", "HIGH", "MEDIUM"],
            key="order_priority_filter"
        )
    
    with col2:
        timing_filter = st.selectbox(
            "⏰ Timing Filter", 
            ["All", "Order Now", "Order This Week", "Monitor"],
            key="order_timing_filter"
        )
    
    with col3:
        sort_by = st.selectbox(
            "📊 Sort By",
            ["Priority", "Daily Demand", "Recommended Qty", "Style Number"],
            key="order_sort_filter"
        )
    
    # Apply filters
    filtered_candidates = reorder_candidates
    if priority_filter != "All":
        filtered_candidates = [i for i in filtered_candidates if i.reorder_priority == priority_filter]
    if timing_filter != "All":
        filtered_candidates = [i for i in filtered_candidates if i.reorder_timing == timing_filter]
    
    # Apply sorting
    if sort_by == "Priority":
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        filtered_candidates.sort(key=lambda x: priority_order.get(x.reorder_priority, 4))
    elif sort_by == "Daily Demand":
        filtered_candidates.sort(key=lambda x: x.recent_daily_demand, reverse=True)
    elif sort_by == "Recommended Qty":
        filtered_candidates.sort(key=lambda x: x.recommended_qty, reverse=True)
    elif sort_by == "Style Number":
        filtered_candidates.sort(key=lambda x: x.style_number)
    
    if not filtered_candidates:
        sharpstock_alert_banner("No products match the selected filters", "info")
        return
    
    st.markdown(f"**📋 {len(filtered_candidates)} products need reordering:**")
    
    # Display products with enhanced interface
    for idx, insight in enumerate(filtered_candidates[:20]):  # Limit to 20 for performance
        _display_reorder_candidate(insight, idx, orders_df, inventory_df, location_config, order_manager, brand)

def _display_reorder_candidate(insight: ProductInsight, idx: int, orders_df: pd.DataFrame,
                              inventory_df: pd.DataFrame, location_config: Dict[int, str], 
                              order_manager, brand: str):
    """Display individual reorder candidate with actions"""
    
    with st.container():
        # Product header
        col1, col2, col3, col4, col5, col6 = st.columns([1.5, 2.5, 1, 1, 1, 1])
        
        with col1:
            # Priority badge
            priority_colors = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡', 
                'LOW': '🟢'
            }
            priority_icon = priority_colors.get(insight.reorder_priority, '⚪')
            
            if st.button(
                f"{priority_icon} {insight.style_number}",
                key=f"style_{brand}_{idx}_{insight.product_id}",
                help="Click to view product variants"
            ):
                st.session_state['selected_style_for_order'] = insight
                st.rerun()
        
        with col2:
            desc = insight.description[:35] + "..." if len(insight.description) > 35 else insight.description
            st.markdown(f"**{desc}**")
            st.caption(f"{insight.reorder_priority} - {insight.reorder_timing}")
        
        with col3:
            st.metric("Daily Demand", f"{insight.recent_daily_demand:.1f}")
        
        with col4:
            inventory_color = "🔴" if insight.current_inventory < 10 else "🟡" if insight.current_inventory < 30 else "🟢"
            st.metric("Stock", f"{insight.current_inventory:,}")
            st.caption(f"{inventory_color}")
        
        with col5:
            st.metric("Recommended", f"{insight.recommended_qty:,}")
        
        with col6:
            # Quick add button
            if st.button("➕ Add", key=f"add_{brand}_{idx}_{insight.product_id}", type="secondary"):
                _quick_add_product_to_order(insight, brand, order_manager, orders_df, inventory_df, location_config)
        
        # Show expanded details if this is the selected style
        if st.session_state.get('selected_style_for_order') and st.session_state['selected_style_for_order'].product_id == insight.product_id:
            _show_variant_breakdown(insight, orders_df, inventory_df, location_config, order_manager, brand)
        
        if idx < 19:  # Don't show divider after last item
            st.markdown("---")

def _show_variant_breakdown(insight: ProductInsight, orders_df: pd.DataFrame, inventory_df: pd.DataFrame,
                           location_config: Dict[int, str], order_manager, brand: str):
    """Show variant breakdown for selected product"""
    
    st.markdown(f"#### 🔍 Variant Breakdown - {insight.style_number}")
    
    # Back button
    if st.button("← Back to Product List", key="back_to_products"):
        st.session_state.pop('selected_style_for_order', None)
        st.rerun()
    
    # Get variants for this product
    product_variants = inventory_df[inventory_df['product_id'] == insight.product_id]
    
    if product_variants.empty:
        st.warning("No variant data found for this product")
        return
    
    # Product info
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📋 Product Information**")
        st.write(f"**Description:** {insight.description}")
        st.write(f"**Brand:** {insight.vendor}")
        st.write(f"**Priority:** {insight.reorder_priority}")
        st.write(f"**Timing:** {insight.reorder_timing}")
    
    with col2:
        st.markdown("**📊 Performance Metrics**")
        st.write(f"**Daily Demand:** {insight.recent_daily_demand:.1f} units")
        st.write(f"**Total Recommended:** {insight.recommended_qty:,} units")
        st.write(f"**Current Inventory:** {insight.current_inventory:,} units")
        st.write(f"**Trend:** {insight.trend_classification}")
    
    # Variant table
    st.markdown("**🎨 Available Variants:**")
    
    variant_data = []
    for _, variant in product_variants.iterrows():
        variant_info = {
            'Color': variant.get('color', 'Unknown'),
            'Size': variant.get('size', 'Unknown'), 
            'Total Inventory': variant.get('total_inventory', 0),
            'Hilo': variant.get('inventory_hilo', 0),
            'Kailua': variant.get('inventory_kailua', 0),
            'Kapaa': variant.get('inventory_kapaa', 0),
            'Wailuku': variant.get('inventory_wailuku', 0)
        }
        variant_data.append(variant_info)
    
    if variant_data:
        sharpstock_enhanced_table(variant_data, f"Variants for {insight.style_number}")
    
    # Smart add button
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧠 Add All Variants (Smart Recommendations)", type="primary", key=f"smart_add_{insight.product_id}"):
            _smart_add_all_variants(insight, brand, order_manager, orders_df, inventory_df, location_config)
    
    with col2:
        if st.button("📊 View Detailed Analysis", key=f"detail_analysis_{insight.product_id}"):
            st.session_state['selected_product_id'] = insight.product_id
            st.session_state['selected_style_number'] = insight.style_number
            st.session_state['current_page'] = 'trends'
            st.rerun()

def _quick_add_product_to_order(insight: ProductInsight, brand: str, order_manager, 
                               orders_df: pd.DataFrame, inventory_df: pd.DataFrame, 
                               location_config: Dict[int, str]):
    """Quick add product to order with basic recommendations"""
    
    # Use existing smart recommendations function
    from order_management.smart_recommendations import add_all_variants_for_product_with_smart_recommendations
    
    added = add_all_variants_for_product_with_smart_recommendations(
        insight.product_id,
        insight.style_number,
        brand,
        orders_df,
        inventory_df,
        location_config,
        order_manager,
        insight
    )
    
    if added > 0:
        total_units = sum([
            item.qty_hilo + item.qty_kailua + item.qty_kapaa + item.qty_wailuku
            for item in order_manager.selected_items.get(brand, [])
            if item.product_id == insight.product_id
        ])
        st.success(f"✅ Added {added} variants for {insight.style_number} ({total_units} total units)")
        st.rerun()
    else:
        st.warning("⚠️ No variants found or already added")

def _smart_add_all_variants(insight: ProductInsight, brand: str, order_manager,
                           orders_df: pd.DataFrame, inventory_df: pd.DataFrame,
                           location_config: Dict[int, str]):
    """Smart add all variants with AI recommendations"""
    
    _quick_add_product_to_order(insight, brand, order_manager, orders_df, inventory_df, location_config)

def _show_all_brand_products(brand: str, brand_insights: List[ProductInsight]):
    """Show all products for brand when no reorders needed"""
    
    st.markdown("**📋 All Products for Reference:**")
    
    for idx, insight in enumerate(brand_insights):
        col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
        
        with col1:
            st.write(f"**{insight.style_number}**")
        
        with col2:
            desc = insight.description[:40] + "..." if len(insight.description) > 40 else insight.description
            st.write(desc)
        
        with col3:
            st.write(f"Stock: {insight.current_inventory:,}")
        
        with col4:
            trend_icon = "📈" if 'Trending' in insight.trend_classification else "📊"
            st.write(f"{trend_icon}")
        
        if idx < len(brand_insights) - 1:
            st.markdown("---")

def _show_current_order_sheet(brand: str, order_manager, location_config: Dict[int, str]):
    """Show current order sheet for the selected brand"""
    
    current_items = order_manager.selected_items.get(brand, [])
    
    if not current_items:
        return
    
    st.markdown("---")
    st.markdown(f"### 📋 Current Order Sheet - {brand}")
    
    # Order summary
    summary = order_manager.get_order_summary(brand)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        sharpstock_metric_card_enhanced(
            "Styles",
            str(len(set(item.style_number for item in current_items))),
            "Unique products",
            "👕",
            "primary"
        )
    
    with col2:
        sharpstock_metric_card_enhanced(
            "Hilo Total",
            str(summary['store_totals']['Hilo']),
            "Units for Hilo",
            "🏪",
            "primary"
        )
    
    with col3:
        sharpstock_metric_card_enhanced(
            "Kailua Total",
            str(summary['store_totals']['Kailua']),
            "Units for Kailua",
            "🏪", 
            "primary"
        )
    
    with col4:
        sharpstock_metric_card_enhanced(
            "Other Stores",
            str(summary['store_totals']['Kapaa'] + summary['store_totals']['Wailuku']),
            "Kapaa + Wailuku",
            "🏪",
            "primary"
        )
    
    with col5:
        total_units = sum(summary['store_totals'].values())
        sharpstock_metric_card_enhanced(
            "Grand Total",
            f"{total_units:,}",
            "Total units",
            "📦",
            "success"
        )
    
    # Order sheet preview
    _show_order_sheet_preview(brand, current_items, order_manager)
    
    # Export options
    _show_export_options(brand, order_manager, summary)

def _show_order_sheet_preview(brand: str, current_items: List, order_manager):
    """Show preview of current order sheet"""
    
    st.markdown("#### 📋 Order Sheet Preview")
    
    # Group by style for display
    style_groups = {}
    for item in current_items:
        style = item.style_number
        if style not in style_groups:
            style_groups[style] = {
                'description': item.description,
                'items': []
            }
        style_groups[style]['items'].append(item)
    
    # Show each style group
    for style_number, style_data in sorted(style_groups.items()):
        with st.expander(f"📦 {style_number} - {style_data['description'][:50]}...", expanded=False):
            
            # Style totals
            style_totals = {
                'Hilo': sum(item.qty_hilo for item in style_data['items']),
                'Kailua': sum(item.qty_kailua for item in style_data['items']),
                'Kapaa': sum(item.qty_kapaa for item in style_data['items']),
                'Wailuku': sum(item.qty_wailuku for item in style_data['items'])
            }
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Hilo", style_totals['Hilo'])
            with col2:
                st.metric("Kailua", style_totals['Kailua'])
            with col3:
                st.metric("Kapaa", style_totals['Kapaa'])
            with col4:
                st.metric("Wailuku", style_totals['Wailuku'])
            with col5:
                total = sum(style_totals.values())
                st.metric("Total", total)
            
            # Variant details
            if len(style_data['items']) > 1:
                st.markdown("**Variants:**")
                variant_data = []
                for item in style_data['items']:
                    variant_data.append({
                        'Color': item.color,
                        'Size': item.size,
                        'Hilo': item.qty_hilo,
                        'Kailua': item.qty_kailua,
                        'Kapaa': item.qty_kapaa,
                        'Wailuku': item.qty_wailuku,
                        'Total': item.qty_hilo + item.qty_kailua + item.qty_kapaa + item.qty_wailuku
                    })
                
                sharpstock_enhanced_table(variant_data, f"Variants for {style_number}")
            
            # Remove style button
            if st.button(f"🗑️ Remove {style_number}", key=f"remove_style_{style_number}"):
                # Remove all variants for this style
                for item in style_data['items']:
                    order_manager.remove_variant_from_order(item.variant_id, brand)
                st.success(f"Removed {style_number} from order sheet")
                st.rerun()

def _show_export_options(brand: str, order_manager, summary: Dict):
    """Show export options for order sheet"""
    
    st.markdown("#### 📤 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Generate Excel Sheets", type="primary", use_container_width=True):
            excel_file = order_manager.export_order_sheet_excel(brand)
            
            if excel_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                filename = f"{brand.replace(' ', '_')}_Order_Sheets_{timestamp}.xlsx"
                
                st.download_button(
                    label="📥 Download Multi-Store Order Sheets",
                    data=excel_file,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel"
                )
                
                st.success("✅ Excel order sheets generated!")
                st.info("📋 Includes: Summary + Individual store sheets")
            else:
                st.error("❌ Failed to generate order sheets")
    
    with col2:
        if st.button("📧 Email to Supplier", type="secondary", use_container_width=True):
            _show_email_preview(brand, summary)
    
    with col3:
        if st.button("🗑️ Clear Order Sheet", type="secondary", use_container_width=True):
            if st.button("⚠️ Confirm Clear", key="confirm_clear"):
                order_manager.clear_brand_selections(brand)
                st.success(f"Cleared {brand} order sheet")
                st.rerun()

def _show_email_preview(brand: str, summary: Dict):
    """Show email preview for supplier"""
    
    total_units = sum(summary['store_totals'].values())
    
    email_content = f"""
Subject: Order Request - {brand} ({datetime.now().strftime('%B %d, %Y')})

Dear {brand} Team,

Please prepare the following order for SharpStock:

Order Summary:
- Total Styles: {summary['total_brands']}
- Total Units: {total_units:,}

Store Distribution:
- Hilo: {summary['store_totals']['Hilo']} units
- Kailua: {summary['store_totals']['Kailua']} units  
- Kapaa: {summary['store_totals']['Kapaa']} units
- Wailuku: {summary['store_totals']['Wailuku']} units

Please find detailed order sheets attached.

Expected delivery: As per usual terms
Contact: [Your contact information]

Best regards,
SharpStock Team
    """
    
    st.text_area(
        "📧 Email Preview (Copy and customize as needed):",
        email_content,
        height=300,
        key="email_preview"
    )

def show_order_management_summary():
    """Show order management summary widget for other pages"""
    
    if 'order_manager' not in st.session_state:
        return
    
    order_manager = st.session_state['order_manager']
    
    if not order_manager.selected_items:
        return
    
    total_brands = len(order_manager.selected_items)
    total_items = sum(len(items) for items in order_manager.selected_items.values())
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sharpstock_alert_banner(
            f"📋 **{total_items} items** in order sheets across {total_brands} brands",
            "info"
        )
    
    with col2:
        if st.button("View Orders", type="primary"):
            st.session_state['current_page'] = 'orders'
            st.rerun()

# Helper functions for order management
def get_reorder_summary_by_brand(insights: List[ProductInsight]) -> Dict[str, Dict]:
    """Get reorder summary organized by brand"""
    
    brand_summary = {}
    
    for insight in insights:
        brand = insight.vendor
        if brand not in brand_summary:
            brand_summary[brand] = {
                'total_products': 0,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'total_recommended': 0,
                'trending_up': 0
            }
        
        brand_summary[brand]['total_products'] += 1
        brand_summary[brand]['total_recommended'] += insight.recommended_qty
        
        if insight.reorder_priority == 'CRITICAL':
            brand_summary[brand]['critical'] += 1
        elif insight.reorder_priority == 'HIGH':
            brand_summary[brand]['high'] += 1
        elif insight.reorder_priority == 'MEDIUM':
            brand_summary[brand]['medium'] += 1
        
        if 'Trending' in insight.trend_classification:
            brand_summary[brand]['trending_up'] += 1
    
    return brand_summary

def calculate_order_sheet_totals(order_manager) -> Dict[str, Any]:
    """Calculate totals across all order sheets"""
    
    totals = {
        'total_brands': 0,
        'total_styles': 0,
        'total_variants': 0,
        'total_units': 0,
        'store_totals': {'Hilo': 0, 'Kailua': 0, 'Kapaa': 0, 'Wailuku': 0}
    }
    
    for brand, items in order_manager.selected_items.items():
        if items:
            totals['total_brands'] += 1
            totals['total_styles'] += len(set(item.style_number for item in items))
            totals['total_variants'] += len(items)
            
            for item in items:
                totals['total_units'] += item.qty_hilo + item.qty_kailua + item.qty_kapaa + item.qty_wailuku
                totals['store_totals']['Hilo'] += item.qty_hilo
                totals['store_totals']['Kailua'] += item.qty_kailua
                totals['store_totals']['Kapaa'] += item.qty_kapaa
                totals['store_totals']['Wailuku'] += item.qty_wailuku
    
    return totals
