"""Product-focused UI components"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
from order_management.order_sheet_manager import OrderSheetManager
from order_management.smart_recommendations import add_all_variants_for_product_with_smart_recommendations
from models.data_models import ProductInsight, VariantDemand, OrderSheetItem

def display_product_detail_page(orders_df: pd.DataFrame, inventory_df: pd.DataFrame, product_id: int, style_number: str, location_config: Dict[int, str]):
    """Product detail page with comprehensive analysis"""
    
    st.header(f"📊 Product Analysis: {style_number}")
    
    # Back button
    if st.button("← Back to Dashboard", type="secondary"):
        st.session_state.pop('selected_product_id', None)
        st.session_state.pop('selected_style_number', None)
        st.rerun()
    
    # Get product data with error handling
    product_orders = pd.DataFrame()
    product_inventory = pd.DataFrame()
    
    try:
        # Convert product_id to int if it's not already
        product_id_int = int(product_id)
        
        # Filter orders
        if not orders_df.empty and 'product_id' in orders_df.columns:
            product_orders = orders_df[orders_df['product_id'] == product_id_int]
        
        # Filter inventory
        if not inventory_df.empty and 'product_id' in inventory_df.columns:
            product_inventory = inventory_df[inventory_df['product_id'] == product_id_int]
        
    except Exception as e:
        st.error(f"❌ Error filtering data: {e}")
        return
    
    if product_orders.empty and product_inventory.empty:
        st.error("❌ No data found for this product in either orders or inventory")
        return
    
    # Enhanced metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if not product_orders.empty:
            total_sold = product_orders['quantity'].sum()
            st.metric("Total Units Sold", f"{total_sold:,}")
        else:
            st.metric("Total Units Sold", "No data")
    
    with col2:
        if not product_orders.empty and 'total_value' in product_orders.columns:
            total_revenue = product_orders['total_value'].sum()
            st.metric("Total Revenue", f"${total_revenue:,.0f}")
        else:
            st.metric("Total Revenue", "No data")
    
    with col3:
        if not product_orders.empty:
            unique_orders = len(product_orders['order_number'].unique())
            st.metric("Number of Orders", unique_orders)
        else:
            st.metric("Number of Orders", "No data")
    
    with col4:
        if not product_inventory.empty:
            total_inv = product_inventory['total_inventory'].sum()
            st.metric("Current Inventory", f"{total_inv:,}")
        else:
            st.metric("Current Inventory", "No data")
    
    with col5:
        if not product_orders.empty:
            # Calculate daily demand
            date_range = (product_orders['created_at'].max() - product_orders['created_at'].min()).days + 1
            daily_demand = product_orders['quantity'].sum() / max(date_range, 1)
            st.metric("Daily Demand", f"{daily_demand:.1f}")
        else:
            st.metric("Daily Demand", "No data")
    
    # Product info
    if not product_orders.empty:
        product_info = product_orders.iloc[0]
        st.info(f"**Description:** {product_info.get('Description', 'No description')} | **Brand:** {product_info.get('vendor', 'Unknown')}")
    
    st.markdown("---")
    
    # 1. VARIANT SALES BAR CHART
    st.subheader("📊 Sales by Variant")
    
    if not product_orders.empty and 'variant_title' in product_orders.columns:
        # Filter out empty variant titles and group
        variant_orders = product_orders[product_orders['variant_title'].notna() & (product_orders['variant_title'] != '')]
        
        if not variant_orders.empty:
            variant_sales = variant_orders.groupby('variant_title').agg({
                'quantity': 'sum',
                'total_value': 'sum'
            }).reset_index().sort_values('quantity', ascending=False)
            
            if len(variant_sales) > 0:
                fig = px.bar(
                    variant_sales.head(15),  # Top 15 variants
                    x='variant_title',
                    y='quantity',
                    title=f"Units Sold by Variant - {style_number}",
                    labels={'variant_title': 'Variant', 'quantity': 'Units Sold'},
                    color='quantity',
                    color_continuous_scale='Blues'
                )
                fig.update_xaxes(tickangle=45)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Show variant summary table
                with st.expander("📋 Detailed Variant Sales"):
                    st.dataframe(variant_sales, use_container_width=True)
            else:
                st.info("No variant sales data found")
        else:
            st.info("No variant data available for sales analysis")
    else:
        st.info("No variant information available in orders")
    
    st.markdown("---")
    
    # 2. INVENTORY LEVELS BY STORE CHART
    st.subheader("📦 Current Inventory by Store")
    
    if not product_inventory.empty:
        # Aggregate inventory by location
        inventory_by_location = {}
        
        # Find inventory columns dynamically
        inventory_columns = [col for col in product_inventory.columns if col.startswith('inventory_')]
        
        for location_id, location_name in location_config.items():
            # Try different possible column name formats
            possible_column_names = [
                f'inventory_{location_name.lower()}',
                f'inventory_{location_name.lower().replace(" ", "_")}',
                f'inventory_{location_name}',
                f'{location_name.lower()}_inventory'
            ]
            
            total_inventory = 0
            column_found = False
            
            for column_name in possible_column_names:
                if column_name in product_inventory.columns:
                    total_inventory = product_inventory[column_name].sum()
                    inventory_by_location[location_name] = total_inventory
                    column_found = True
                    break
            
            if not column_found:
                inventory_by_location[location_name] = 0
        
        if any(qty > 0 for qty in inventory_by_location.values()):
            inv_df = pd.DataFrame(list(inventory_by_location.items()), 
                                columns=['Store Location', 'Inventory'])
            
            fig = px.bar(
                inv_df,
                x='Store Location',
                y='Inventory',
                title=f"Current Inventory Levels - {style_number}",
                labels={'Store Location': 'Store', 'Inventory': 'Units Available'},
                color='Inventory',
                color_continuous_scale='Greens'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ No inventory found at any location")
        
        # Show detailed inventory breakdown
        with st.expander("📋 Detailed Inventory by Variant & Store"):
            # Create enhanced inventory display
            inv_display_data = []
            for _, row in product_inventory.iterrows():
                variant_info = {
                    'Variant': row.get('variant_title', 'Unknown'),
                    'Color': row.get('color', ''),
                    'Size': row.get('size', '')
                }
                
                # Add location inventory using the found columns
                for location_id, location_name in location_config.items():
                    # Use the same logic as above to find the right column
                    possible_column_names = [
                        f'inventory_{location_name.lower()}',
                        f'inventory_{location_name.lower().replace(" ", "_")}',
                        f'inventory_{location_name}',
                        f'{location_name.lower()}_inventory'
                    ]
                    
                    inventory_qty = 0
                    for column_name in possible_column_names:
                        if column_name in row and row[column_name] is not None:
                            inventory_qty = int(row[column_name])
                            break
                    
                    variant_info[location_name] = inventory_qty
                
                variant_info['Total'] = int(row.get('total_inventory', 0))
                variant_info['Sold'] = int(row.get('total_sold', 0))
                
                inv_display_data.append(variant_info)
            
            if inv_display_data:
                inv_detail_df = pd.DataFrame(inv_display_data)
                st.dataframe(inv_detail_df, use_container_width=True, hide_index=True)
            else:
                st.warning("No detailed inventory data available")
    else:
        st.warning("⚠️ No inventory data available for this product")
        
        # Show helpful message for products with sales but no inventory
        if not product_orders.empty:
            st.info("""
            **This product has sales history but no current inventory data.**
            
            Possible reasons:
            • Product may be discontinued
            • Inventory not tracked in current system
            • Product sold out completely
            • Data sync issue between sales and inventory systems
            
            **Recommendation:** Check with your inventory management system or Shopify admin.
            """)
    
    st.markdown("---")
    
    # 3. SALES TREND OVER TIME
    st.subheader("📈 Sales Trend Analysis")
    
    if not product_orders.empty and len(product_orders) > 1:
        # Create time series analysis
        product_orders_copy = product_orders.copy()
        
        # Suppress the timezone warning
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # Group by week for trend visualization
            product_orders_copy['week'] = product_orders_copy['created_at'].dt.to_period('W')
            weekly_sales = product_orders_copy.groupby('week').agg({
                'quantity': 'sum',
                'total_value': 'sum'
            }).reset_index()
            weekly_sales['week'] = weekly_sales['week'].astype(str)
        
        # Create dual-axis chart
        fig = px.line(
            weekly_sales,
            x='week',
            y='quantity',
            title=f"Weekly Sales Trend - {style_number}",
            labels={'week': 'Week', 'quantity': 'Units Sold'},
            markers=True
        )
        
        # Add revenue as secondary y-axis (if there's significant data)
        if 'total_value' in weekly_sales.columns and weekly_sales['total_value'].sum() > 0:
            fig.add_scatter(
                x=weekly_sales['week'],
                y=weekly_sales['total_value'],
                mode='lines+markers',
                name='Revenue ($)',
                yaxis='y2',
                line=dict(color='green', dash='dash')
            )
            
            # Update layout for dual axis
            fig.update_layout(
                yaxis=dict(title='Units Sold', side='left'),
                yaxis2=dict(title='Revenue ($)', side='right', overlaying='y'),
                height=400
            )
        
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Sales trend insights
        with st.expander("📊 Trend Insights"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_weekly = weekly_sales['quantity'].mean()
                st.metric("Avg Weekly Sales", f"{avg_weekly:.1f}")
            
            with col2:
                peak_week = weekly_sales.loc[weekly_sales['quantity'].idxmax()]
                st.metric("Peak Week", f"{peak_week['quantity']} units")
                st.caption(f"Week of {peak_week['week']}")
            
            with col3:
                total_weeks = len(weekly_sales)
                st.metric("Weeks with Sales", total_weeks)
                
                # Calculate trend direction
                if total_weeks >= 4:
                    recent_avg = weekly_sales.tail(2)['quantity'].mean()
                    earlier_avg = weekly_sales.head(2)['quantity'].mean()
                    if recent_avg > earlier_avg * 1.1:
                        st.success("📈 Trending Up")
                    elif recent_avg < earlier_avg * 0.9:
                        st.error("📉 Trending Down") 
                    else:
                        st.info("➡️ Stable")
    else:
        st.info("Need more sales data points for trend analysis")
    
    # Quick Actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 View All Variants", use_container_width=True):
            if not product_inventory.empty:
                st.info("Detailed variant data shown above in inventory section")
            else:
                st.warning("No variant data available")
    
    with col2:
        if st.button("📈 Export Sales Data", use_container_width=True):
            if not product_orders.empty:
                csv = product_orders.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"sales_{style_number}_{product_id}.csv",
                    "text/csv",
                    key="product_sales_download"
                )
            else:
                st.warning("No sales data to export")
    
    with col3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.info("Data refresh functionality - implement cache invalidation")

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

def display_enhanced_variant_breakdown(
    selected_insight: ProductInsight,
    orders_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    location_config: Dict[int, str],
    order_manager: OrderSheetManager,
    selected_brand: str,
    analysis_days: int = 30
):
    """Enhanced variant breakdown with demand analysis and smart recommendations"""
    
    product_id = selected_insight.product_id
    
    # Get variants for this product
    product_variants = inventory_df[inventory_df['product_id'] == product_id]
    
    if product_variants.empty:
        st.warning("No variant data found for this product")
        return
    
    # Enhanced product information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📊 Product Overview**")
        st.write(f"**Style:** {selected_insight.style_number}")
        st.write(f"**Description:** {selected_insight.description}")
        st.write(f"**Priority:** {selected_insight.reorder_priority}")
        st.write(f"**Timing:** {selected_insight.reorder_timing}")
    
    with col2:
        st.markdown("**📈 Performance Metrics**")
        st.write(f"**Daily Demand:** {selected_insight.recent_daily_demand:.1f} units")
        st.write(f"**Recent Sales:** {selected_insight.recent_total_sales:,} units")
        st.write(f"**Trend:** {selected_insight.trend_classification}")
        st.write(f"**Velocity Change:** {selected_insight.velocity_change:+.1f}%")
    
    with col3:
        st.markdown("**📦 Inventory Status**")
        st.write(f"**Current Inventory:** {selected_insight.current_inventory:,} units")
        st.write(f"**Days Until Stockout:** {selected_insight.days_until_stockout}")
        st.write(f"**Total Recommended:** {selected_insight.recommended_qty:,} units")
        st.write(f"**Turnover Rate:** {selected_insight.inventory_turnover:.1f}x")
    
    # Calculate variant-specific demand patterns
    recent_cutoff = orders_df['created_at'].max() - pd.Timedelta(days=analysis_days)
    recent_orders = orders_df[
        (orders_df['product_id'] == product_id) & 
        (orders_df['created_at'] >= recent_cutoff)
    ]
    
    st.markdown("---")
    st.markdown("**🎯 Smart Variant Recommendations**")
    st.caption(f"Based on {analysis_days}-day demand analysis with store-specific patterns")
    
    # Enhanced variant table
    cols = st.columns([2, 2, 1, 1, 1, 1, 1, 1, 1])
    headers = ["Color", "Size", "Total Inv", "Hilo", "Kailua", "Kapaa", "Wailuku", "Rec. Qty", "Action"]
    for i, header in enumerate(headers):
        with cols[i]:
            st.markdown(f"**{header}**")
    
    st.markdown("---")
    
    # Display each variant with enhanced calculations
    for idx, (_, variant) in enumerate(product_variants.iterrows()):
        variant_id = variant['variant_id']
        
        # Calculate variant-specific recommendations
        variant_orders = recent_orders[recent_orders['variant_id'] == variant_id]
        variant_recent_sales = variant_orders['quantity'].sum()
        
        # Calculate store-specific demand for this variant
        store_recommendations = {}
        for store_name in location_config.values():
            store_orders = variant_orders[variant_orders['Store Location'] == store_name]
            store_sales = store_orders['quantity'].sum()
            store_daily_demand = store_sales / analysis_days if store_sales > 0 else 0
            
            # Current inventory for this store
            inventory_col = f'inventory_{store_name.lower()}'
            current_inv = variant.get(inventory_col, 0) or 0
            
            # Calculate recommendation (45 days supply)
            if store_daily_demand > 0:
                target_inv = store_daily_demand * 45
                needed = max(0, target_inv - current_inv)
                store_recommendations[store_name] = max(1, int(needed)) if needed > 0.5 else 0
            else:
                store_recommendations[store_name] = 0
        
        total_recommended = sum(store_recommendations.values())
        
        cols = st.columns([2, 2, 1, 1, 1, 1, 1, 1, 1])
        
        with cols[0]:
            st.write(variant.get('color', 'Unknown'))
        
        with cols[1]:
            st.write(variant.get('size', 'Unknown'))
        
        with cols[2]:
            total_inv = variant.get('total_inventory', 0)
            if total_inv < 5:
                st.markdown(f"<span style='color: red'>{total_inv}</span>", unsafe_allow_html=True)
            else:
                st.write(f"{total_inv}")
        
        # Current inventory by store
        with cols[3]:
            st.write(f"{variant.get('inventory_hilo', 0)}")
        with cols[4]:
            st.write(f"{variant.get('inventory_kailua', 0)}")
        with cols[5]:
            st.write(f"{variant.get('inventory_kapaa', 0)}")
        with cols[6]:
            st.write(f"{variant.get('inventory_wailuku', 0)}")
        
        with cols[7]:
            if total_recommended > 0:
                st.markdown(f"<span style='color: green; font-weight: bold'>{total_recommended}</span>", unsafe_allow_html=True)
            else:
                st.write("0")
        
        with cols[8]:
            # Smart add individual variant
            if st.button("➕", key=f"add_variant_{idx}_{variant_id}"):
                order_item = OrderSheetItem(
                    product_id=int(product_id),
                    variant_id=int(variant_id),
                    style_number=selected_insight.style_number,
                    description=selected_insight.description,
                    color=str(variant.get('color', '')),
                    size=str(variant.get('size', '')),
                    vendor=selected_brand,
                    qty_hilo=store_recommendations.get('Hilo', 0),
                    qty_kailua=store_recommendations.get('Kailua', 0),
                    qty_kapaa=store_recommendations.get('Kapaa', 0),
                    qty_wailuku=store_recommendations.get('Wailuku', 0),
                    priority=selected_insight.reorder_priority,
                    notes=f"Smart recommendation based on {analysis_days}-day analysis"
                )
                
                if selected_brand not in order_manager.selected_items:
                    order_manager.selected_items[selected_brand] = []
                
                # Check if already exists
                existing = next((item for item in order_manager.selected_items[selected_brand] 
                               if item.variant_id == variant_id), None)
                
                if not existing:
                    order_manager.selected_items[selected_brand].append(order_item)
                    st.success(f"Added variant with {total_recommended} total units")
                    st.rerun()
                else:
                    st.warning("Variant already in order sheet")
        
        # Show detailed breakdown for variants with recommendations
        if total_recommended > 0:
            with st.expander(f"📊 Demand Analysis - {variant.get('color', 'Unknown')}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Recent Performance ({analysis_days} days):**")
                    st.write(f"• Total sold: {variant_recent_sales} units")
                    st.write(f"• Daily average: {variant_recent_sales / analysis_days:.2f}")
                    
                    if variant_recent_sales > 0:
                        st.write(f"**Store Distribution:**")
                        for store_name in location_config.values():
                            store_orders = variant_orders[variant_orders['Store Location'] == store_name]
                            store_sales = store_orders['quantity'].sum()
                            pct = (store_sales / variant_recent_sales) * 100 if variant_recent_sales > 0 else 0
                            st.write(f"• {store_name}: {store_sales} units ({pct:.0f}%)")
                
                with col2:
                    st.write(f"**Recommendations by Store:**")
                    for store_name, rec_qty in store_recommendations.items():
                        if rec_qty > 0:
                            inventory_col = f'inventory_{store_name.lower()}'
                            current_inv = variant.get(inventory_col, 0) or 0
                            st.write(f"• {store_name}: {rec_qty} units (current: {current_inv})")
    
    # Quick action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧠 Add All Variants (Smart)", type="primary"):
            added = add_all_variants_for_product_with_smart_recommendations(
                product_id, selected_insight.style_number, selected_brand,
                orders_df, inventory_df, location_config, order_manager,
                selected_insight, analysis_days
            )
            
            if added > 0:
                total_units = sum([
                    item.qty_hilo + item.qty_kailua + item.qty_kapaa + item.qty_wailuku 
                    for item in order_manager.selected_items.get(selected_brand, [])
                    if item.product_id == product_id
                ])
                st.success(f"Added {added} variants with smart recommendations ({total_units} total units)")
                st.rerun()
    
    with col2:
        if st.button("📊 View Product Detail"):
            st.session_state['selected_product_id'] = product_id
            st.session_state['selected_style_number'] = selected_insight.style_number
            st.rerun()
    
    with col3:
        if st.button("⬅️ Back to Products"):
            st.session_state.pop('selected_style_for_variants', None)
            st.rerun()