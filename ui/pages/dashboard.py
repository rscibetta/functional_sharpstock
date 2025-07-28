"""
SharpStock Dashboard Page - Landing Page with Best Sellers
Clean, focused landing experience
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any

from ui.components import (
    sharpstock_page_header,
    sharpstock_metric_card_enhanced,
    sharpstock_quick_action_card,
    sharpstock_alert_banner,
    create_sharpstock_chart_enhanced,
    sharpstock_status_indicator,
    sharpstock_enhanced_table
)

def display_dashboard_page():
    """Main dashboard/landing page"""
    
    # Page header
    sharpstock_page_header(
        "SharpStock Dashboard",
        "Your business intelligence command center"
    )
    
    # Check if user has completed setup
    user_profile = st.session_state.get('user_profile')
    if not user_profile:
        _show_setup_required()
        return
    
    # Check if analysis data exists
    if not st.session_state.get('data_fetched', False):
        _show_initial_setup(user_profile)
        return
    
    # Main dashboard content
    _show_dashboard_overview()
    _show_best_sellers_section()
    _show_quick_actions()

def _show_setup_required():
    """Show setup required message"""
    
    sharpstock_alert_banner(
        "Welcome to SharpStock! Please complete your profile setup to get started.",
        "info"
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if sharpstock_quick_action_card(
            "Complete Setup",
            "Configure your Shopify store connection and start analyzing your data",
            "⚙️",
            "Go to Profile Settings",
            "setup_profile"
        ):
            st.session_state['current_page'] = 'profile'
            st.rerun()

def _show_initial_setup(user_profile):
    """Show initial analysis setup"""
    
    # Welcome message
    st.markdown(f"## Welcome back, {user_profile.shop_name}! 👋")
    
    # Check profile completeness
    if not hasattr(user_profile, 'shop_name') or not user_profile.shop_name:
        sharpstock_alert_banner(
            "⚠️ **Profile Incomplete** - Please complete your store configuration first.",
            "warning"
        )
        
        if st.button("🔧 Complete Profile Setup", type="primary"):
            st.session_state['current_page'] = 'profile'
            st.rerun()
        return
    
    # Show analysis options
    st.markdown("### 🚀 Ready to analyze your data?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if sharpstock_quick_action_card(
            "Run Initial Analysis",
            "Analyze your sales data and get AI-powered insights",
            "🧠",
            "Start Analysis",
            "start_analysis",
            "primary"
        ):
            _run_initial_analysis()
    
    with col2:
        if sharpstock_quick_action_card(
            "Upload Pending Orders",
            "Include orders you've placed but haven't received yet",
            "📦",
            "Manage Pending Orders",
            "manage_pending"
        ):
            st.session_state['current_page'] = 'pending'
            st.rerun()

def _run_initial_analysis():
    """Trigger initial analysis"""
    
    with st.spinner("🧠 Running your first analysis..."):
        # Import and run analysis function from main interface
        from app.main_interface import run_analysis_if_needed
        
        if run_analysis_if_needed():
            st.success("✅ Analysis complete! Your dashboard is ready.")
            st.rerun()
        else:
            st.error("❌ Analysis failed. Please check your settings.")

def _show_dashboard_overview():
    """Show main dashboard overview with key metrics"""
    
    # Get analysis data
    insights = st.session_state.get('insights', [])
    summary_metrics = st.session_state.get('summary_metrics', {})
    recent_orders_df = st.session_state.get('recent_orders_df', pd.DataFrame())
    
    # Calculate key metrics
    critical_alerts = len([i for i in insights if hasattr(i, 'reorder_priority') and i.reorder_priority == 'CRITICAL'])
    high_alerts = len([i for i in insights if hasattr(i, 'reorder_priority') and i.reorder_priority == 'HIGH'])
    trending_up = len([i for i in insights if hasattr(i, 'trend_classification') and 'Trending' in i.trend_classification])
    
    total_revenue = summary_metrics.get('total_recent_revenue', 0)
    revenue_growth = summary_metrics.get('revenue_growth_rate', 0)
    
    # Metrics row
    st.markdown("### 📊 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sharpstock_metric_card_enhanced(
            "Revenue (30d)",
            f"${total_revenue:,.0f}",
            f"{revenue_growth:+.1f}% vs historical",
            "💰",
            "primary",
            "up" if revenue_growth > 0 else "down" if revenue_growth < 0 else "neutral"
        )
    
    with col2:
        sharpstock_metric_card_enhanced(
            "Critical Alerts",
            str(critical_alerts),
            f"{high_alerts} high priority",
            "🚨",
            "error" if critical_alerts > 0 else "success"
        )
    
    with col3:
        sharpstock_metric_card_enhanced(
            "Products Analyzed",
            f"{len(insights):,}",
            f"{trending_up} trending up",
            "📦",
            "primary"
        )
    
    with col4:
        avg_stockout = summary_metrics.get('avg_days_until_stockout', 999)
        sharpstock_metric_card_enhanced(
            "Inventory Health",
            f"{avg_stockout:.0f} days" if avg_stockout < 999 else "Stable",
            "Average days until stockout",
            "📅",
            "warning" if avg_stockout < 30 else "success"
        )
    
    # Show alerts if any
    if critical_alerts > 0:
        sharpstock_alert_banner(
            f"🚨 **{critical_alerts} products need immediate reordering!** Click 'View Reorder Alerts' below to see details.",
            "error"
        )
    elif high_alerts > 0:
        sharpstock_alert_banner(
            f"⚠️ **{high_alerts} products need reordering soon.** Review your reorder alerts.",
            "warning"
        )

def _show_best_sellers_section():
    """Enhanced best sellers section"""
    
    st.markdown("---")
    st.markdown("### 🏆 Top Performing Products")
    
    recent_orders_df = st.session_state.get('recent_orders_df', pd.DataFrame())
    location_config = st.session_state.get('location_config', {})
    
    if recent_orders_df.empty:
        sharpstock_alert_banner("No sales data available for best sellers analysis", "info")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        vendors = ['All'] + sorted([v for v in recent_orders_df['vendor'].dropna().unique() if v and v != 'Unknown'])
        selected_vendor = st.selectbox("🏷️ Brand:", vendors, key="bestseller_vendor")
    
    with col2:
        locations = ['All'] + sorted([l for l in recent_orders_df['Store Location'].dropna().unique() if l and l != 'Unknown'])
        selected_location = st.selectbox("📍 Location:", locations, key="bestseller_location")
    
    with col3:
        time_period = st.selectbox("📅 Period:", ["Last 30 days", "Last 7 days", "Last 14 days"], key="bestseller_period")
    
    # Apply filters
    filtered_df = recent_orders_df.copy()
    
    # Time filter
    if time_period == "Last 7 days":
        cutoff = filtered_df['created_at'].max() - timedelta(days=7)
        filtered_df = filtered_df[filtered_df['created_at'] >= cutoff]
    elif time_period == "Last 14 days":
        cutoff = filtered_df['created_at'].max() - timedelta(days=14)
        filtered_df = filtered_df[filtered_df['created_at'] >= cutoff]
    
    if selected_vendor != 'All':
        filtered_df = filtered_df[filtered_df['vendor'] == selected_vendor]
    
    if selected_location != 'All':
        filtered_df = filtered_df[filtered_df['Store Location'] == selected_location]
    
    if filtered_df.empty:
        sharpstock_alert_banner("No data matches the selected filters", "warning")
        return
    
    # Calculate best sellers
    bestsellers = filtered_df.groupby(['product_id', 'Style Number', 'Description', 'vendor']).agg({
        'quantity': 'sum',
        'total_value': 'sum'
    }).reset_index().sort_values('quantity', ascending=False).head(10)
    
    # Display as enhanced cards
    for idx, row in bestsellers.iterrows():
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([0.5, 2, 3, 1.5, 1.5])
            
            with col1:
                # Rank with medal
                rank = idx + 1
                if rank == 1:
                    st.markdown("🥇")
                elif rank == 2:
                    st.markdown("🥈")
                elif rank == 3:
                    st.markdown("🥉")
                else:
                    st.markdown(f"**{rank}**")
            
            with col2:
                # Clickable style number
                if st.button(
                    f"📊 {row['Style Number']}", 
                    key=f"bestseller_{idx}_{int(row['product_id'])}",
                    help="Click for detailed analysis"
                ):
                    st.session_state['selected_product_id'] = int(row['product_id'])
                    st.session_state['selected_style_number'] = str(row['Style Number'])
                    st.session_state['current_page'] = 'trends'  # Go to trends page for product detail
                    st.rerun()
            
            with col3:
                desc = str(row['Description'])
                display_desc = desc[:40] + '...' if len(desc) > 40 else desc
                st.markdown(f"**{display_desc}**")
                st.caption(f"Brand: {row['vendor']}")
            
            with col4:
                st.metric("Units Sold", f"{int(row['quantity']):,}")
            
            with col5:
                st.metric("Revenue", f"${row['total_value']:,.0f}")
        
        if idx < len(bestsellers) - 1:
            st.markdown("---")
    
    # Chart visualization
    if len(bestsellers) > 0:
        st.markdown("#### 📈 Visual Breakdown")
        
        # Create chart
        fig = create_sharpstock_chart_enhanced(
            bestsellers,
            chart_type="bar",
            title="Top 10 Products by Units Sold",
            x='Style Number',
            y='quantity',
            height=400
        )
        
        fig.update_layout(
            xaxis_title="Product Style",
            yaxis_title="Units Sold",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

def _show_quick_actions():
    """Show quick action cards for navigation"""
    
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if sharpstock_quick_action_card(
            "Reorder Alerts",
            "View products that need immediate attention",
            "🚨",
            "View Alerts",
            "quick_reorder",
            "error"
        ):
            st.session_state['current_page'] = 'reorder'
            st.rerun()
    
    with col2:
        if sharpstock_quick_action_card(
            "Generate Orders",
            "Create order sheets for your suppliers",
            "📋",
            "Create Orders",
            "quick_orders",
            "primary"
        ):
            st.session_state['current_page'] = 'orders'
            st.rerun()
    
    with col3:
        if sharpstock_quick_action_card(
            "Transfer Recommendations",
            "Optimize inventory across locations",
            "🔄",
            "View Transfers",
            "quick_transfers",
            "warning"
        ):
            st.session_state['current_page'] = 'transfers'
            st.rerun()
    
    with col4:
        if sharpstock_quick_action_card(
            "Trend Analysis",
            "Deep dive into product performance",
            "📈",
            "Analyze Trends",
            "quick_trends",
            "success"
        ):
            st.session_state['current_page'] = 'trends'
            st.rerun()
    
    # Additional actions
    st.markdown("#### 🔧 Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📦 Manage Pending Orders", type="secondary", use_container_width=True):
            st.session_state['current_page'] = 'pending'
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh Analysis", type="secondary", use_container_width=True):
            # Clear analysis data to force refresh
            st.session_state['data_fetched'] = False
            st.success("Analysis data cleared. Data will refresh on next page load.")
            st.rerun()
    
    with col3:
        if st.button("⚙️ Settings", type="secondary", use_container_width=True):
            st.session_state['current_page'] = 'profile'
            st.rerun()

# Additional helper functions for dashboard
def get_dashboard_insights_summary():
    """Get summary of insights for dashboard display"""
    
    insights = st.session_state.get('insights', [])
    if not insights:
        return {}
    
    return {
        'total_products': len(insights),
        'critical_alerts': len([i for i in insights if i.reorder_priority == 'CRITICAL']),
        'high_alerts': len([i for i in insights if i.reorder_priority == 'HIGH']),
        'trending_up': len([i for i in insights if 'Trending' in i.trend_classification]),
        'declining': len([i for i in insights if 'Declining' in i.trend_classification]),
        'avg_daily_demand': sum([i.recent_daily_demand for i in insights]) / len(insights),
        'total_inventory': sum([i.current_inventory for i in insights])
    }
