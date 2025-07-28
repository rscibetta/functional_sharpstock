"""
SharpStock Transfer Recommendations Page
Optimize inventory distribution across store locations
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any

from models.data_models import ProductInsight, TransferRecommendation
from ui.components import (
    sharpstock_page_header,
    sharpstock_metric_card_enhanced,
    sharpstock_alert_banner,
    sharpstock_status_indicator,
    sharpstock_enhanced_table,
    create_sharpstock_chart_enhanced
)

def display_transfer_recommendations_page():
    """Main transfer recommendations page"""
    
    sharpstock_page_header(
        "🔄 Transfer Recommendations",
        "Optimize inventory distribution across your store locations",
        show_back_button=True
    )
    
    # Get required data
    orders_df = st.session_state.get('recent_orders_df', pd.DataFrame())
    inventory_df = st.session_state.get('inventory_df', pd.DataFrame())
    insights = st.session_state.get('insights', [])
    location_config = st.session_state.get('location_config', {})
    user_profile = st.session_state.get('user_profile')
    
    if orders_df.empty or inventory_df.empty:
        sharpstock_alert_banner(
            "Transfer analysis requires both sales and inventory data. Please run analysis first.",
            "warning"
        )
        return
    
    # Analysis settings
    _show_transfer_settings()
    
    # Generate and display recommendations
    recommendations = _generate_transfer_recommendations(orders_df, inventory_df, insights, location_config)
    
    if recommendations:
        _show_transfer_overview(recommendations, location_config)
        _show_transfer_recommendations(recommendations)
        _show_transfer_analytics(recommendations, location_config)
    else:
        _show_no_transfers_needed()

def _show_transfer_settings():
    """Show transfer analysis settings"""
    
    st.markdown("### ⚙️ Transfer Analysis Settings")
    
    with st.expander("🔧 Analysis Parameters", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            analysis_days = st.slider(
                "Demand Period (days)",
                min_value=7,
                max_value=90,
                value=30,
                help="Period to calculate demand patterns"
            )
        
        with col2:
            min_transfer_qty = st.number_input(
                "Minimum Transfer Quantity",
                min_value=1,
                max_value=50,
                value=3,
                help="Minimum units to recommend for transfer"
            )
        
        with col3:
            urgency_threshold = st.slider(
                "Urgency Threshold (days)",
                min_value=5,
                max_value=60,
                value=30,
                help="Days of stock to trigger urgent transfers"
            )
        
        # Store these in session state for use in analysis
        st.session_state.update({
            'transfer_analysis_days': analysis_days,
            'transfer_min_qty': min_transfer_qty,
            'transfer_urgency_threshold': urgency_threshold
        })

def _generate_transfer_recommendations(orders_df: pd.DataFrame, inventory_df: pd.DataFrame, 
                                     insights: List[ProductInsight], location_config: Dict[int, str]) -> List[Dict]:
    """Generate transfer recommendations based on inventory imbalances"""
    
    with st.spinner("🧠 Analyzing transfer opportunities..."):
        try:
            # Import your existing transfer engine
            from analysis.transfer_analysis import TransferAnalysisEngine
            
            user_profile = st.session_state.get('user_profile')
            analysis_days = st.session_state.get('transfer_analysis_days', 30)
            
            transfer_engine = TransferAnalysisEngine(location_config, user_profile)
            recommendations = transfer_engine.analyze_transfer_opportunities(
                orders_df, inventory_df, insights, analysis_days
            )
            
            return recommendations
            
        except ImportError:
            # Fallback: Generate basic recommendations if transfer engine not available
            return _generate_basic_transfer_recommendations(orders_df, inventory_df, location_config)
        except Exception as e:
            st.error(f"❌ Error generating transfer recommendations: {e}")
            return []

def _generate_basic_transfer_recommendations(orders_df: pd.DataFrame, inventory_df: pd.DataFrame, 
                                           location_config: Dict[int, str]) -> List[Dict]:
    """Generate basic transfer recommendations as fallback"""
    
    recommendations = []
    analysis_days = st.session_state.get('transfer_analysis_days', 30)
    min_transfer_qty = st.session_state.get('transfer_min_qty', 3)
    
    # Get recent orders for demand calculation
    recent_cutoff = orders_df['created_at'].max() - pd.Timedelta(days=analysis_days)
    recent_orders = orders_df[orders_df['created_at'] >= recent_cutoff]
    
    # Analyze each product
    for product_id in inventory_df['product_id'].unique():
        product_inventory = inventory_df[inventory_df['product_id'] == product_id]
        product_orders = recent_orders[recent_orders['product_id'] == product_id]
        
        if product_inventory.empty:
            continue
        
        # Get product info
        product_info = product_inventory.iloc[0]
        style_number = product_info.get('style_number', 'Unknown')
        description = product_info.get('description', 'Unknown')
        vendor = product_info.get('vendor', 'Unknown')
        
        # Calculate demand and inventory by location
        location_data = {}
        for location_id, location_name in location_config.items():
            inventory_col = f'inventory_{location_name.lower()}'
            current_inventory = product_info.get(inventory_col, 0) or 0
            
            # Calculate demand for this location
            location_orders = product_orders[product_orders['Store Location'] == location_name]
            total_sold = location_orders['quantity'].sum() if not location_orders.empty else 0
            daily_demand = total_sold / analysis_days if total_sold > 0 else 0
            days_of_stock = current_inventory / daily_demand if daily_demand > 0 else 999
            
            location_data[location_name] = {
                'inventory': current_inventory,
                'daily_demand': daily_demand,
                'days_of_stock': days_of_stock,
                'location_id': location_id
            }
        
        # Find transfer opportunities
        for from_location, from_data in location_data.items():
            for to_location, to_data in location_data.items():
                if from_location == to_location:
                    continue
                
                # Check if transfer makes sense
                if (from_data['days_of_stock'] > 60 and  # Source has excess
                    to_data['days_of_stock'] < 30 and    # Destination needs stock
                    from_data['inventory'] >= min_transfer_qty and  # Sufficient quantity
                    to_data['daily_demand'] > 0):        # Destination has demand
                    
                    # Calculate transfer quantity
                    excess_qty = max(0, from_data['inventory'] - (from_data['daily_demand'] * 45))
                    needed_qty = max(0, (to_data['daily_demand'] * 45) - to_data['inventory'])
                    transfer_qty = min(excess_qty, needed_qty, from_data['inventory'] // 2)
                    
                    if transfer_qty >= min_transfer_qty:
                        urgency = "URGENT" if to_data['days_of_stock'] < 14 else "HIGH" if to_data['days_of_stock'] < 30 else "MEDIUM"
                        
                        recommendations.append({
                            'product_id': product_id,
                            'style_number': style_number,
                            'description': description,
                            'vendor': vendor,
                            'from_location': from_location,
                            'to_location': to_location,
                            'from_inventory': from_data['inventory'],
                            'to_inventory': to_data['inventory'],
                            'from_days_stock': from_data['days_of_stock'],
                            'to_days_stock': to_data['days_of_stock'],
                            'transfer_qty': int(transfer_qty),
                            'urgency': urgency,
                            'potential_impact': transfer_qty * to_data['daily_demand'] * 30,  # 30-day impact
                            'reasoning': f"Transfer {int(transfer_qty)} units from {from_location} ({from_data['days_of_stock']:.0f} days stock) to {to_location} ({to_data['days_of_stock']:.0f} days stock)"
                        })
    
    # Sort by urgency and potential impact
    recommendations.sort(key=lambda x: (
        {'URGENT': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}.get(x['urgency'], 4),
        -x['potential_impact']
    ))
    
    return recommendations[:50]  # Limit to top 50 recommendations

def _show_transfer_overview(recommendations: List[Dict], location_config: Dict[int, str]):
    """Show transfer recommendations overview"""
    
    # Calculate overview metrics
    total_recommendations = len(recommendations)
    urgent_transfers = len([r for r in recommendations if r['urgency'] == 'URGENT'])
    high_priority = len([r for r in recommendations if r['urgency'] == 'HIGH'])
    total_units = sum([r['transfer_qty'] for r in recommendations])
    total_impact = sum([r['potential_impact'] for r in recommendations])
    
    st.markdown("### 📊 Transfer Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sharpstock_metric_card_enhanced(
            "Total Transfers",
            str(total_recommendations),
            "Recommended moves",
            "🔄",
            "primary"
        )
    
    with col2:
        sharpstock_metric_card_enhanced(
            "Urgent Transfers",
            str(urgent_transfers),
            f"{high_priority} high priority",
            "🚨",
            "error" if urgent_transfers > 0 else "success"
        )
    
    with col3:
        sharpstock_metric_card_enhanced(
            "Total Units",
            f"{total_units:,}",
            "Units to transfer",
            "📦",
            "primary"
        )
    
    with col4:
        sharpstock_metric_card_enhanced(
            "Potential Impact",
            f"${total_impact:,.0f}",
            "30-day revenue opportunity",
            "💰",
            "success"
        )
    
    # Show alerts for urgent transfers
    if urgent_transfers > 0:
        sharpstock_alert_banner(
            f"🚨 **{urgent_transfers} urgent transfers needed!** Some locations may stock out within 2 weeks without action.",
            "error"
        )
    elif high_priority > 0:
        sharpstock_alert_banner(
            f"⚠️ **{high_priority} high priority transfers recommended** to optimize inventory distribution.",
            "warning"
        )

def _show_transfer_recommendations(recommendations: List[Dict]):
    """Show detailed transfer recommendations"""
    
    st.markdown("---")
    st.markdown("### 🎯 Transfer Recommendations")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        urgency_filter = st.selectbox(
            "🚨 Filter by Urgency",
            ["All", "URGENT", "HIGH", "MEDIUM", "LOW"]
        )
    
    with col2:
        brands = sorted(list(set([r['vendor'] for r in recommendations if r['vendor'] != 'Unknown'])))
        brand_filter = st.selectbox("🏷️ Filter by Brand", ["All"] + brands)
    
    with col3:
        locations = sorted(list(set([r['to_location'] for r in recommendations])))
        location_filter = st.selectbox("📍 Filter by Destination", ["All"] + locations)
    
    # Apply filters
    filtered_recs = recommendations
    if urgency_filter != "All":
        filtered_recs = [r for r in filtered_recs if r['urgency'] == urgency_filter]
    if brand_filter != "All":
        filtered_recs = [r for r in filtered_recs if r['vendor'] == brand_filter]
    if location_filter != "All":
        filtered_recs = [r for r in filtered_recs if r['to_location'] == location_filter]
    
    if not filtered_recs:
        sharpstock_alert_banner("No transfers match the selected filters", "info")
        return
    
    # Display recommendations
    st.markdown(f"**🔄 Showing {len(filtered_recs)} transfer recommendations:**")
    
    for idx, rec in enumerate(filtered_recs[:20]):  # Limit to 20 for performance
        urgency_color = {
            'URGENT': '🔴',
            'HIGH': '🟠', 
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }.get(rec['urgency'], '⚪')
        
        with st.expander(
            f"{urgency_color} **{rec['style_number']}** - Transfer {rec['transfer_qty']} units from {rec['from_location']} → {rec['to_location']}",
            expanded=idx == 0 if rec['urgency'] == 'URGENT' else False
        ):
            
            # Transfer details
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**📦 Source Location**")
                st.metric(
                    f"{rec['from_location']}",
                    f"{rec['from_inventory']} units",
                    f"{rec['from_days_stock']:.0f} days stock"
                )
                excess_indicator = "🟢 Excess" if rec['from_days_stock'] > 60 else "🟡 Adequate"
                st.caption(excess_indicator)
            
            with col2:
                st.markdown("**🎯 Destination Location**") 
                days_color = "🔴" if rec['to_days_stock'] < 14 else "🟡" if rec['to_days_stock'] < 30 else "🟢"
                st.metric(
                    f"{rec['to_location']}",
                    f"{rec['to_inventory']} units", 
                    f"{days_color} {rec['to_days_stock']:.0f} days stock"
                )
                need_indicator = "🔴 Critical" if rec['to_days_stock'] < 14 else "🟡 Low" if rec['to_days_stock'] < 30 else "🟢 Adequate"
                st.caption(need_indicator)
            
            with col3:
                st.markdown("**💡 Transfer Impact**")
                st.metric(
                    "Recommended Transfer",
                    f"{rec['transfer_qty']} units",
                    f"${rec['potential_impact']:,.0f} impact"
                )
                st.caption(f"Urgency: {rec['urgency']}")
            
            # Product details
            st.markdown("**📋 Product Information**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Description:** {rec['description'][:60]}...")
                st.write(f"**Brand:** {rec['vendor']}")
            
            with col2:
                if st.button("📊 View Product Details", key=f"transfer_detail_{rec['product_id']}_{idx}"):
                    st.session_state['selected_product_id'] = rec['product_id']
                    st.session_state['selected_style_number'] = rec['style_number']
                    st.session_state['current_page'] = 'trends'
                    st.rerun()
            
            # Reasoning
            st.markdown("**🧠 Analysis**")
            st.info(rec['reasoning'])
            
            # Action buttons
            st.markdown("**⚡ Actions**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ Approve Transfer", key=f"approve_{idx}"):
                    st.success(f"Transfer approved: {rec['transfer_qty']} units {rec['from_location']} → {rec['to_location']}")
            
            with col2:
                if st.button("📋 Add to Transfer List", key=f"add_transfer_{idx}"):
                    _add_to_transfer_list(rec)
            
            with col3:
                if st.button("📞 Contact Store", key=f"contact_{idx}"):
                    st.info(f"Contact {rec['from_location']} and {rec['to_location']} stores about {rec['style_number']}")

def _show_transfer_analytics(recommendations: List[Dict], location_config: Dict[int, str]):
    """Show transfer analytics and insights"""
    
    st.markdown("---")
    st.markdown("### 📈 Transfer Analytics")
    
    if not recommendations:
        return
    
    # Location analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📤 Top Source Locations")
        source_counts = {}
        for rec in recommendations:
            source_counts[rec['from_location']] = source_counts.get(rec['from_location'], 0) + 1
        
        if source_counts:
            source_df = pd.DataFrame(list(source_counts.items()), columns=['Location', 'Transfers'])
            source_df = source_df.sort_values('Transfers', ascending=False)
            
            fig = create_sharpstock_chart_enhanced(
                source_df,
                chart_type="bar",
                title="Transfers FROM Locations",
                x='Location',
                y='Transfers',
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📥 Top Destination Locations")
        dest_counts = {}
        for rec in recommendations:
            dest_counts[rec['to_location']] = dest_counts.get(rec['to_location'], 0) + 1
        
        if dest_counts:
            dest_df = pd.DataFrame(list(dest_counts.items()), columns=['Location', 'Transfers'])
            dest_df = dest_df.sort_values('Transfers', ascending=False)
            
            fig = create_sharpstock_chart_enhanced(
                dest_df,
                chart_type="bar", 
                title="Transfers TO Locations",
                x='Location',
                y='Transfers',
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Brand analysis
    st.markdown("#### 🏷️ Transfers by Brand")
    brand_analysis = {}
    for rec in recommendations:
        brand = rec['vendor']
        if brand not in brand_analysis:
            brand_analysis[brand] = {'count': 0, 'total_units': 0, 'total_impact': 0}
        brand_analysis[brand]['count'] += 1
        brand_analysis[brand]['total_units'] += rec['transfer_qty']
        brand_analysis[brand]['total_impact'] += rec['potential_impact']
    
    if brand_analysis:
        brand_data = []
        for brand, data in brand_analysis.items():
            brand_data.append({
                'Brand': brand,
                'Transfer Count': data['count'],
                'Total Units': data['total_units'],
                'Potential Impact': f"${data['total_impact']:,.0f}"
            })
        
        brand_df = pd.DataFrame(brand_data)
        brand_df = brand_df.sort_values('Transfer Count', ascending=False)
        
        sharpstock_enhanced_table(brand_data, "Brand Transfer Summary")

def _show_no_transfers_needed():
    """Show when no transfers are recommended"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: rgba(16, 185, 129, 0.1); border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.3);">
            <div style="font-size: 4rem; margin-bottom: 1rem;">✅</div>
            <h2 style="color: #10B981; margin-bottom: 1rem;">Inventory Well Distributed!</h2>
            <p style="color: #9CA3AF; font-size: 1.1rem;">No transfer recommendations needed at this time. Your inventory appears to be optimally distributed across locations.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show some insights about why no transfers are needed
    st.markdown("---")
    st.markdown("### 💡 Inventory Distribution Insights")
    
    inventory_df = st.session_state.get('inventory_df', pd.DataFrame())
    location_config = st.session_state.get('location_config', {})
    
    if not inventory_df.empty and location_config:
        _show_inventory_distribution_summary(inventory_df, location_config)

def _show_inventory_distribution_summary(inventory_df: pd.DataFrame, location_config: Dict[int, str]):
    """Show summary of current inventory distribution"""
    
    # Calculate inventory by location
    location_totals = {}
    for location_id, location_name in location_config.items():
        inventory_col = f'inventory_{location_name.lower()}'
        if inventory_col in inventory_df.columns:
            total = inventory_df[inventory_col].sum()
            location_totals[location_name] = total
    
    if location_totals:
        col1, col2 = st.columns(2)
        
        with col1:
            # Inventory distribution chart
            location_df = pd.DataFrame(list(location_totals.items()), columns=['Location', 'Inventory'])
            
            fig = create_sharpstock_chart_enhanced(
                location_df,
                chart_type="pie",
                title="Current Inventory Distribution",
                values='Inventory',
                names='Location',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Location metrics
            total_inventory = sum(location_totals.values())
            for location, inventory in location_totals.items():
                percentage = (inventory / total_inventory * 100) if total_inventory > 0 else 0
                sharpstock_metric_card_enhanced(
                    location,
                    f"{inventory:,}",
                    f"{percentage:.1f}% of total",
                    "🏪",
                    "primary"
                )

def _add_to_transfer_list(transfer_rec: Dict):
    """Add transfer to a saved list"""
    
    if 'transfer_list' not in st.session_state:
        st.session_state['transfer_list'] = []
    
    # Check if already added
    existing = any(
        t['product_id'] == transfer_rec['product_id'] and 
        t['from_location'] == transfer_rec['from_location'] and
        t['to_location'] == transfer_rec['to_location']
        for t in st.session_state['transfer_list']
    )
    
    if existing:
        st.warning(f"⚠️ {transfer_rec['style_number']} transfer already in list")
    else:
        st.session_state['transfer_list'].append(transfer_rec)
        st.success(f"✅ Added {transfer_rec['style_number']} to transfer list")

def show_transfer_list():
    """Show saved transfer list (can be called from other pages)"""
    
    transfer_list = st.session_state.get('transfer_list', [])
    
    if not transfer_list:
        st.info("No transfers saved yet")
        return
    
    st.markdown("### 📋 Saved Transfer List")
    
    for idx, transfer in enumerate(transfer_list):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            st.write(f"**{transfer['style_number']}**")
            st.caption(transfer['vendor'])
        
        with col2:
            st.write(f"From: **{transfer['from_location']}**")
            st.caption(f"{transfer['from_inventory']} units")
        
        with col3:
            st.write(f"To: **{transfer['to_location']}**")
            st.caption(f"{transfer['transfer_qty']} units")
        
        with col4:
            if st.button("🗑️", key=f"remove_transfer_{idx}"):
                st.session_state['transfer_list'].pop(idx)
                st.rerun()
    
    # Export options
    if st.button("📥 Export Transfer List", type="primary"):
        transfer_df = pd.DataFrame(transfer_list)
        csv = transfer_df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            f"transfer_recommendations_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
