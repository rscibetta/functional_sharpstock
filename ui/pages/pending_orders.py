"""
SharpStock Pending Orders Page
Track and manage orders that haven't been received yet
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any

from models.data_models import PendingOrder, UserProfile
from ui.components import (
    sharpstock_page_header,
    sharpstock_metric_card_enhanced,
    sharpstock_alert_banner,
    sharpstock_enhanced_table,
    create_sharpstock_chart_enhanced
)

def display_pending_orders_page():
    """Main pending orders page"""
    
    sharpstock_page_header(
        "📦 Pending Orders Management",
        "Track orders placed but not yet received",
        show_back_button=True
    )
    
    user_profile = st.session_state.get('user_profile')
    location_config = st.session_state.get('location_config', {})
    
    if not user_profile:
        sharpstock_alert_banner("Please complete your profile setup first.", "warning")
        return
    
    # Initialize pending order manager
    try:
        from pending_orders.pending_order_manager import PendingOrderManager
        pending_manager = PendingOrderManager(user_profile, location_config)
    except ImportError:
        sharpstock_alert_banner("Pending orders feature not available. Please check system configuration.", "error")
        return
    
    # Main pending orders interface
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Upload Orders",
        "📋 Current Orders",
        "📊 Analytics",
        "💡 Help & Settings"
    ])
    
    with tab1:
        _show_upload_interface(pending_manager, location_config)
    
    with tab2:
        _show_current_pending_orders(pending_manager)
    
    with tab3:
        _show_pending_orders_analytics(pending_manager)
    
    with tab4:
        _show_help_and_settings()

def _show_upload_interface(pending_manager, location_config: Dict[int, str]):
    """Upload interface for pending order sheets"""
    
    st.markdown("### 📤 Upload Pending Order Sheets")
    st.caption("Upload Excel order sheets to track items you've ordered but haven't received yet")
    
    # Upload section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📄 Select Order Sheet",
            type=['xlsx', 'xls'],
            help="Upload order sheets in Excel format (same format as SharpStock generates)",
            key="pending_orders_upload"
        )
    
    with col2:
        if uploaded_file:
            st.success("✅ File selected")
            st.caption(f"File: {uploaded_file.name}")
            st.caption(f"Size: {uploaded_file.size / 1024:.1f} KB")
    
    if uploaded_file is not None:
        # Configuration options
        st.markdown("#### ⚙️ Order Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            expected_arrival = st.date_input(
                "📅 Expected Arrival Date",
                value=datetime.now() + timedelta(days=14),
                min_value=datetime.now().date(),
                help="When do you expect these orders to arrive?"
            )
        
        with col2:
            brand_override = st.text_input(
                "🏷️ Brand Override (optional)",
                placeholder="Leave blank to auto-detect",
                help="Override brand if not detected from filename"
            )
        
        with col3:
            confidence_level = st.slider(
                "🎯 Confidence Level",
                min_value=0.5,
                max_value=1.0,
                value=0.9,
                step=0.1,
                help="How confident are you this order will arrive as expected?"
            )
        
        # Parse button
        if st.button("🔍 Parse Order Sheet", type="primary", use_container_width=True):
            _process_uploaded_order_sheet(
                pending_manager, uploaded_file, expected_arrival, brand_override, confidence_level
            )

def _process_uploaded_order_sheet(pending_manager, uploaded_file, expected_arrival, brand_override, confidence_level):
    """Process uploaded order sheet"""
    
    with st.spinner("📊 Analyzing order sheet..."):
        try:
            # Parse the uploaded file
            pending_orders = pending_manager.parse_order_sheet_upload(uploaded_file)
            
            if pending_orders:
                # Update order details
                for order in pending_orders:
                    order.expected_arrival = datetime.combine(expected_arrival, datetime.min.time())
                    if brand_override:
                        order.brand = brand_override
                    elif not order.brand:
                        # Try to detect from filename
                        filename = uploaded_file.name.lower()
                        for brand_keyword in ['nike', 'adidas', 'puma', 'vans', 'converse', 'birkenstock']:
                            if brand_keyword in filename:
                                order.brand = brand_keyword.title()
                                break
                
                # Show preview and save
                _show_parsed_orders_preview(pending_manager, pending_orders)
                
            else:
                sharpstock_alert_banner(
                    "No valid order data found. Please check your file format.",
                    "warning"
                )
        
        except Exception as e:
            sharpstock_alert_banner(f"Error parsing order sheet: {e}", "error")

def _show_parsed_orders_preview(pending_manager, pending_orders: List[PendingOrder]):
    """Show preview of parsed orders before saving"""
    
    st.markdown("---")
    st.markdown("### 🔍 Order Preview")
    
    # Summary metrics
    summary = pending_manager.get_pending_orders_summary(pending_orders)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sharpstock_metric_card_enhanced(
            "Total Items",
            str(summary['total_orders']),
            "Order line items",
            "📋",
            "primary"
        )
    
    with col2:
        sharpstock_metric_card_enhanced(
            "Total Units",
            f"{summary['total_units']:,}",
            "Units ordered",
            "📦",
            "primary"
        )
    
    with col3:
        sharpstock_metric_card_enhanced(
            "Unique Styles",
            str(summary['total_styles']),
            "Different products",
            "👕",
            "primary"
        )
    
    with col4:
        sharpstock_metric_card_enhanced(
            "Locations",
            str(len(summary['by_location'])),
            "Store destinations",
            "🏪",
            "primary"
        )
    
    # Breakdown tables
    col1, col2 = st.columns(2)
    
    with col1:
        if summary['by_location']:
            st.markdown("**📍 By Location:**")
            location_data = [
                {'Location': loc, 'Units': qty}
                for loc, qty in summary['by_location'].items()
            ]
            sharpstock_enhanced_table(location_data, "Location Breakdown")
    
    with col2:
        if summary['by_brand']:
            st.markdown("**🏷️ By Brand:**")
            brand_data = [
                {'Brand': brand, 'Units': qty}
                for brand, qty in summary['by_brand'].items()
            ]
            sharpstock_enhanced_table(brand_data, "Brand Breakdown")
    
    # Sample items
    with st.expander("📋 Sample Order Items", expanded=False):
        sample_data = []
        for order in pending_orders[:10]:  # Show first 10
            sample_data.append({
                'Style': order.style_number,
                'Variant': order.variant_info,
                'Location': order.location_name,
                'Quantity': order.quantity,
                'Brand': order.brand or 'Unknown',
                'Expected': order.expected_arrival.strftime('%Y-%m-%d')
            })
        
        if sample_data:
            sharpstock_enhanced_table(sample_data, f"Sample Items (showing 10 of {len(pending_orders)})")
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Save Orders", type="primary", use_container_width=True):
            if pending_manager.save_pending_orders(pending_orders):
                st.success(f"✅ Successfully saved {len(pending_orders)} pending orders!")
                st.session_state['pending_orders_uploaded'] = True
                st.rerun()
            else:
                st.error("❌ Failed to save pending orders")
    
    with col2:
        if st.button("🔄 Include in Analysis", type="primary", use_container_width=True):
            if pending_manager.save_pending_orders(pending_orders):
                st.session_state['pending_orders_uploaded'] = True
                st.session_state['trigger_reanalysis_with_pending'] = True
                st.success("✅ Orders saved and will be included in next analysis!")
                st.info("💡 Go to Business Intelligence to run updated analysis.")
            else:
                st.error("❌ Failed to save pending orders")
    
    with col3:
        if st.button("❌ Cancel", type="secondary", use_container_width=True):
            st.rerun()

def _show_current_pending_orders(pending_manager):
    """Show currently saved pending orders"""
    
    st.markdown("### 📋 Current Pending Orders")
    
    # Load current pending orders
    pending_orders = pending_manager.load_pending_orders()
    
    if not pending_orders:
        _show_no_pending_orders()
        return
    
    # Summary metrics
    summary = pending_manager.get_pending_orders_summary(pending_orders)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sharpstock_metric_card_enhanced(
            "Pending Units",
            f"{summary['total_units']:,}",
            "Total units on order",
            "📦",
            "primary"
        )
    
    with col2:
        sharpstock_metric_card_enhanced(
            "Pending Styles",
            str(summary['total_styles']),
            "Unique products",
            "👕",
            "primary"
        )
    
    with col3:
        # Calculate average arrival date
        arrival_dates = [order.expected_arrival for order in pending_orders]
        avg_arrival = min(arrival_dates) if arrival_dates else datetime.now()
        days_until = (avg_arrival.date() - datetime.now().date()).days
        
        sharpstock_metric_card_enhanced(
            "Next Arrival",
            f"{days_until} days",
            avg_arrival.strftime('%b %d'),
            "📅",
            "warning" if days_until < 7 else "primary"
        )
    
    with col4:
        # Count overdue orders
        overdue_count = len([o for o in pending_orders if o.expected_arrival.date() < datetime.now().date()])
        
        sharpstock_metric_card_enhanced(
            "Status",
            "Overdue" if overdue_count > 0 else "On Track",
            f"{overdue_count} overdue" if overdue_count > 0 else "All on schedule",
            "⚠️" if overdue_count > 0 else "✅",
            "warning" if overdue_count > 0 else "success"
        )
    
    # Show alerts for overdue orders
    if overdue_count > 0:
        sharpstock_alert_banner(
            f"⚠️ **{overdue_count} orders are overdue!** Expected arrival dates have passed.",
            "warning"
        )
    
    # Display orders by brand
    _show_pending_orders_by_brand(pending_orders)
    
    # Management actions
    _show_pending_orders_actions(pending_manager, pending_orders)

def _show_no_pending_orders():
    """Show when no pending orders exist"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: rgba(14, 165, 233, 0.1); border-radius: 12px; border: 1px solid rgba(14, 165, 233, 0.3);">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📦</div>
            <h2 style="color: #0EA5E9; margin-bottom: 1rem;">No Pending Orders</h2>
            <p style="color: #9CA3AF; font-size: 1.1rem;">Upload order sheets in the Upload tab to start tracking your pending inventory.</p>
        </div>
        """, unsafe_allow_html=True)

def _show_pending_orders_by_brand(pending_orders: List[PendingOrder]):
    """Display pending orders organized by brand"""
    
    st.markdown("---")
    st.markdown("### 🏷️ Orders by Brand")
    
    # Group by brand
    by_brand = {}
    for order in pending_orders:
        brand = order.brand or 'Unknown'
        if brand not in by_brand:
            by_brand[brand] = []
        by_brand[brand].append(order)
    
    # Display each brand
    for brand, brand_orders in by_brand.items():
        brand_units = sum(order.quantity for order in brand_orders)
        
        with st.expander(f"🏷️ {brand} ({len(brand_orders)} items, {brand_units:,} units)", expanded=True):
            
            # Brand summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Line Items", len(brand_orders))
            
            with col2:
                st.metric("Total Units", f"{brand_units:,}")
            
            with col3:
                earliest_arrival = min(order.expected_arrival for order in brand_orders)
                days_until = (earliest_arrival.date() - datetime.now().date()).days
                st.metric("Next Arrival", f"{days_until} days")
            
            # Brand orders table
            brand_data = []
            for order in brand_orders:
                status = "Overdue" if order.expected_arrival.date() < datetime.now().date() else "Pending"
                status_icon = "⚠️" if status == "Overdue" else "⏳"
                
                brand_data.append({
                    'Style': order.style_number,
                    'Variant': order.variant_info or 'All',
                    'Location': order.location_name,
                    'Quantity': order.quantity,
                    'Expected': order.expected_arrival.strftime('%Y-%m-%d'),
                    'Status': f"{status_icon} {status}",
                    'Notes': order.notes or ''
                })
            
            if brand_data:
                sharpstock_enhanced_table(brand_data, f"{brand} Order Details")

def _show_pending_orders_actions(pending_manager, pending_orders: List[PendingOrder]):
    """Show management actions for pending orders"""
    
    st.markdown("---")
    st.markdown("### 🔧 Management Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Include in Next Analysis", type="primary", use_container_width=True):
            st.session_state['trigger_reanalysis_with_pending'] = True
            st.success("✅ Pending orders will be included in next analysis")
            st.info("💡 Go to Business Intelligence and run analysis to see updated recommendations")
    
    with col2:
        if st.button("📊 Export Orders", type="secondary", use_container_width=True):
            _export_pending_orders(pending_orders)
    
    with col3:
        if st.button("✅ Mark as Received", type="secondary", use_container_width=True):
            _show_mark_received_interface(pending_manager, pending_orders)
    
    with col4:
        if st.button("🗑️ Clear All", type="secondary", use_container_width=True):
            if st.button("⚠️ Confirm Clear All", key="confirm_clear_all"):
                pending_manager.clear_pending_orders()
                st.success("✅ Cleared all pending orders")
                st.rerun()

def _export_pending_orders(pending_orders: List[PendingOrder]):
    """Export pending orders to CSV"""
    
    export_data = []
    for order in pending_orders:
        export_data.append({
            'Style Number': order.style_number,
            'Brand': order.brand,
            'Variant': order.variant_info,
            'Color': order.color,
            'Size': order.size,
            'Location': order.location_name,
            'Quantity': order.quantity,
            'Expected Arrival': order.expected_arrival.strftime('%Y-%m-%d'),
            'Status': 'Overdue' if order.expected_arrival.date() < datetime.now().date() else 'Pending',
            'Notes': order.notes
        })
    
    if export_data:
        csv = pd.DataFrame(export_data).to_csv(index=False)
        st.download_button(
            "📥 Download Pending Orders CSV",
            csv,
            f"pending_orders_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            key="export_pending_orders"
        )
        st.success("✅ Export ready for download")

def _show_mark_received_interface(pending_manager, pending_orders: List[PendingOrder]):
    """Interface to mark orders as received"""
    
    st.markdown("#### ✅ Mark Orders as Received")
    
    # Group by brand for easier selection
    by_brand = {}
    for order in pending_orders:
        brand = order.brand or 'Unknown'
        if brand not in by_brand:
            by_brand[brand] = []
        by_brand[brand].append(order)
    
    selected_brand = st.selectbox(
        "Select brand:",
        list(by_brand.keys()),
        key="mark_received_brand"
    )
    
    if selected_brand:
        brand_orders = by_brand[selected_brand]
        
        # Show orders for selection
        st.markdown(f"**Select {selected_brand} orders to mark as received:**")
        
        selected_orders = []
        for idx, order in enumerate(brand_orders):
            if st.checkbox(
                f"{order.style_number} - {order.variant_info} ({order.quantity} units to {order.location_name})",
                key=f"select_order_{idx}"
            ):
                selected_orders.append(order)
        
        if selected_orders:
            if st.button("✅ Mark Selected as Received", type="primary"):
                # Remove selected orders from pending
                for order in selected_orders:
                    pending_manager.remove_pending_order(order)
                
                st.success(f"✅ Marked {len(selected_orders)} orders as received")
                st.rerun()

def _show_pending_orders_analytics(pending_manager):
    """Show analytics for pending orders"""
    
    st.markdown("### 📊 Pending Orders Analytics")
    
    pending_orders = pending_manager.load_pending_orders()
    
    if not pending_orders:
        st.info("No pending orders data to analyze")
        return
    
    # Timeline analysis
    _show_arrival_timeline(pending_orders)
    
    # Location analysis
    _show_location_distribution(pending_orders)
    
    # Performance insights
    _show_pending_order_insights(pending_orders)

def _show_arrival_timeline(pending_orders: List[PendingOrder]):
    """Show timeline of expected arrivals"""
    
    st.markdown("#### 📅 Arrival Timeline")
    
    # Group by arrival date
    by_date = {}
    for order in pending_orders:
        date_key = order.expected_arrival.date()
        if date_key not in by_date:
            by_date[date_key] = []
        by_date[date_key].append(order)
    
    # Create timeline data
    timeline_data = []
    for date, date_orders in sorted(by_date.items()):
        total_units = sum(order.quantity for order in date_orders)
        status = "Overdue" if date < datetime.now().date() else "Upcoming"
        
        timeline_data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Orders': len(date_orders),
            'Units': total_units,
            'Status': status
        })
    
    if timeline_data:
        # Chart
        df_timeline = pd.DataFrame(timeline_data)
        fig = create_sharpstock_chart_enhanced(
            df_timeline,
            chart_type="bar",
            title="Expected Arrivals Timeline",
            x='Date',
            y='Units',
            color='Status',
            height=400
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Table
        sharpstock_enhanced_table(timeline_data, "Arrival Schedule")

def _show_location_distribution(pending_orders: List[PendingOrder]):
    """Show distribution of pending orders by location"""
    
    st.markdown("#### 📍 Distribution by Location")
    
    by_location = {}
    for order in pending_orders:
        location = order.location_name
        if location not in by_location:
            by_location[location] = {'orders': 0, 'units': 0, 'styles': set()}
        
        by_location[location]['orders'] += 1
        by_location[location]['units'] += order.quantity
        by_location[location]['styles'].add(order.style_number)
    
    if by_location:
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart of units by location
            location_units = [(loc, data['units']) for loc, data in by_location.items()]
            df_location = pd.DataFrame(location_units, columns=['Location', 'Units'])
            
            fig = create_sharpstock_chart_enhanced(
                df_location,
                chart_type="pie",
                title="Units by Location",
                values='Units',
                names='Location',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Location metrics
            for location, data in by_location.items():
                sharpstock_metric_card_enhanced(
                    location,
                    f"{data['units']:,}",
                    f"{data['orders']} orders, {len(data['styles'])} styles",
                    "🏪",
                    "primary"
                )

def _show_pending_order_insights(pending_orders: List[PendingOrder]):
    """Show insights about pending orders"""
    
    st.markdown("#### 💡 Insights")
    
    # Calculate insights
    total_orders = len(pending_orders)
    overdue_orders = [o for o in pending_orders if o.expected_arrival.date() < datetime.now().date()]
    upcoming_week = [o for o in pending_orders if 0 <= (o.expected_arrival.date() - datetime.now().date()).days <= 7]
    
    # Brand analysis
    by_brand = {}
    for order in pending_orders:
        brand = order.brand or 'Unknown'
        by_brand[brand] = by_brand.get(brand, 0) + order.quantity
    
    top_brand = max(by_brand.items(), key=lambda x: x[1]) if by_brand else ("Unknown", 0)
    
    # Display insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎯 Key Insights:**")
        
        if overdue_orders:
            st.warning(f"⚠️ {len(overdue_orders)} orders are overdue")
        
        if upcoming_week:
            st.info(f"📅 {len(upcoming_week)} orders arriving this week")
        
        st.success(f"🏷️ Top brand: {top_brand[0]} ({top_brand[1]:,} units)")
        
        # Average lead time
        if pending_orders:
            lead_times = [(order.expected_arrival.date() - datetime.now().date()).days for order in pending_orders]
            avg_lead_time = sum(lead_times) / len(lead_times)
            st.info(f"📊 Average lead time: {avg_lead_time:.0f} days")
    
    with col2:
        st.markdown("**📈 Recommendations:**")
        
        if len(overdue_orders) > total_orders * 0.2:
            st.error("🚨 High percentage of overdue orders - review supplier performance")
        
        if len(upcoming_week) > total_orders * 0.5:
            st.warning("📦 Many orders arriving soon - prepare receiving capacity")
        
        if len(set(order.brand for order in pending_orders)) > 10:
            st.info("🏷️ Many brands - consider consolidating suppliers")
        
        st.success("💡 Use pending orders in analysis for accurate reorder recommendations")

def _show_help_and_settings():
    """Show help information and settings"""
    
    st.markdown("### 💡 Help & Settings")
    
    # Help section
    with st.expander("📖 How Pending Orders Work", expanded=True):
        st.markdown("""
        **Pending Orders** help you track inventory you've ordered but haven't received yet.
        
        #### 🎯 Benefits:
        - **Avoid over-ordering** - Don't reorder items you've already ordered
        - **Better planning** - See projected inventory after pending orders arrive
        - **Accurate analysis** - Get recommendations that account for incoming stock
        
        #### 📤 How to Upload:
        1. **Export order sheets** from your vendors or use SharpStock-generated sheets
        2. **Upload the Excel file** in the Upload tab
        3. **Set expected arrival date** for the orders
        4. **Include in analysis** to get updated recommendations
        
        #### 🔄 Integration with Analysis:
        - Pending orders are added to your current inventory projections
        - Reorder recommendations account for incoming stock
        - Transfer suggestions consider pending inventory at each location
        """)
    
    # Settings section
    with st.expander("⚙️ Pending Orders Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            default_lead_time = st.number_input(
                "Default Lead Time (days)",
                min_value=1,
                max_value=90,
                value=14,
                help="Default expected arrival time for new orders"
            )
            
            auto_clear = st.checkbox(
                "Auto-clear overdue orders",
                value=False,
                help="Automatically remove orders when arrival date passes"
            )
        
        with col2:
            confidence_threshold = st.slider(
                "Confidence threshold for analysis",
                min_value=0.5,
                max_value=1.0,
                value=0.8,
                help="Minimum confidence level to include orders in analysis"
            )
            
            include_in_reorder = st.checkbox(
                "Include in reorder calculations",
                value=True,
                help="Factor pending orders into reorder recommendations"
            )
        
        if st.button("💾 Save Settings"):
            # Save settings to session state or user profile
            st.session_state['pending_orders_settings'] = {
                'default_lead_time': default_lead_time,
                'auto_clear': auto_clear,
                'confidence_threshold': confidence_threshold,
                'include_in_reorder': include_in_reorder
            }
            st.success("✅ Settings saved!")
    
    # Example formats
    with st.expander("📋 Supported File Formats", expanded=False):
        st.markdown("**Supported Excel formats:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Summary Format (Style-based):**")
            example_summary = {
                'Style Number': ['SHOE001', 'SHOE002', 'SHIRT001'],
                'Description': ['Running Shoe', 'Basketball Shoe', 'Cotton T-Shirt'],
                'Hilo': [5, 3, 8],
                'Kailua': [10, 7, 12],
                'Kapaa': [4, 2, 6],
                'Wailuku': [6, 5, 10]
            }
            st.dataframe(pd.DataFrame(example_summary), use_container_width=True)
        
        with col2:
            st.markdown("**Individual Store Format (Variant-based):**")
            example_variant = {
                'Style Number': ['SHOE001', 'SHOE001', 'SHOE002'],
                'Color': ['Black', 'White', 'Red'],
                'Size': ['9', '10', '9.5'],
                'Quantity': [3, 2, 4]
            }
            st.dataframe(pd.DataFrame(example_variant), use_container_width=True)

# Utility functions for pending orders
def show_pending_orders_widget():
    """Show pending orders widget for other pages"""
    
    if st.session_state.get('pending_orders_uploaded', False):
        try:
            from pending_orders.pending_order_manager import PendingOrderManager
            user_profile = st.session_state.get('user_profile')
            location_config = st.session_state.get('location_config', {})
            
            if user_profile and location_config:
                pending_manager = PendingOrderManager(user_profile, location_config)
                pending_orders = pending_manager.load_pending_orders()
                
                if pending_orders:
                    summary = pending_manager.get_pending_orders_summary(pending_orders)
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        sharpstock_alert_banner(
                            f"📦 **{summary['total_units']:,} units pending** across {summary['total_styles']} styles - included in analysis",
                            "info"
                        )
                    
                    with col2:
                        if st.button("Manage", type="primary"):
                            st.session_state['current_page'] = 'pending'
                            st.rerun()
        
        except Exception:
            pass  # Silently fail if pending orders not available
