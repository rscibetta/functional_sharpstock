"""
SharpStock Trend Analysis Page
Deep dive into product performance and trend insights
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any

from models.data_models import ProductInsight
from ui.components import (
    sharpstock_page_header,
    sharpstock_metric_card_enhanced,
    sharpstock_alert_banner,
    sharpstock_status_indicator,
    create_sharpstock_chart_enhanced,
    sharpstock_enhanced_table
)

def display_trend_analysis_page():
    """Main trend analysis page"""
    
    sharpstock_page_header(
        "📈 Trend Analysis",
        "Deep dive into product performance and market trends",
        show_back_button=True
    )
    
    insights = st.session_state.get('insights', [])
    recent_orders_df = st.session_state.get('recent_orders_df', pd.DataFrame())
    
    if not insights:
        sharpstock_alert_banner("No analysis data available. Please run analysis first.", "warning")
        return
    
    # Check for selected product detail view
    if st.session_state.get('selected_product_id'):
        _show_product_detail_view()
        return
    
    # Main trend analysis content
    _show_trend_overview(insights)
    _show_trend_categories(insights)
    _show_velocity_analysis(insights)
    _show_product_finder(insights)

def _show_trend_overview(insights: List[ProductInsight]):
    """Show trend analysis overview metrics"""
    
    # Calculate trend statistics
    trend_stats = _calculate_trend_statistics(insights)
    
    st.markdown("### 📊 Trend Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sharpstock_metric_card_enhanced(
            "Trending Up",
            str(trend_stats['trending_up']),
            f"{trend_stats['trending_up_pct']:.1f}% of products",
            "📈",
            "success"
        )
    
    with col2:
        sharpstock_metric_card_enhanced(
            "Hot Sellers",
            str(trend_stats['hot_sellers']),
            f"{trend_stats['hot_sellers_pct']:.1f}% of products",
            "🔥",
            "error"
        )
    
    with col3:
        sharpstock_metric_card_enhanced(
            "Declining",
            str(trend_stats['declining']),
            f"{trend_stats['declining_pct']:.1f}% of products",
            "📉",
            "warning"
        )
    
    with col4:
        sharpstock_metric_card_enhanced(
            "Avg Velocity Change",
            f"{trend_stats['avg_velocity']:+.1f}%",
            "Overall trend direction",
            "⚡",
            "primary"
        )
    
    # Trend distribution chart
    _show_trend_distribution_chart(insights)

def _show_trend_distribution_chart(insights: List[ProductInsight]):
    """Show trend distribution visualization"""
    
    # Count trends
    trend_counts = {}
    velocity_data = []
    
    for insight in insights:
        trend = insight.trend_classification
        trend_counts[trend] = trend_counts.get(trend, 0) + 1
        velocity_data.append({
            'Trend': trend,
            'Velocity_Change': insight.velocity_change,
            'Daily_Demand': insight.recent_daily_demand,
            'Product': insight.style_number,
            'Brand': insight.vendor
        })
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart of trend distribution
        if trend_counts:
            df_trends = pd.DataFrame(list(trend_counts.items()), columns=['Trend', 'Count'])
            fig = create_sharpstock_chart_enhanced(
                df_trends,
                chart_type="pie",
                title="Product Trend Distribution",
                values='Count',
                names='Trend',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Velocity vs Demand scatter plot
        if velocity_data:
            df_velocity = pd.DataFrame(velocity_data)
            fig = create_sharpstock_chart_enhanced(
                df_velocity,
                chart_type="scatter",
                title="Velocity Change vs Daily Demand",
                x='Velocity_Change',
                y='Daily_Demand',
                color='Trend',
                hover_data=['Product', 'Brand'],
                height=400
            )
            fig.update_layout(
                xaxis_title="Velocity Change (%)",
                yaxis_title="Daily Demand (units)"
            )
            st.plotly_chart(fig, use_container_width=True)

def _show_trend_categories(insights: List[ProductInsight]):
    """Show products organized by trend categories"""
    
    st.markdown("---")
    st.markdown("### 🎯 Products by Trend Category")
    
    # Categorize products
    categories = {
        'Trending Up': [i for i in insights if 'Trending Up' in i.trend_classification],
        'Hot Seller': [i for i in insights if 'Hot Seller' in i.trend_classification],
        'New Strong Seller': [i for i in insights if 'New Strong Seller' in i.trend_classification],
        'Declining': [i for i in insights if 'Declining' in i.trend_classification],
        'Stable': [i for i in insights if 'Stable' in i.trend_classification]
    }
    
    # Create tabs for each category
    non_empty_categories = {k: v for k, v in categories.items() if v}
    
    if non_empty_categories:
        tab_names = [f"{cat} ({len(products)})" for cat, products in non_empty_categories.items()]
        tabs = st.tabs(tab_names)
        
        for tab, (category, products) in zip(tabs, non_empty_categories.items()):
            with tab:
                _display_category_products(category, products)
    else:
        sharpstock_alert_banner("No trend data available", "info")

def _display_category_products(category: str, products: List[ProductInsight]):
    """Display products in a specific trend category"""
    
    if not products:
        st.info(f"No products in {category} category")
        return
    
    # Sort products by relevance to category
    if category == 'Trending Up':
        products.sort(key=lambda x: x.velocity_change, reverse=True)
    elif category == 'Hot Seller':
        products.sort(key=lambda x: x.recent_daily_demand, reverse=True)
    elif category == 'Declining':
        products.sort(key=lambda x: x.velocity_change)
    else:
        products.sort(key=lambda x: x.recent_daily_demand, reverse=True)
    
    # Show category insights
    _show_category_insights(category, products)
    
    # Display top products
    st.markdown(f"#### 🏆 Top {category} Products")
    
    for idx, insight in enumerate(products[:10]):
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 3, 1.5, 1.5, 1, 1])
            
            with col1:
                if st.button(
                    f"📊 {insight.style_number}",
                    key=f"trend_{category}_{idx}_{insight.product_id}",
                    help="Click for detailed analysis"
                ):
                    st.session_state['selected_product_id'] = insight.product_id
                    st.session_state['selected_style_number'] = insight.style_number
                    st.rerun()
            
            with col2:
                desc = insight.description[:40] + "..." if len(insight.description) > 40 else insight.description
                st.markdown(f"**{desc}**")
                st.caption(f"Brand: {insight.vendor}")
            
            with col3:
                velocity_color = "🟢" if insight.velocity_change > 10 else "🟡" if insight.velocity_change > -10 else "🔴"
                st.metric("Velocity", f"{insight.velocity_change:+.1f}%", delta_color="normal")
                st.caption(f"{velocity_color}")
            
            with col4:
                st.metric("Daily Demand", f"{insight.recent_daily_demand:.1f}")
                st.caption(f"vs {insight.historical_daily_demand:.1f} avg")
            
            with col5:
                priority_color = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(insight.reorder_priority, "⚪")
                st.write(f"{priority_color}")
                st.caption(insight.reorder_priority)
            
            with col6:
                st.metric("Inventory", f"{insight.current_inventory:,}")
                days_text = f"{insight.days_until_stockout}d" if insight.days_until_stockout < 999 else "OK"
                st.caption(days_text)
        
        if idx < len(products[:10]) - 1:
            st.markdown("---")

def _show_category_insights(category: str, products: List[ProductInsight]):
    """Show insights specific to the trend category"""
    
    if not products:
        return
    
    avg_velocity = sum(p.velocity_change for p in products) / len(products)
    avg_demand = sum(p.recent_daily_demand for p in products) / len(products)
    top_brands = {}
    
    for product in products:
        brand = product.vendor
        top_brands[brand] = top_brands.get(brand, 0) + 1
    
    top_brand = max(top_brands.items(), key=lambda x: x[1]) if top_brands else ("Unknown", 0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Average Velocity", f"{avg_velocity:+.1f}%")
    
    with col2:
        st.metric("Average Daily Demand", f"{avg_demand:.1f}")
    
    with col3:
        st.metric("Top Brand", top_brand[0])
        st.caption(f"{top_brand[1]} products")

def _show_velocity_analysis(insights: List[ProductInsight]):
    """Show detailed velocity analysis"""
    
    st.markdown("---")
    st.markdown("### ⚡ Velocity Analysis")
    
    # Velocity ranges
    velocity_ranges = {
        'High Growth (>20%)': [i for i in insights if i.velocity_change > 20],
        'Moderate Growth (5-20%)': [i for i in insights if 5 <= i.velocity_change <= 20],
        'Stable (-5% to 5%)': [i for i in insights if -5 <= i.velocity_change < 5],
        'Moderate Decline (-20% to -5%)': [i for i in insights if -20 <= i.velocity_change < -5],
        'High Decline (<-20%)': [i for i in insights if i.velocity_change < -20]
    }
    
    # Velocity distribution chart
    velocity_data = []
    for range_name, products in velocity_ranges.items():
        if products:
            velocity_data.append({
                'Range': range_name,
                'Count': len(products),
                'Avg_Velocity': sum(p.velocity_change for p in products) / len(products)
            })
    
    if velocity_data:
        df_velocity = pd.DataFrame(velocity_data)
        
        fig = create_sharpstock_chart_enhanced(
            df_velocity,
            chart_type="bar",
            title="Products by Velocity Range",
            x='Range',
            y='Count',
            height=400
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Show velocity insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Growth Opportunities")
        growth_products = velocity_ranges['High Growth (>20%)'] + velocity_ranges['Moderate Growth (5-20%)']
        if growth_products:
            growth_products.sort(key=lambda x: x.velocity_change, reverse=True)
            for product in growth_products[:5]:
                st.markdown(f"• **{product.style_number}** (+{product.velocity_change:.1f}%) - {product.vendor}")
        else:
            st.info("No significant growth products found")
    
    with col2:
        st.markdown("#### 📉 Declining Products")
        decline_products = velocity_ranges['High Decline (<-20%)'] + velocity_ranges['Moderate Decline (-20% to -5%)']
        if decline_products:
            decline_products.sort(key=lambda x: x.velocity_change)
            for product in decline_products[:5]:
                st.markdown(f"• **{product.style_number}** ({product.velocity_change:.1f}%) - {product.vendor}")
        else:
            st.info("No significantly declining products found")

def _show_product_finder(insights: List[ProductInsight]):
    """Show product search and filter interface"""
    
    st.markdown("---")
    st.markdown("### 🔍 Product Finder")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input(
            "🔍 Search Products",
            placeholder="Enter style number or description",
            help="Search by product style number or description"
        )
    
    with col2:
        brands = ['All'] + sorted(list(set([i.vendor for i in insights if i.vendor != 'Unknown'])))
        selected_brand = st.selectbox("🏷️ Filter by Brand", brands)
    
    with col3:
        trend_options = ['All'] + sorted(list(set([i.trend_classification for i in insights])))
        selected_trend = st.selectbox("📈 Filter by Trend", trend_options)
    
    # Apply filters
    filtered_products = insights
    
    if search_term:
        filtered_products = [
            p for p in filtered_products 
            if search_term.lower() in p.style_number.lower() or search_term.lower() in p.description.lower()
        ]
    
    if selected_brand != 'All':
        filtered_products = [p for p in filtered_products if p.vendor == selected_brand]
    
    if selected_trend != 'All':
        filtered_products = [p for p in filtered_products if p.trend_classification == selected_trend]
    
    # Display results
    if filtered_products:
        st.markdown(f"**Found {len(filtered_products)} products:**")
        
        # Create table data
        table_data = []
        for product in filtered_products[:20]:  # Limit to 20 for performance
            table_data.append({
                'Style': product.style_number,
                'Description': product.description[:50] + "..." if len(product.description) > 50 else product.description,
                'Brand': product.vendor,
                'Trend': product.trend_classification,
                'Velocity': f"{product.velocity_change:+.1f}%",
                'Daily Demand': f"{product.recent_daily_demand:.1f}",
                'Priority': product.reorder_priority,
                'Inventory': f"{product.current_inventory:,}"
            })
        
        # Display as enhanced table
        sharpstock_enhanced_table(table_data, f"Search Results ({len(filtered_products)} found)")
        
        if len(filtered_products) > 20:
            st.caption(f"Showing first 20 of {len(filtered_products)} results")
    else:
        sharpstock_alert_banner("No products match your search criteria", "info")

def _show_product_detail_view():
    """Show detailed view for selected product"""
    
    # This would integrate with your existing product detail component
    from ui.product_detail import display_product_detail_page
    
    recent_orders_df = st.session_state.get('recent_orders_df', pd.DataFrame())
    inventory_df = st.session_state.get('inventory_df', pd.DataFrame())
    location_config = st.session_state.get('location_config', {})
    
    display_product_detail_page(
        recent_orders_df,
        inventory_df,
        st.session_state['selected_product_id'],
        st.session_state.get('selected_style_number', 'Unknown'),
        location_config
    )

def _calculate_trend_statistics(insights: List[ProductInsight]) -> Dict[str, Any]:
    """Calculate trend statistics for overview"""
    
    total_products = len(insights)
    if total_products == 0:
        return {
            'trending_up': 0, 'trending_up_pct': 0,
            'hot_sellers': 0, 'hot_sellers_pct': 0,
            'declining': 0, 'declining_pct': 0,
            'avg_velocity': 0
        }
    
    trending_up = len([i for i in insights if 'Trending' in i.trend_classification])
    hot_sellers = len([i for i in insights if 'Hot' in i.trend_classification])
    declining = len([i for i in insights if 'Declining' in i.trend_classification])
    avg_velocity = sum([i.velocity_change for i in insights]) / total_products
    
    return {
        'trending_up': trending_up,
        'trending_up_pct': (trending_up / total_products) * 100,
        'hot_sellers': hot_sellers,
        'hot_sellers_pct': (hot_sellers / total_products) * 100,
        'declining': declining,
        'declining_pct': (declining / total_products) * 100,
        'avg_velocity': avg_velocity
    }
