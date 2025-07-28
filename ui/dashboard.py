"""
SharpStock Dashboard - Native Streamlit Implementation
Clean, professional components using Streamlit's native theming
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
from models.data_models import ProductInsight, SeasonalInsight, UserProfile
from ui.components import (
    sharpstock_section_header,
    sharpstock_metric_card,
    sharpstock_info_box,
    sharpstock_status_badge,
    sharpstock_trend_indicator,
    create_sharpstock_chart,
    sharpstock_dataframe,
    sharpstock_metric_dashboard
)
try:
    from pending_orders.pending_order_manager import PendingOrderManager
except ImportError:
    PendingOrderManager = None

def display_best_sellers_section_native(orders_df: pd.DataFrame, location_config: Dict[int, str]):
    """Native Streamlit best sellers section"""
    
    sharpstock_section_header(
        "🏆 Top Performing Products",
        "Best selling items across your store locations"
    )
    
    if orders_df.empty:
        sharpstock_info_box("No sales data available for best sellers analysis", "info")
        return
    
    # Enhanced filters
    col1, col2, col3 = st.columns(3)
    with col1:
        vendors = ['All'] + sorted([v for v in orders_df['vendor'].dropna().unique() if v and v != 'Unknown'])
        selected_vendor = st.selectbox("🏷️ Brand:", vendors, key="bestseller_vendor")
    with col2:
        locations = ['All'] + sorted([l for l in orders_df['Store Location'].dropna().unique() if l and l != 'Unknown'])
        selected_location = st.selectbox("📍 Location:", locations, key="bestseller_location")
    with col3:
        num_products = st.slider("📊 Show:", 5, 30, 15, key="bestseller_count")
    
    # Apply filters
    filtered_df = orders_df.copy()
    if selected_vendor != 'All':
        filtered_df = filtered_df[filtered_df['vendor'] == selected_vendor]
    if selected_location != 'All':
        filtered_df = filtered_df[filtered_df['Store Location'] == selected_location]
    
    if filtered_df.empty:
        sharpstock_info_box("No data matches the selected filters", "warning")
        return
    
    # Calculate best sellers
    bestsellers = filtered_df.groupby(['product_id', 'Style Number', 'Description', 'vendor']).agg({
        'quantity': 'sum',
        'total_value': 'sum'
    }).reset_index().sort_values('quantity', ascending=False).head(num_products)
    
    if bestsellers.empty:
        sharpstock_info_box("No best sellers data available", "warning")
        return
    
    # Native table display
    st.markdown("**📊 Top Products:**")
    
    # Create clean table structure
    for idx, row in bestsellers.iterrows():
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 4, 2, 2, 1])
            
            with col1:
                if st.button(
                    f"📊 {str(row['Style Number'])}", 
                    key=f"bestseller_{idx}_{int(row['product_id'])}",
                    help="Click to view detailed analysis"
                ):
                    st.session_state['selected_product_id'] = int(row['product_id'])
                    st.session_state['selected_style_number'] = str(row['Style Number'])
                    st.rerun()
            
            with col2:
                desc = str(row['Description'])
                display_desc = desc[:50] + '...' if len(desc) > 50 else desc
                st.markdown(f"**{display_desc}**")
                st.caption(f"Brand: {str(row['vendor']) if row['vendor'] else 'Unknown'}")
            
            with col3:
                st.metric("Units Sold", f"{int(row['quantity']):,}")
            
            with col4:
                st.metric("Revenue", f"${row['total_value']:,.0f}")
            
            with col5:
                # Rank badge using native styling
                rank = idx + 1
                if rank <= 3:
                    st.markdown(f"🥇 **#{rank}**" if rank == 1 else f"🥈 **#{rank}**" if rank == 2 else f"🥉 **#{rank}**")
                else:
                    st.markdown(f"**#{rank}**")
        
        if idx < len(bestsellers) - 1:
            st.markdown("---")

def display_business_metrics_native(insights: List[ProductInsight], summary_metrics: Dict):
    """Native Streamlit business metrics dashboard"""
    
    sharpstock_section_header(
        "📊 Business Performance Dashboard", 
        "Real-time insights and key performance indicators"
    )
    
    # Prepare metrics data
    recent_revenue = summary_metrics.get('total_recent_revenue', 0)
    growth_rate = summary_metrics.get('revenue_growth_rate', 0)
    total_products = len(insights)
    trending_up = summary_metrics.get('trending_up_count', 0)
    critical_reorders = summary_metrics.get('critical_reorders', 0)
    high_priority = summary_metrics.get('high_priority_reorders', 0)
    avg_stockout_days = summary_metrics.get('avg_days_until_stockout', 999)
    at_risk = summary_metrics.get('inventory_at_risk', 0)
    
    # Create metrics array
    metrics_data = [
        {
            'title': 'Total Revenue',
            'value': f'${recent_revenue:,.0f}',
            'delta': f'{growth_rate:+.1f}% vs historical',
            'icon': '💰'
        },
        {
            'title': 'Products Analyzed',
            'value': f'{total_products:,}',
            'delta': f'{trending_up} trending up ({trending_up/max(total_products,1)*100:.0f}%)',
            'icon': '📦'
        },
        {
            'title': 'Reorder Alerts',
            'value': f'{critical_reorders + high_priority}',
            'delta': f'{critical_reorders} critical, {high_priority} high priority',
            'icon': '🚨'
        },
        {
            'title': 'Inventory Status',
            'value': f'{avg_stockout_days:.0f} days' if avg_stockout_days < 999 else 'Stable',
            'delta': f'{at_risk} products at risk (≤30 days)',
            'icon': '📅'
        }
    ]
    
    # Display using metric dashboard component
    sharpstock_metric_dashboard(metrics_data)

def display_reorder_recommendations_native(insights: List[ProductInsight]):
    """Native Streamlit reorder recommendations"""
    
    sharpstock_section_header(
        "🎯 Smart Reorder Recommendations",
        "AI-powered recommendations based on trend analysis and demand forecasting"
    )
    
    if not insights:
        sharpstock_info_box("No reorder recommendations available at this time.", "info")
        return
    
    # Filters using native Streamlit
    col1, col2, col3 = st.columns(3)
    
    with col1:
        priority_filter = st.selectbox(
            "🎚️ Priority Level",
            ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
            key="reorder_priority_filter"
        )
    
    with col2:
        timing_filter = st.selectbox(
            "⏰ Timing Filter",
            ["All", "Order Now", "Order This Week", "Monitor", "No Action"],
            key="reorder_timing_filter"
        )
    
    with col3:
        vendor_options = ["All"] + sorted(list(set([i.vendor for i in insights if i.vendor != 'Unknown'])))
        vendor_filter = st.selectbox("🏷️ Brand Filter", vendor_options, key="reorder_vendor_filter")
    
    # Apply filters
    filtered_insights = insights
    if priority_filter != "All":
        filtered_insights = [i for i in filtered_insights if i.reorder_priority == priority_filter]
    if timing_filter != "All":
        filtered_insights = [i for i in filtered_insights if i.reorder_timing == timing_filter]
    if vendor_filter != "All":
        filtered_insights = [i for i in filtered_insights if i.vendor == vendor_filter]
    
    if not filtered_insights:
        sharpstock_info_box("No products match the selected filters.", "warning")
        return
    
    st.markdown(f"**📋 Showing {len(filtered_insights)} recommendations:**")
    
    # Display recommendations using native Streamlit expandables
    for idx, insight in enumerate(filtered_insights[:15]):  # Limit for performance
        
        # Create expandable product card
        with st.expander(
            f"{sharpstock_status_badge(insight.reorder_priority)} **{insight.style_number}** - {insight.description[:50]}...", 
            expanded=False
        ):
            
            # Product details in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**📊 Performance Metrics**")
                
                # Use native metrics
                st.metric("Daily Demand", f"{insight.recent_daily_demand:.1f}", 
                         f"vs {insight.historical_daily_demand:.1f} historical")
                st.metric("Recent Sales", f"{insight.recent_total_sales:,}", 
                         f"${insight.recent_revenue:,.0f} revenue")
            
            with col2:
                st.markdown("**📦 Inventory Status**")
                
                days_left = insight.days_until_stockout
                days_color = "🔴" if days_left <= 14 else "🟡" if days_left <= 30 else "🟢"
                
                st.metric("Current Stock", f"{insight.current_inventory:,}", 
                         f"{days_color} {days_left} days remaining" if days_left < 999 else "Well stocked")
                st.metric("Turnover Rate", f"{insight.inventory_turnover:.1f}x", "Annual turnover")
            
            with col3:
                st.markdown("**🎯 Recommendations**")
                
                priority_color = "🔴" if insight.reorder_priority == "CRITICAL" else "🟡" if insight.reorder_priority == "HIGH" else "🟢"
                
                st.metric("Recommended Qty", f"{insight.recommended_qty:,}", 
                         f"{priority_color} {insight.reorder_timing}")
                
                st.markdown("**📈 Trend Analysis**")
                st.write(sharpstock_trend_indicator(insight.trend_classification, insight.velocity_change))
            
            # Reasoning section
            st.markdown("**💡 AI Analysis & Reasoning**")
            sharpstock_info_box(insight.reasoning, "info")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"📊 View Details", key=f"detail_{insight.product_id}_{idx}"):
                    st.session_state['selected_product_id'] = insight.product_id
                    st.session_state['selected_style_number'] = insight.style_number
                    st.rerun()
            
            with col2:
                if st.button(f"🛒 Add to Order", key=f"order_{insight.product_id}_{idx}"):
                    st.success("Added to order sheet!")
            
            with col3:
                if st.button(f"📋 Copy Info", key=f"copy_{insight.product_id}_{idx}"):
                    # Create copyable text
                    copy_text = f"{insight.style_number}: {insight.recommended_qty} units needed - {insight.reorder_timing}"
                    st.text_area("Copy this:", copy_text, height=50, key=f"copy_area_{idx}")

def display_trend_analysis_native(insights: List[ProductInsight]):
    """Native Streamlit trend analysis"""
    
    sharpstock_section_header(
        "📈 Advanced Trend Analysis",
        "Machine learning powered trend detection and velocity analysis"
    )
    
    if not insights:
        sharpstock_info_box("No trend data available for analysis.", "warning")
        return
    
    # Trend distribution analysis
    trend_counts = {}
    velocity_data = []
    
    for insight in insights:
        trend_counts[insight.trend_classification] = trend_counts.get(insight.trend_classification, 0) + 1
        velocity_data.append({
            'trend': insight.trend_classification,
            'velocity': insight.velocity_change,
            'daily_demand': insight.recent_daily_demand,
            'style': insight.style_number
        })
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Enhanced pie chart
        if trend_counts:
            df_trends = pd.DataFrame(list(trend_counts.items()), columns=['Trend', 'Count'])
            fig = create_sharpstock_chart(
                df_trends,
                chart_type="pie",
                title="Product Trend Distribution",
                values='Count',
                names='Trend'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Velocity vs Demand scatter
        if velocity_data:
            df_velocity = pd.DataFrame(velocity_data)
            fig = create_sharpstock_chart(
                df_velocity,
                chart_type="scatter",
                title="Velocity Change vs Daily Demand",
                x='velocity',
                y='daily_demand',
                color='trend',
                hover_data=['style']
            )
            fig.update_layout(
                xaxis_title="Velocity Change (%)",
                yaxis_title="Daily Demand (units)"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Trend summary using native tabs
    st.markdown("### 📊 Trend Categories")
    
    trend_categories = ['Trending Up', 'Hot Seller', 'New Strong Seller', 'Declining']
    
    # Create tabs for different trend categories
    if any(i.trend_classification in trend_categories for i in insights):
        trend_tabs = st.tabs([f"{cat} ({len([i for i in insights if i.trend_classification == cat])})" 
                             for cat in trend_categories])
        
        for tab_idx, category in enumerate(trend_categories):
            with trend_tabs[tab_idx]:
                category_products = [i for i in insights if i.trend_classification == category]
                
                if category_products:
                    # Sort products appropriately
                    if category == 'Hot Seller':
                        category_products.sort(key=lambda x: x.recent_daily_demand, reverse=True)
                    else:
                        category_products.sort(key=lambda x: abs(x.velocity_change), reverse=True)
                    
                    # Display top products in this category
                    for idx, insight in enumerate(category_products[:10]):
                        col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 1, 1])
                        
                        with col1:
                            if st.button(insight.style_number, key=f"trend_{category}_{idx}_{insight.product_id}"):
                                st.session_state['selected_product_id'] = insight.product_id
                                st.session_state['selected_style_number'] = insight.style_number
                                st.rerun()
                        
                        with col2:
                            desc = insight.description[:35] + "..." if len(insight.description) > 35 else insight.description
                            st.write(desc)
                        
                        with col3:
                            st.write(f"**{insight.vendor}**")
                        
                        with col4:
                            change_color = "🟢" if insight.velocity_change > 0 else "🔴" if insight.velocity_change < 0 else "⚪"
                            st.write(f"{change_color} {insight.velocity_change:+.1f}%")
                        
                        with col5:
                            st.write(f"{insight.recent_daily_demand:.1f}/day")
                        
                        if idx < len(category_products[:10]) - 1:
                            st.markdown("---")
                else:
                    sharpstock_info_box(f"No products currently in {category} category", "info")

def display_seasonal_analysis_native(seasonal_insights: List[SeasonalInsight]):
    """Native Streamlit seasonal analysis"""
    
    sharpstock_section_header(
        "📅 Seasonal Intelligence",
        "Advanced seasonal pattern detection and product elevation analysis"
    )
    
    if not seasonal_insights:
        sharpstock_info_box("No seasonal data available for analysis.", "warning")
        return
    
    # Seasonal explanation
    sharpstock_info_box(
        "**Seasonal Elevation** identifies products that sell significantly **above their normal rate** during specific months. "
        "This helps identify true seasonal opportunities vs. products that are just generally popular.",
        "info"
    )
    
    # Seasonal charts
    months = [s.month_name for s in seasonal_insights]
    demand = [s.avg_daily_demand for s in seasonal_insights]
    multipliers = [s.seasonal_multiplier for s in seasonal_insights]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Enhanced demand chart
        df_demand = pd.DataFrame({'Month': months, 'Daily_Demand': demand})
        fig = create_sharpstock_chart(
            df_demand,
            chart_type="bar",
            title="Monthly Demand Patterns",
            x='Month',
            y='Daily_Demand'
        )
        fig.update_layout(xaxis_title="Month", yaxis_title="Average Daily Demand")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Enhanced multiplier chart
        df_multiplier = pd.DataFrame({'Month': months, 'Multiplier': multipliers})
        fig = create_sharpstock_chart(
            df_multiplier,
            chart_type="line",
            title="Seasonal Multipliers",
            x='Month',
            y='Multiplier'
        )
        fig.add_hline(y=1.0, line_dash="dash", line_color="#EF4444", annotation_text="Average")
        fig.update_layout(xaxis_title="Month", yaxis_title="Seasonal Multiplier")
        st.plotly_chart(fig, use_container_width=True)
    
    # Enhanced seasonal products display using native tabs
    st.markdown("### 🌟 Seasonally Elevated Products by Quarter")
    
    q1_tab, q2_tab, q3_tab, q4_tab = st.tabs(["Q1 (Jan-Mar)", "Q2 (Apr-Jun)", "Q3 (Jul-Sep)", "Q4 (Oct-Dec)"])
    
    quarters = {
        q1_tab: [1, 2, 3],
        q2_tab: [4, 5, 6], 
        q3_tab: [7, 8, 9],
        q4_tab: [10, 11, 12]
    }
    
    for tab, months_in_quarter in quarters.items():
        with tab:
            for season in seasonal_insights:
                if season.month in months_in_quarter:
                    
                    # Enhanced month header
                    multiplier_emoji = "🔥" if season.seasonal_multiplier > 1.1 else "❄️" if season.seasonal_multiplier < 0.9 else "📊"
                    
                    with st.container():
                        col1, col2 = st.columns([1, 3])
                        
                        with col1:
                            st.metric(
                                f"{multiplier_emoji} {season.month_name}",
                                f"{season.avg_daily_demand:.0f}",
                                f"{season.seasonal_multiplier:.2f}x vs average"
                            )
                        
                        with col2:
                            if season.peak_products:
                                st.markdown("**🌟 Seasonally Elevated Products:**")
                                
                                for i, product in enumerate(season.peak_products, 1):
                                    style = product['style_number']
                                    description = product['description']
                                    quantity = product['quantity']
                                    elevation = product['seasonal_elevation']
                                    product_id = product['product_id']
                                    
                                    # Enhanced product card using native components
                                    with st.container():
                                        col_a, col_b, col_c, col_d = st.columns([0.5, 1.5, 3, 1])
                                        
                                        with col_a:
                                            st.markdown(f"**{i}.**")
                                        
                                        with col_b:
                                            if st.button(style, key=f"seasonal_{season.month}_{i}_{style}_{product_id}"):
                                                st.session_state['selected_product_id'] = product_id
                                                st.session_state['selected_style_number'] = style
                                                st.rerun()
                                        
                                        with col_c:
                                            st.write(description)
                                        
                                        with col_d:
                                            # Color-coded elevation
                                            if elevation >= 3.0:
                                                st.markdown("🔥 **Strong**")
                                            elif elevation >= 2.0:
                                                st.markdown("⚡ **Moderate**")
                                            else:
                                                st.markdown("📈 **Weak**")
                                            st.caption(f"{elevation:.1f}x normal")
                                        
                                        # Detailed analysis in expander
                                        with st.expander(f"📊 {style} Analysis", expanded=False):
                                            metric_col1, metric_col2 = st.columns(2)
                                            
                                            with metric_col1:
                                                st.metric(
                                                    f"Monthly Sales ({season.month_name})",
                                                    f"{quantity:,}",
                                                    f"{product['daily_avg_month']:.2f} daily avg"
                                                )
                                            
                                            with metric_col2:
                                                st.metric(
                                                    "Annual Performance",
                                                    f"{product['daily_avg_overall']:.2f}",
                                                    f"{elevation:.1f}x seasonal boost"
                                                )
                            else:
                                sharpstock_info_box(
                                    f"No significantly elevated products found for {season.month_name}. "
                                    "Products need to sell 50%+ above their annual average with meaningful volume.",
                                    "info"
                                )
                    
                    st.markdown("---")

def display_transfer_recommendations_native(
    orders_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    insights: List[ProductInsight],
    location_config: Dict[int, str],
    user_profile
):
    """Native Streamlit transfer recommendations interface"""
    
    sharpstock_section_header(
        "🔄 Inventory Transfer Recommendations",
        "Smart transfer suggestions to optimize inventory distribution"
    )
    
    if orders_df.empty or inventory_df.empty:
        sharpstock_info_box("Need both sales and inventory data to generate transfer recommendations", "info")
        return
    
    # Initialize transfer engine
    from analysis.transfer_analysis import TransferAnalysisEngine
    transfer_engine = TransferAnalysisEngine(location_config, user_profile)
    
    # Settings using native components
    with st.expander("⚙️ Transfer Analysis Settings"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            analysis_days = st.slider(
                "Demand Analysis Period (days):", 
                7, 90, 30,
                help="Period to calculate demand patterns"
            )
        
        with col2:
            urgency_filter = st.selectbox(
                "Urgency Level:",
                ["All", "URGENT", "HIGH", "MEDIUM", "LOW"]
            )
        
        with col3:
            location_filter = st.selectbox(
                "Destination Store:",
                ["All"] + list(location_config.values())
            )
    
    # Generate recommendations
    with st.spinner("🧠 Analyzing transfer opportunities..."):
        recommendations = transfer_engine.analyze_transfer_opportunities(
            orders_df, inventory_df, insights, analysis_days
        )
    
    # Apply filters
    filtered_recs = recommendations
    if urgency_filter != "All":
        filtered_recs = [r for r in filtered_recs if r.transfer_urgency == urgency_filter]
    if location_filter != "All":
        filtered_recs = [r for r in filtered_recs if r.to_location_name == location_filter]
    
    if not filtered_recs:
        sharpstock_info_box("No transfer recommendations found with current filters", "info")
        return
    
    # Summary metrics using native metrics
    metrics_data = [
        {
            'title': 'Total Recommendations',
            'value': f'{len(filtered_recs)}',
            'icon': '📊'
        },
        {
            'title': 'Urgent Transfers',
            'value': f'{len([r for r in filtered_recs if r.transfer_urgency == "URGENT"])}',
            'icon': '🚨'
        },
        {
            'title': 'Potential Impact',
            'value': f'${sum(r.financial_impact for r in filtered_recs):,.0f}',
            'icon': '💰'
        },
        {
            'title': 'Total Units',
            'value': f'{sum(r.recommended_transfer_qty for r in filtered_recs):,}',
            'icon': '📦'
        }
    ]
    
    sharpstock_metric_dashboard(metrics_data)
    
    # Display recommendations using native expandables
    st.markdown("**🔄 Transfer Recommendations:**")
    
    for idx, rec in enumerate(filtered_recs[:20]):
        with st.expander(
            f"{sharpstock_status_badge(rec.transfer_urgency)} **{rec.style_number}** - Transfer {rec.recommended_transfer_qty} units", 
            expanded=False
        ):
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    f"From: {rec.from_location_name}",
                    f"{rec.from_inventory} units",
                    f"{rec.from_days_of_stock} days stock"
                )
            
            with col2:
                days_color = "🔴" if rec.to_days_of_stock < 30 else "🟡" if rec.to_days_of_stock < 60 else "🟢"
                st.metric(
                    f"To: {rec.to_location_name}",
                    f"{rec.to_inventory} units",
                    f"{days_color} {rec.to_days_of_stock} days stock"
                )
            
            with col3:
                st.metric(
                    "Financial Impact",
                    f"${rec.financial_impact:,.0f}",
                    f"Transfer: {rec.recommended_transfer_qty} units"
                )
            
            # Action button
            if st.button(f"📊 View Product Details", key=f"transfer_detail_{rec.product_id}_{idx}"):
                st.session_state['selected_product_id'] = rec.product_id
                st.session_state['selected_style_number'] = rec.style_number
                st.rerun()
            
            # Reasoning
            sharpstock_info_box(rec.reasoning, "info")

def display_order_sheet_interface_native(
    insights: List[ProductInsight],
    orders_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    location_config: Dict[int, str],
    user_profile
):
    """Native Streamlit order sheet interface"""
    
    sharpstock_section_header(
        "📋 Order Sheet Generator",
        "Select products to reorder, then view variant breakdowns"
    )
    
    # Initialize order manager
    if 'order_sheet_manager' not in st.session_state:
        from order_management.order_sheet_manager import OrderSheetManager
        st.session_state['order_sheet_manager'] = OrderSheetManager(location_config)
    
    order_manager = st.session_state['order_sheet_manager']
    
    # Step 1: Brand Selection
    st.markdown("### 1️⃣ Select Brand")
    available_brands = sorted(list(set([i.vendor for i in insights if i.vendor not in ['Unknown', '', 'nan']])))
    
    if not available_brands:
        sharpstock_info_box("No brands found in the analysis data", "warning")
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
        sharpstock_info_box(f"No products found for {selected_brand}", "warning")
        return
    
    # Filter for products that actually need reordering
    reorder_insights = [i for i in brand_insights if i.reorder_priority in ['CRITICAL', 'HIGH', 'MEDIUM']]
    
    if not reorder_insights:
        sharpstock_info_box(f"No products currently need reordering for {selected_brand}", "info")
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
        sharpstock_info_box("No products match the selected filters", "warning")
        return
    
    # Display products using native table format
    st.write("**Select products to add to order sheet:**")
    
    # Create clean table structure
    for idx, insight in enumerate(reorder_insights[:20]):  # Limit to 20 for performance
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 3, 1, 1, 1, 1])
            
            with col1:
                # Make style number clickable for variant breakdown
                if st.button(insight.style_number, key=f"style_{idx}_{insight.product_id}"):
                    st.session_state['selected_style_for_variants'] = insight
                    st.rerun()
            
            with col2:
                desc = insight.description[:35] + "..." if len(insight.description) > 35 else insight.description
                st.write(desc)
                st.caption(f"{sharpstock_status_badge(insight.reorder_priority)} - {insight.reorder_timing}")
            
            with col3:
                st.metric("Daily Demand", f"{insight.recent_daily_demand:.1f}")
            
            with col4:
                st.metric("Current Stock", f"{insight.current_inventory:,}")
            
            with col5:
                st.metric("Recommended", f"{insight.recommended_qty:,}")
            
            with col6:
                # Quick add entire product button
                if st.button("➕ Add Style", key=f"add_style_{idx}_{insight.product_id}"):
                    # Import the smart recommendations function
                    from order_management.smart_recommendations import add_all_variants_for_product_with_smart_recommendations
                    
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
        
        if idx < len(reorder_insights[:20]) - 1:
            st.markdown("---")
    
    # Current Order Sheet (if items exist)
    current_items = order_manager.selected_items.get(selected_brand, [])
    if current_items:
        st.markdown("---")
        st.markdown(f"### 3️⃣ Current Order Sheet - {selected_brand}")
        
        # Summary metrics
        summary = order_manager.get_order_summary(selected_brand)
        
        summary_metrics = [
            {
                'title': 'Total Styles',
                'value': f'{len(set(item.style_number for item in current_items))}',
                'icon': '📊'
            },
            {
                'title': 'Hilo Total',
                'value': f'{summary["store_totals"]["Hilo"]}',
                'icon': '🏪'
            },
            {
                'title': 'Kailua Total', 
                'value': f'{summary["store_totals"]["Kailua"]}',
                'icon': '🏪'
            },
            {
                'title': 'Grand Total',
                'value': f'{sum(summary["store_totals"].values())}',
                'icon': '📦'
            }
        ]
        
        sharpstock_metric_dashboard(summary_metrics)
        
        # Export actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Generate Excel", type="primary"):
                excel_file = order_manager.export_order_sheet_excel(selected_brand)
                
                if excel_file:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                    filename = f"{selected_brand.replace(' ', '_')}_Order_{timestamp}.xlsx"
                    
                    st.download_button(
                        label="📥 Download Order Sheets",
                        data=excel_file,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    st.success("✅ Order sheets generated!")
                else:
                    st.error("Failed to generate order sheets")
        
        with col2:
            if st.button("🗑️ Clear Orders"):
                order_manager.clear_brand_selections(selected_brand)
                st.success(f"Cleared {selected_brand} order sheet")
                st.rerun()
        
        with col3:
            total_units = sum(summary['store_totals'].values())
            summary_text = f"{selected_brand} Order Summary:\nTotal Units: {total_units}\nHilo: {summary['store_totals']['Hilo']}\nKailua: {summary['store_totals']['Kailua']}\nKapaa: {summary['store_totals']['Kapaa']}\nWailuku: {summary['store_totals']['Wailuku']}"
            
            if st.button("📋 Show Summary"):
                st.text_area(
                    "Order Summary:",
                    value=summary_text,
                    height=120,
                    key="order_summary_display"
                )

def display_pending_orders_alert():
    """Alert shown on dashboard when pending orders are active"""
    
    if not PendingOrderManager:
        return  # Skip if pending orders not available
    
    if st.session_state.get('pending_orders_uploaded', False):
        user_profile = st.session_state.get('user_profile')
        location_config = st.session_state.get('location_config', {})
        
        if user_profile and hasattr(user_profile, 'location_config'):
            try:
                pending_manager = PendingOrderManager(user_profile, user_profile.location_config)
                pending_orders = pending_manager.load_pending_orders()
                
                if pending_orders:
                    summary = pending_manager.get_pending_orders_summary(pending_orders)
                    
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.info(f"""
                        📦 **Pending Orders Active**: {summary['total_units']:,} units across {summary['total_styles']} styles
                        
                        ✅ Analysis includes projected inventory after pending orders arrive.
                        """)
                    
                    with col2:
                        if st.button("🗑️ Clear Pending", key="clear_pending_alert"):
                            pending_manager.clear_pending_orders()
                            st.success("Cleared pending orders")
                            st.rerun()
            except Exception as e:
                st.warning(f"⚠️ Pending orders alert error: {e}")

# Export all functions for easy importing
__all__ = [
    'display_best_sellers_section_native',
    'display_business_metrics_native', 
    'display_reorder_recommendations_native',
    'display_trend_analysis_native',
    'display_seasonal_analysis_native',
    'display_transfer_recommendations_native',
    'display_order_sheet_interface_native',
    'display_pending_orders_alert',
    'diagnose_data_mismatch'
]

def diagnose_data_mismatch(orders_df, inventory_df):
    """Diagnose mismatches between sales and inventory data"""
    
    if orders_df.empty or inventory_df.empty:
        return
    
    # Get unique product IDs from each dataset
    sales_products = set(orders_df['product_id'].unique())
    inventory_products = set(inventory_df['product_id'].unique())
    
    # Find mismatches
    only_in_sales = sales_products - inventory_products
    only_in_inventory = inventory_products - sales_products
    in_both = sales_products & inventory_products
    
    st.subheader("📊 Data Quality Check")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Products in Both", len(in_both))
        st.metric("Only in Sales", len(only_in_sales))
    
    with col2:
        st.metric("Only in Inventory", len(only_in_inventory))
        st.metric("Total Sales Products", len(sales_products))
    
    with col3:
        st.metric("Total Inventory Products", len(inventory_products))
        overlap_pct = (len(in_both) / len(sales_products)) * 100 if sales_products else 0
        st.metric("Overlap %", f"{overlap_pct:.1f}%")
    
    if only_in_sales:
        with st.expander(f"⚠️ {len(only_in_sales)} Products with Sales but No Inventory"):
            st.write("These products have sales history but no inventory data:")
            
            # Show top products by sales volume
            problem_products = orders_df[orders_df['product_id'].isin(only_in_sales)]
            problem_summary = problem_products.groupby(['product_id', 'Style Number']).agg({
                'quantity': 'sum',
                'total_value': 'sum'
            }).reset_index().sort_values('quantity', ascending=False)
            
            st.dataframe(problem_summary.head(10), use_container_width=True)
            
            if len(only_in_sales) > 20:
                st.warning(f"⚠️ This affects {len(only_in_sales)} products. Consider re-running inventory fetch.")