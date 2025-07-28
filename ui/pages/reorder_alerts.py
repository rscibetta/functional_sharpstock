"""
SharpStock Reorder Alerts Page
Focused page for critical and high priority reorder recommendations
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any

from models.data_models import ProductInsight
from ui.components import (
    sharpstock_page_header,
    sharpstock_metric_card_enhanced,
    sharpstock_alert_banner,
    sharpstock_status_indicator,
    sharpstock_enhanced_table
)

def display_reorder_alerts_page():
    """Main reorder alerts page"""
    
    sharpstock_page_header(
        "🚨 Reorder Alerts",
        "Products requiring immediate attention",
        show_back_button=True
    )
    
    insights = st.session_state.get('insights', [])
    if not insights:
        sharpstock_alert_banner("No analysis data available. Please run analysis first.", "warning")
        return
    
    # Filter for alerts only
    alerts = [i for i in insights if i.reorder_priority in ['CRITICAL', 'HIGH']]
    
    if not alerts:
        _show_no_alerts()
        return
    
    # Show alerts overview
    _show_alerts_overview(alerts)
    
    # Show alert categories
    _show_alert_categories(alerts)

def _show_no_alerts():
    """Show when there are no alerts"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: rgba(16, 185, 129, 0.1); border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.3);">
            <div style="font-size: 4rem; margin-bottom: 1rem;">✅</div>
            <h2 style="color: #10B981; margin-bottom: 1rem;">All Good!</h2>
            <p style="color: #9CA3AF; font-size: 1.1rem;">No critical or high priority reorders needed at this time.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show medium priority items if any
    insights = st.session_state.get('insights', [])
    medium_priority = [i for i in insights if i.reorder_priority == 'MEDIUM']
    
    if medium_priority:
        st.markdown("---")
        st.markdown("### 🟡 Medium Priority Items")
        st.caption("Items to monitor for future ordering")
        
        _display_alert_list(medium_priority[:10], show_actions=False)

def _show_alerts_overview(alerts: List[ProductInsight]):
    """Show overview metrics for alerts"""
    
    critical_alerts = [i for i in alerts if i.reorder_priority == 'CRITICAL']
    high_alerts = [i for i in alerts if i.reorder_priority == 'HIGH']
    
    # Calculate totals
    total_recommended_qty = sum([i.recommended_qty for i in alerts])
    total_current_inventory = sum([i.current_inventory for i in alerts])
    avg_days_stockout = sum([i.days_until_stockout for i in alerts if i.days_until_stockout < 999]) / max(len([i for i in alerts if i.days_until_stockout < 999]), 1)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sharpstock_metric_card_enhanced(
            "Critical Alerts",
            str(len(critical_alerts)),
            "Need immediate ordering",
            "🔴",
            "error"
        )
    
    with col2:
        sharpstock_metric_card_enhanced(
            "High Priority",
            str(len(high_alerts)),
            "Order this week",
            "🟠",
            "warning"
        )
    
    with col3:
        sharpstock_metric_card_enhanced(
            "Total Units Needed",
            f"{total_recommended_qty:,}",
            f"Current: {total_current_inventory:,}",
            "📦",
            "primary"
        )
    
    with col4:
        sharpstock_metric_card_enhanced(
            "Avg Days to Stockout",
            f"{avg_days_stockout:.0f}",
            "For items at risk",
            "⏰",
            "warning" if avg_days_stockout < 30 else "primary"
        )
    
    # Show urgent banner if critical alerts exist
    if critical_alerts:
        sharpstock_alert_banner(
            f"🚨 **URGENT:** {len(critical_alerts)} products are critically low and need immediate ordering to avoid stockouts!",
            "error"
        )

def _show_alert_categories(alerts: List[ProductInsight]):
    """Show alerts organized by priority"""
    
    critical_alerts = [i for i in alerts if i.reorder_priority == 'CRITICAL']
    high_alerts = [i for i in alerts if i.reorder_priority == 'HIGH']
    
    # Tabs for different priority levels
    if critical_alerts:
        tab1, tab2 = st.tabs([
            f"🔴 Critical ({len(critical_alerts)})",
            f"🟠 High Priority ({len(high_alerts)})"
        ])
        
        with tab1:
            st.markdown("### 🚨 Critical Priority - Order Immediately")
            st.caption("These products are at risk of stockout within days")
            _display_alert_list(critical_alerts, priority="CRITICAL")
        
        with tab2:
            st.markdown("### ⚠️ High Priority - Order This Week")
            st.caption("These products should be ordered soon to maintain healthy inventory")
            _display_alert_list(high_alerts, priority="HIGH")
    
    elif high_alerts:
        st.markdown("### ⚠️ High Priority Items")
        st.caption("These products should be ordered soon")
        _display_alert_list(high_alerts, priority="HIGH")

def _display_alert_list(alerts: List[ProductInsight], priority: str = "", show_actions: bool = True):
    """Display list of alerts with enhanced formatting"""
    
    if not alerts:
        st.info("No items in this category")
        return
    
    # Sort by urgency (days until stockout, then by daily demand)
    sorted_alerts = sorted(alerts, key=lambda x: (x.days_until_stockout, -x.recent_daily_demand))
    
    # Enhanced display
    for idx, insight in enumerate(sorted_alerts):
        with st.container():
            # Create expandable alert card
            urgency_indicator = "🔥" if insight.days_until_stockout <= 7 else "⚠️" if insight.days_until_stockout <= 14 else "📅"
            
            with st.expander(
                f"{urgency_indicator} **{insight.style_number}** - {insight.description[:50]}... "
                f"({insight.recommended_qty:,} units needed)",
                expanded=idx == 0 if priority == "CRITICAL" else False
            ):
                
                # Alert details in columns
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**📊 Current Status**")
                    
                    # Current inventory with color coding
                    inv_color = "🔴" if insight.current_inventory < 10 else "🟡" if insight.current_inventory < 30 else "🟢"
                    st.metric("Current Inventory", f"{insight.current_inventory:,}", f"{inv_color}")
                    
                    days_color = "🔴" if insight.days_until_stockout <= 7 else "🟡" if insight.days_until_stockout <= 14 else "🟢"
                    stockout_text = f"{insight.days_until_stockout} days" if insight.days_until_stockout < 999 else "Well stocked"
                    st.metric("Days Until Stockout", stockout_text, f"{days_color}")
                
                with col2:
                    st.markdown("**📈 Performance Metrics**")
                    
                    st.metric("Daily Demand", f"{insight.recent_daily_demand:.1f}", 
                             f"vs {insight.historical_daily_demand:.1f} historical")
                    
                    trend_color = "📈" if insight.velocity_change > 0 else "📉" if insight.velocity_change < 0 else "➡️"
                    st.metric("Trend", insight.trend_classification, f"{trend_color} {insight.velocity_change:+.1f}%")
                
                with col3:
                    st.markdown("**🎯 Recommendation**")
                    
                    st.metric("Recommended Qty", f"{insight.recommended_qty:,}", insight.reorder_timing)
                    st.metric("Brand", insight.vendor, f"Lead time varies")
                
                # AI Reasoning
                st.markdown("**💡 AI Analysis**")
                st.info(insight.reasoning)
                
                # Action buttons if enabled
                if show_actions:
                    st.markdown("**⚡ Quick Actions**")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if st.button("📊 View Details", key=f"detail_{insight.product_id}_{idx}"):
                            st.session_state['selected_product_id'] = insight.product_id
                            st.session_state['selected_style_number'] = insight.style_number
                            st.session_state['current_page'] = 'trends'
                            st.rerun()
                    
                    with col2:
                        if st.button("🛒 Add to Order", key=f"order_{insight.product_id}_{idx}"):
                            _add_to_order_sheet(insight)
                    
                    with col3:
                        if st.button("📋 Copy Info", key=f"copy_{insight.product_id}_{idx}"):
                            copy_text = f"{insight.style_number}: {insight.recommended_qty} units - {insight.reorder_timing} - {insight.vendor}"
                            st.text_area("Copy this text:", copy_text, height=60, key=f"copy_text_{idx}")
                    
                    with col4:
                        if st.button("📞 Contact Supplier", key=f"contact_{insight.product_id}_{idx}"):
                            st.info(f"Contact {insight.vendor} for {insight.style_number}")

def _add_to_order_sheet(insight: ProductInsight):
    """Add product to order sheet"""
    
    # Initialize order sheet if not exists
    if 'order_sheet_items' not in st.session_state:
        st.session_state['order_sheet_items'] = []
    
    # Check if already added
    existing = any(item.get('product_id') == insight.product_id for item in st.session_state['order_sheet_items'])
    
    if existing:
        st.warning(f"⚠️ {insight.style_number} is already in your order sheet")
    else:
        # Add to order sheet
        order_item = {
            'product_id': insight.product_id,
            'style_number': insight.style_number,
            'description': insight.description,
            'vendor': insight.vendor,
            'recommended_qty': insight.recommended_qty,
            'priority': insight.reorder_priority,
            'reasoning': insight.reasoning,
            'added_from': 'reorder_alerts'
        }
        
        st.session_state['order_sheet_items'].append(order_item)
        st.success(f"✅ Added {insight.style_number} to order sheet ({insight.recommended_qty:,} units)")

def show_alerts_summary():
    """Show summary widget for other pages"""
    
    insights = st.session_state.get('insights', [])
    if not insights:
        return
    
    critical_count = len([i for i in insights if i.reorder_priority == 'CRITICAL'])
    high_count = len([i for i in insights if i.reorder_priority == 'HIGH'])
    
    if critical_count > 0 or high_count > 0:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            alert_text = f"🚨 {critical_count} critical alerts" if critical_count > 0 else f"⚠️ {high_count} high priority alerts"
            sharpstock_alert_banner(
                f"{alert_text} - Review your reorder recommendations",
                "error" if critical_count > 0 else "warning"
            )
        
        with col2:
            if st.button("View Alerts", type="primary"):
                st.session_state['current_page'] = 'reorder'
                st.rerun()

# Filter and search functions
def filter_alerts_by_vendor(alerts: List[ProductInsight], vendor: str = "All"):
    """Filter alerts by vendor"""
    if vendor == "All":
        return alerts
    return [i for i in alerts if i.vendor == vendor]

def filter_alerts_by_timing(alerts: List[ProductInsight], timing: str = "All"):
    """Filter alerts by timing"""
    if timing == "All":
        return alerts
    return [i for i in alerts if i.reorder_timing == timing]

def search_alerts(alerts: List[ProductInsight], search_term: str):
    """Search alerts by style number or description"""
    if not search_term:
        return alerts
    
    search_term = search_term.lower()
    return [
        i for i in alerts 
        if search_term in i.style_number.lower() or search_term in i.description.lower()
    ]
