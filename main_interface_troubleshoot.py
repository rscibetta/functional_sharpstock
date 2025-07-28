"""
SharpStock Main Interface - Part 1: Imports and Setup
Professional implementation with enterprise UI integration
"""
import streamlit as st

# CRITICAL: Set page config FIRST, before any other imports that might use Streamlit
st.set_page_config(
    page_title="SharpStock - Advanced Business Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# TRY TO IMPORT ENTERPRISE UI - WITH FALLBACKS
try:
    from ui.enterprise_styles import apply_enterprise_styles
    from ui.enterprise_components import (
        enterprise_page_header,
        enterprise_metric_card,
        enterprise_metric_dashboard,
        enterprise_alert,
        enterprise_section_header,
        enterprise_status_badge,
        render_empty_state
    )
    from ui.enterprise_navigation import enterprise_sidebar_navigation
    
    # Apply enterprise styling
    apply_enterprise_styles()
    
    ENTERPRISE_UI_AVAILABLE = True
    
except ImportError as e:
    ENTERPRISE_UI_AVAILABLE = False
    
    # Create fallback functions
    def apply_enterprise_styles():
        pass
    
    def enterprise_page_header(title, subtitle="", icon="", show_back_button=False):
        st.title(f"{icon} {title}" if icon else title)
        if subtitle:
            st.caption(subtitle)
    
    def enterprise_metric_card(title, value, delta="", delta_type="neutral", icon="📊", help_text="", variant="default"):
        st.metric(title, value, delta, help=help_text)
    
    def enterprise_metric_dashboard(metrics_data, columns=4):
        cols = st.columns(min(len(metrics_data), columns))
        for i, metric in enumerate(metrics_data):
            with cols[i % columns]:
                st.metric(
                    metric.get('title', 'Metric'),
                    metric.get('value', '0'),
                    metric.get('delta', '')
                )
    
    def enterprise_alert(message, alert_type="info"):
        if alert_type == "success":
            st.success(message)
        elif alert_type == "warning":
            st.warning(message)
        elif alert_type == "error":
            st.error(message)
        else:
            st.info(message)
    
    def enterprise_section_header(title, description="", icon=""):
        st.subheader(f"{icon} {title}" if icon else title)
        if description:
            st.caption(description)
    
    def enterprise_status_badge(status, variant="default", size="md", pulse=False):
        return f"**{status}**"
    
    def render_empty_state(title="No Data", description="", icon="📭", action_label=None, action_callback=None):
        st.info(f"{icon} **{title}** - {description}")
        if action_label and action_callback:
            if st.button(action_label):
                action_callback()
    
    def enterprise_sidebar_navigation():
        st.sidebar.title("⚡ SharpStock")
        
        # Simple navigation
        pages = [
            ("🏠 Dashboard", "dashboard"),
            ("🚨 Reorder Alerts", "reorder"),
            ("📈 Trend Analysis", "trends"),
            ("🔄 Transfers", "transfers"),
            ("📋 Orders", "orders"),
            ("📦 Pending Orders", "pending"),
            ("⚙️ Settings", "profile")
        ]
        
        for label, page_key in pages:
            if st.sidebar.button(label, key=f"nav_{page_key}"):
                st.session_state['current_page'] = page_key
                st.rerun()

# Now do all other imports
import pandas as pd
import time
import logging
import traceback
from datetime import datetime, timedelta
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Core imports - these must work for the app to function
from database.database_manager import DatabaseManager
from auth.auth_manager import AuthenticationManager
from models.data_models import UserProfile
from shopify.client import AdvancedShopifyClient
from analysis.business_intelligence import EnhancedBusinessIntelligenceEngine
from utils.data_processing import process_orders_fast, create_inventory_dataframe_fast, get_demo_profile

# Optional imports with error handling
try:
    from pending_orders.pending_order_manager import PendingOrderManager
    from ui.pending_order_components import display_pending_orders_interface, display_pending_orders_alert
    PENDING_ORDERS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Pending orders not available: {e}")
    PENDING_ORDERS_AVAILABLE = False
    PendingOrderManager = None
    display_pending_orders_interface = None
    display_pending_orders_alert = lambda: None

# UI imports with fallbacks
try:
    from ui.components import (
        apply_sharpstock_branding, 
        apply_minimal_css,
        sharpstock_metric_card,
        sharpstock_section_header,
        sharpstock_info_box,
        sharpstock_page_header,
        sharpstock_sidebar_header,
        sharpstock_metric_dashboard
    )
    UI_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"UI components import error: {e}")
    UI_COMPONENTS_AVAILABLE = False
    # Create fallback functions
    def apply_sharpstock_branding():
        st.title("⚡ SharpStock")
    def apply_minimal_css():
        pass
    def sharpstock_metric_card(title, value, delta="", icon=""):
        st.metric(title, value, delta)
    def sharpstock_section_header(title, subtitle=""):
        st.subheader(title)
        if subtitle:
            st.caption(subtitle)
    def sharpstock_info_box(message, box_type="info"):
        if box_type == "success":
            st.success(message)
        elif box_type == "warning":
            st.warning(message)
        elif box_type == "error":
            st.error(message)
        else:
            st.info(message)
    def sharpstock_page_header(title, subtitle="", icon=""):
        st.title(f"{icon} {title}" if icon else title)
        if subtitle:
            st.caption(subtitle)
    def sharpstock_sidebar_header():
        st.sidebar.title("⚡ SharpStock")
    def sharpstock_metric_dashboard(metrics_data, title=""):
        if title:
            st.subheader(title)
        cols = st.columns(len(metrics_data))
        for i, metric in enumerate(metrics_data):
            with cols[i]:
                st.metric(
                    metric.get('title', 'Metric'),
                    metric.get('value', '0'),
                    metric.get('delta', '')
                )

def safe_error_handler(func):
    """Decorator for safe error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            st.error(f"❌ Error in {func.__name__}: {str(e)}")
            return None
    return wrapper

"""
SharpStock Main Interface - Part 2: Core Functions
Profile management and analysis interface functions
"""

@safe_error_handler
def integrate_pending_orders_if_enabled(inventory_df, user_profile, location_config):
    """Integrate pending orders into inventory if enabled"""
    
    # Check if pending orders are uploaded
    pending_uploaded = st.session_state.get('pending_orders_uploaded', False)
    
    if not pending_uploaded:
        return inventory_df
    
    # Check if re-analysis is triggered
    trigger_reanalysis = st.session_state.get('trigger_reanalysis_with_pending', False)
    
    try:
        pending_manager = PendingOrderManager(user_profile, location_config)
        pending_orders = pending_manager.load_pending_orders()
        
        if pending_orders:
            st.info(f"📦 Including {len(pending_orders)} pending order items in analysis...")
            
            # Use the inventory integration method
            updated_inventory_df = pending_manager.debug_inventory_integration(inventory_df, pending_orders)
            
            # Set flag to show pending orders are active
            st.session_state['analysis_includes_pending'] = True
            
            # Clear the trigger for next time
            st.session_state['trigger_reanalysis_with_pending'] = False
            
            return updated_inventory_df
                        
    except Exception as e:
        st.error(f"❌ Error integrating pending orders: {e}")
    
    return inventory_df

def show_profile_management_tab(db_manager: DatabaseManager, user_id: str):
    """Profile management with comprehensive error handling"""
    
    try:
        # Page header
        sharpstock_page_header(
            "👤 Profile Management",
            "Configure your store settings and manage your SharpStock account"
        )
        
        # Load current profile safely
        profile = None
        try:
            profile = db_manager.load_user_profile(user_id)
        except Exception as e:
            st.warning(f"⚠️ Could not load profile: {e}")
        
        # Store Configuration Section
        sharpstock_section_header("🏪 Store Configuration", "Connect your Shopify store to SharpStock")
        
        col1, col2 = st.columns(2)
        
        with col1:
            shop_name = st.text_input(
                "🏬 Shop Name", 
                value=profile.shop_name if profile else "",
                help="Your Shopify store name (e.g., 'my-store' from my-store.myshopify.com)"
            )
            
            # API token input with safe handling
            if profile and hasattr(profile, 'encrypted_api_token') and profile.encrypted_api_token:
                api_token = st.text_input(
                    "🔐 API Access Token", 
                    type="password", 
                    value="[TOKEN SAVED]", 
                    help="Your Shopify Admin API access token (encrypted and stored securely)"
                )
                update_token = api_token != "[TOKEN SAVED]"
            else:
                api_token = st.text_input(
                    "🔐 API Access Token", 
                    type="password", 
                    help="Your Shopify Admin API access token - this will be encrypted for security"
                )
                update_token = True
        
        with col2:
            # Default lead time
            default_lead_time = st.number_input(
                "📅 Default Lead Time (days)", 
                min_value=1, 
                max_value=60, 
                value=profile.default_lead_time if profile else 14,
                help="Default lead time for suppliers in days"
            )
            
            # Location display
            st.markdown("**📍 Store Locations:**")
            if profile and hasattr(profile, 'location_config'):
                try:
                    for loc_id, loc_name in profile.location_config.items():
                        st.markdown(f"• **{loc_name}** (ID: {loc_id})")
                except Exception as e:
                    st.warning(f"⚠️ Could not display locations: {e}")
            else:
                sharpstock_info_box("Standard Hawaii locations will be configured after saving", "info")
        
        # Save button with error handling
        if st.button("💾 Save Store Configuration", type="primary", use_container_width=True):
            if shop_name and api_token:
                try:
                    # Use the existing location config
                    location_config = {
                        65859125301: 'Hilo',
                        36727324725: 'Kailua', 
                        36727390261: 'Kapaa',
                        1223720986: 'Wailuku'
                    }
                    
                    # Handle token encryption safely
                    encrypted_token = None
                    try:
                        if update_token and api_token != "[TOKEN SAVED]":
                            encrypted_token = db_manager.encrypt_token(api_token)
                        elif profile and hasattr(profile, 'encrypted_api_token'):
                            encrypted_token = profile.encrypted_api_token
                        else:
                            encrypted_token = db_manager.encrypt_token(api_token)
                    except Exception as e:
                        st.error(f"❌ Token encryption failed: {e}")
                        return
                    
                    new_profile = UserProfile(
                        user_id=user_id,
                        username=profile.username if profile else "",
                        email=profile.email if profile else "",
                        shop_name=shop_name,
                        encrypted_api_token=encrypted_token,
                        location_config=location_config,
                        default_lead_time=default_lead_time,
                        created_at=profile.created_at if profile else datetime.now(),
                        last_cache_update=profile.last_cache_update if profile else None
                    )
                    
                    if db_manager.save_user_profile(new_profile):
                        st.success("✅ Configuration saved successfully!")
                        st.session_state['user_profile'] = new_profile
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to save configuration")
                        
                except Exception as e:
                    st.error(f"❌ Save failed: {e}")
            else:
                st.error("❌ Please fill in all required fields")
        
        # Connection Status
        if profile and hasattr(profile, 'shop_name') and hasattr(profile, 'encrypted_api_token'):
            if profile.shop_name and profile.encrypted_api_token:
                sharpstock_info_box(
                    "✅ **Store Connected Successfully!** You can now run analysis in the Analysis tab.",
                    "success"
                )
            else:
                sharpstock_info_box(
                    "⚠️ **Store Configuration Required** Please complete store configuration to enable analysis.",
                    "warning"
                )
        else:
            sharpstock_info_box(
                "⚠️ **Profile Not Found** Please complete your store configuration.",
                "warning"
            )
        
        # Brand Lead Times Management (if profile exists)
        if profile and hasattr(profile, 'shop_name') and profile.shop_name:
            try:
                st.markdown("---")
                sharpstock_section_header(
                    "🏷️ Brand Lead Times",
                    "Configure specific lead times for different brands/suppliers"
                )
                
                brand_lead_times = {}
                try:
                    brand_lead_times = db_manager.get_brand_lead_times(user_id)
                except Exception as e:
                    st.warning(f"⚠️ Could not load brand lead times: {e}")
                
                # Display existing brand lead times
                if brand_lead_times:
                    st.markdown("**Current Brand Configurations:**")
                    
                    # Create metrics data for dashboard
                    brand_metrics = []
                    for brand, lead_time in list(brand_lead_times.items())[:6]:  # Limit to 6
                        brand_metrics.append({
                            'title': brand,
                            'value': f'{lead_time} days',
                            'delta': 'Lead time',
                            'icon': '🏷️'
                        })
                    
                    if brand_metrics:
                        sharpstock_metric_dashboard(brand_metrics)
                
                # Add new brand lead time
                st.markdown("**➕ Add New Brand Lead Time:**")
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    new_brand = st.text_input(
                        "Brand Name", 
                        key="new_brand_input",
                        placeholder="Enter brand/supplier name"
                    )
                with col2:
                    new_lead_time = st.number_input(
                        "Lead Time (days)", 
                        min_value=1, 
                        max_value=180, 
                        value=14, 
                        key="new_brand_lead_time"
                    )
                with col3:
                    st.write("")  # Spacer
                    if st.button("➕ Add Brand", type="secondary"):
                        if new_brand:
                            try:
                                if db_manager.save_brand_lead_time(user_id, new_brand, new_lead_time):
                                    st.success(f"✅ Lead time for {new_brand} saved!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to save brand lead time")
                            except Exception as e:
                                st.error(f"❌ Error saving brand: {e}")
                
            except Exception as e:
                st.error(f"❌ Error in brand management section: {e}")
        
    except Exception as e:
        st.error(f"❌ Error in profile management: {e}")

@safe_error_handler
def show_analysis_interface(db_manager: DatabaseManager, user_id: str, profile: UserProfile):
    """Analysis interface with comprehensive error handling"""
    
    try:
        # Page header
        sharpstock_page_header(
            "📊 SharpStock Business Intelligence",
            "Advanced AI-powered analytics for your inventory and sales data",
            "⚡"
        )
        
        # Check profile status for non-demo users
        if not st.session_state.get('demo_mode', False):
            try:
                profile = db_manager.load_user_profile(user_id)
                if not profile or not hasattr(profile, 'shop_name') or not profile.shop_name:
                    sharpstock_info_box(
                        "⚠️ **Store Configuration Required** Please complete your store configuration in the Profile Management tab first.",
                        "warning"
                    )
                    
                    if st.button("🔄 Refresh Profile Status", type="secondary"):
                        st.rerun()
                    return
                    
                if not hasattr(profile, 'encrypted_api_token') or not profile.encrypted_api_token:
                    sharpstock_info_box(
                        "⚠️ **API Token Required** Please add your Shopify API token in Profile Management.",
                        "warning"
                    )
                    return
                    
            except Exception as e:
                st.error(f"❌ Profile validation error: {e}")
                return
        
        # Get credentials with error handling
        try:
            if st.session_state.get('demo_mode', False):
                shop_name = "naturally-birkenstock"
                api_version = "2023-10"
                access_token = "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"
                location_config = get_demo_profile().location_config
                
                sharpstock_info_box("🚀 **Demo Mode Active** - Using sample data for demonstration", "info")
            else:
                shop_name = profile.shop_name
                api_version = "2023-10"
                try:
                    access_token = db_manager.decrypt_token(profile.encrypted_api_token)
                    location_config = profile.location_config
                    
                    sharpstock_info_box(f"✅ **Connected to {profile.shop_name}** - Ready for analysis", "success")
                except Exception as e:
                    sharpstock_info_box(
                        "❌ **Authentication Error** Failed to decrypt API token. Please update your credentials in Profile Management.",
                        "error"
                    )
                    if st.button("🔄 Refresh Profile", type="secondary"):
                        st.rerun()
                    return
        except Exception as e:
            st.error(f"❌ Credential setup error: {e}")
            return
        
        # Enhanced analysis configuration in sidebar
        with st.sidebar:
            try:
                sharpstock_sidebar_header()
                
                sharpstock_section_header("⚙️ Analysis Configuration")
                
                # User context
                if st.session_state.get('demo_mode', False):
                    sharpstock_metric_card("Mode", "Demo", "Sample data", icon="🎮")
                else:
                    sharpstock_metric_card("User", profile.username if profile else "Unknown", 
                                         profile.shop_name if profile else "Unknown", icon="👤")
                
                # Analysis period
                st.markdown("**📅 Analysis Period**")
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start", value=datetime.now() - timedelta(days=30))
                with col2:
                    end_date = st.date_input("End", value=datetime.now())
                
                # Historical data selection
                st.markdown("**📚 Historical Analysis**")
                historical_years = st.selectbox(
                    "Historical period:",
                    options=[1, 2, 3, 4, 5],
                    index=1,
                    help="Choose how many years of historical data to use for trend analysis"
                )
                
                # Location selection
                st.markdown("**📍 Store Locations**")
                try:
                    location_options = list(location_config.values()) if location_config else ['Default Store']
                    selected_locations = st.multiselect(
                        "Select locations:",
                        options=location_options,
                        default=location_options,
                        help="Choose which store locations to include in analysis"
                    )
                    location_ids = [k for k, v in location_config.items() if v in selected_locations] if location_config else [1]
                except Exception as e:
                    st.warning(f"⚠️ Location setup error: {e}")
                    location_ids = [1]
                    selected_locations = ['Default Store']
                
                # Analysis settings
                st.markdown("**🔧 Analysis Settings**")
                test_mode = st.checkbox("⚡ Quick Test Mode", value=True, help="Analyze top 50 products only for faster testing")
                safe_mode = st.checkbox("🛡️ Safe Mode", value=True, help="Use minimal data processing to avoid errors")
                use_cache = st.checkbox("📚 Use Cached Data", value=True, help="Use previously downloaded historical data when available")
                
            except Exception as e:
                st.error(f"❌ Sidebar configuration error: {e}")
                # Set defaults
                location_ids = [1]
                test_mode = True
                safe_mode = True
                use_cache = False
        
        # Enhanced analysis button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            analysis_button = st.button(
                "🚀 Run Advanced Analysis", 
                type="primary", 
                use_container_width=True,
                help="Launch comprehensive AI-powered business intelligence analysis"
            )
        
        if analysis_button:
            if not location_ids:
                sharpstock_info_box("❌ Please select at least one store location", "error")
                return
            
            # Professional loading screen with error handling
            with st.spinner("⚡ Analyzing your data with AI..."):
                start_time = time.time()
                
                try:
                    # Step 1: Initialize client with error handling
                    try:
                        client = AdvancedShopifyClient(shop_name, api_version, access_token, location_ids)
                    except Exception as e:
                        st.error(f"❌ Failed to initialize Shopify client: {e}")
                        return
                    
                    # Step 2: Load brand lead times safely
                    brand_lead_times = {}
                    try:
                        if not st.session_state.get('demo_mode', False):
                            brand_lead_times = db_manager.get_brand_lead_times(user_id)
                    except Exception as e:
                        pass  # Continue with empty brand lead times
                    
                    # Step 3: Initialize business intelligence engine
                    try:
                        bi_engine = EnhancedBusinessIntelligenceEngine(profile, brand_lead_times)
                    except Exception as e:
                        st.error(f"❌ Failed to initialize BI engine: {e}")
                        return
                    
                    # Step 4: Fetch order data with comprehensive error handling
                    recent_orders = []
                    historical_orders = []
                    
                    try:
                        # FIXED: Handle the return value properly
                        result = client.fetch_comprehensive_orders(
                            datetime.combine(start_date, datetime.min.time()),
                            datetime.combine(end_date, datetime.max.time()),
                            use_cache=use_cache,
                            user_id=user_id,
                            db_manager=db_manager,
                            historical_years=historical_years
                        )
                        
                        # Check if result is a tuple or single value
                        if isinstance(result, tuple) and len(result) == 2:
                            recent_orders, historical_orders = result
                        else:
                            # If it returns a single value, treat it as recent orders
                            recent_orders = result if result else []
                            historical_orders = []
                        
                        # Apply safe mode limits
                        if safe_mode:
                            if recent_orders and len(recent_orders) > 100:
                                recent_orders = recent_orders[:100]
                                st.info("🛡️ Safe mode: Limited to 100 recent orders")
                            if historical_orders and len(historical_orders) > 200:
                                historical_orders = historical_orders[:200]
                                st.info("🛡️ Safe mode: Limited to 200 historical orders")
                        
                    except Exception as e:
                        st.error(f"❌ Failed to fetch order data: {e}")
                        return

                    if not recent_orders and not historical_orders:
                        sharpstock_info_box("⚠️ No order data found for analysis. Try adjusting your date range or check your API connection.", "warning")
                        return
                    
                    # Step 5: Process order data safely
                    recent_orders_df = pd.DataFrame()
                    historical_orders_df = pd.DataFrame()
                    
                    try:
                        if recent_orders:
                            recent_orders_df = process_orders_fast(recent_orders, location_config)
                    except Exception as e:
                        st.warning(f"⚠️ Error processing recent orders: {e}")
                    
                    try:
                        if historical_orders:
                            historical_orders_df = process_orders_fast(historical_orders, location_config)
                    except Exception as e:
                        st.warning(f"⚠️ Error processing historical orders: {e}")
                    
                    # Combine for product identification
                    all_orders_df = pd.DataFrame()
                    try:
                        if not recent_orders_df.empty and not historical_orders_df.empty:
                            all_orders_df = pd.concat([recent_orders_df, historical_orders_df], ignore_index=True)
                        elif not recent_orders_df.empty:
                            all_orders_df = recent_orders_df.copy()
                        elif not historical_orders_df.empty:
                            all_orders_df = historical_orders_df.copy()
                            
                    except Exception as e:
                        st.error(f"❌ Error combining order data: {e}")
                        return
                    
                    if all_orders_df.empty:
                        sharpstock_info_box("⚠️ No valid order data after processing", "warning")
                        return
                    
                    # Step 6: Determine products to analyze
                    try:
                        if test_mode:
                            top_products = all_orders_df.groupby('product_id')['quantity'].sum().sort_values(ascending=False).head(50).index.tolist()
                            product_ids = top_products
                            st.info("⚡ Quick test mode: Analyzing top 50 products")
                        else:
                            product_ids = all_orders_df['product_id'].unique().tolist()
                            
                    except Exception as e:
                        st.error(f"❌ Error determining products: {e}")
                        return
                    
                    # Step 7: Fetch variants and inventory
                    variants_data = {}
                    inventory_levels = {}
                    
                    try:
                        result = client.fetch_variants_and_inventory(product_ids)
                        if isinstance(result, tuple) and len(result) == 2:
                            variants_data, inventory_levels = result
                        else:
                            variants_data = result if result else {}
                            inventory_levels = {}
                            
                    except Exception as e:
                        st.warning(f"⚠️ Error fetching variants/inventory: {e}")
                        # Continue with empty data
                    
                    # Step 8: Create inventory dataframe
                    inventory_df = pd.DataFrame()
                    try:
                        inventory_df = create_inventory_dataframe_fast(all_orders_df, variants_data, inventory_levels, location_config)
                    except Exception as e:
                        st.warning(f"⚠️ Error creating inventory dataframe: {e}")
                    
                    # Step 8.5: Integrate pending orders if enabled
                    try:
                        inventory_df = integrate_pending_orders_if_enabled(
                            inventory_df, profile, location_config
                        )
                    except Exception as e:
                        st.warning(f"⚠️ Error integrating pending orders: {e}")

                    # Step 9: Run business intelligence analysis
                    insights = []
                    seasonal_insights = []
                    summary_metrics = {}
                    
                    try:
                        cached_historical_df = None
                        if use_cache and user_id and db_manager:
                            try:
                                cached_historical_df = db_manager.load_cached_historical_data(user_id, historical_years)
                            except Exception as e:
                                pass  # Continue without cache

                        insights, seasonal_insights, summary_metrics = bi_engine.analyze_comprehensive_performance(
                            recent_orders_df, historical_orders_df, inventory_df, cached_historical_df
                        )
                        
                    except Exception as e:
                        st.warning(f"⚠️ Error in BI analysis: {e}")
                        # Continue with empty results
                    
                    # Step 10: Update cache timestamp for non-demo users
                    try:
                        if not st.session_state.get('demo_mode', False) and historical_orders and profile:
                            profile.last_cache_update = datetime.now()
                            db_manager.save_user_profile(profile)
                    except Exception as e:
                        pass  # Continue without updating cache
                    
                    # Calculate analysis duration
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    # Store results in session state
                    st.session_state.update({
                        'insights': insights,
                        'seasonal_insights': seasonal_insights,
                        'summary_metrics': summary_metrics,
                        'recent_orders_df': recent_orders_df,
                        'historical_orders_df': historical_orders_df,
                        'inventory_df': inventory_df,
                        'analysis_duration': duration,
                        'data_fetched': True,
                        'location_config': location_config,
                        'user_profile': profile
                    })
                    
                    # Clean success and immediate redirect
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ **Analysis Error:** {str(e)}")
                    
                    with st.expander("🔍 Troubleshooting Guide", expanded=False):
                        st.markdown("""
                        **Common Solutions:**
                        1. **Try Safe Mode** - Processes minimal data to avoid errors
                        2. **Use Quick Test Mode** - Analyze fewer products first
                        3. **Verify API Credentials** - Check your settings in Profile tab
                        4. **Check Internet Connection** - Ensure stable connectivity
                        5. **Reduce Date Range** - Try a shorter analysis period
                        6. **Clear Cache** - Reset cached data if issues persist
                        """)
                    return
        
        # Display results if analysis is complete
        if st.session_state.get('data_fetched', False):
            try:
                display_analysis_results()
            except Exception as e:
                st.error(f"❌ Error displaying results: {e}")
                    
    except Exception as e:
        st.error(f"❌ Critical error in analysis interface: {e}")
"""
SharpStock Main Interface - Part 3: Analysis and Display Functions
Analysis results display and page navigation functions
"""

@safe_error_handler
def display_analysis_results():
    """Clean analysis results with sidebar navigation"""
    
    try:
        # Get results from session state
        insights = st.session_state.get('insights', [])
        seasonal_insights = st.session_state.get('seasonal_insights', [])
        summary_metrics = st.session_state.get('summary_metrics', {})
        recent_orders_df = st.session_state.get('recent_orders_df', pd.DataFrame())
        inventory_df = st.session_state.get('inventory_df', pd.DataFrame())
        duration = st.session_state.get('analysis_duration', 0)
        location_config = st.session_state.get('location_config', {})
        user_profile = st.session_state.get('user_profile')
        
        # Check for product detail view first
        if st.session_state.get('selected_product_id'):
            try:
                from ui.product_detail import display_product_detail_page
                display_product_detail_page(
                    recent_orders_df, 
                    inventory_df, 
                    st.session_state['selected_product_id'],
                    st.session_state.get('selected_style_number', 'Unknown'),
                    location_config
                )
                return
            except Exception as e:
                st.error(f"❌ Error displaying product detail: {e}")
                # Clear the selected product and continue
                st.session_state.pop('selected_product_id', None)
                st.session_state.pop('selected_style_number', None)
        
        # Sidebar Navigation
        with st.sidebar:
            st.markdown("---")
            sharpstock_section_header("📊 Analysis Results")
            
            # Navigation options
            analysis_pages = [
                "📈 Overview",
                "📊 Business Metrics", 
                "🎯 Reorder Intelligence", 
                "📈 Trend Analysis", 
                "📅 Seasonal Insights",
                "🔄 Transfer Recommendations",
                "📋 Order Sheets"
            ]
            
            selected_page = st.radio(
                "Select Analysis View:",
                analysis_pages,
                key="analysis_navigation"
            )
            
            # Quick stats in sidebar
            st.markdown("---")
            st.markdown("**📊 Quick Stats**")
            critical_count = len([i for i in insights if hasattr(i, 'reorder_priority') and i.reorder_priority == 'CRITICAL'])
            trending_count = len([i for i in insights if hasattr(i, 'trend_classification') and 'Trending' in i.trend_classification])
            
            st.metric("Products Analyzed", f"{len(insights):,}")
            st.metric("Critical Alerts", critical_count)
            st.metric("Trending Products", trending_count)
            st.metric("Analysis Time", f"{duration:.1f}s")
        
        # Main Content Area - Route to appropriate page
        if selected_page == "📈 Overview":
            display_analysis_overview(insights, summary_metrics, recent_orders_df, location_config, duration)
        elif selected_page == "📊 Business Metrics":
            display_business_metrics_page(insights, summary_metrics)
        elif selected_page == "🎯 Reorder Intelligence":
            display_reorder_intelligence_page(insights)
        elif selected_page == "📈 Trend Analysis":
            display_trend_analysis_page(insights)
        elif selected_page == "📅 Seasonal Insights":
            display_seasonal_insights_page(seasonal_insights)
        elif selected_page == "🔄 Transfer Recommendations":
            display_transfer_recommendations_page(recent_orders_df, inventory_df, insights, location_config, user_profile)
        elif selected_page == "📋 Order Sheets":
            display_order_sheets_page(insights, recent_orders_df, inventory_df, location_config, user_profile)
                
    except Exception as e:
        st.error(f"❌ Critical error displaying results: {e}")

def display_analysis_overview(insights, summary_metrics, recent_orders_df, location_config, duration):
    """Clean overview page with summary + best sellers only"""

    # Page header
    st.title("📊 Analysis Complete")
    st.caption("Your comprehensive business intelligence analysis is ready")

    # Summary Metrics
    try:
        critical_count = len([i for i in insights if hasattr(i, 'reorder_priority') and i.reorder_priority == 'CRITICAL'])
        high_priority = len([i for i in insights if hasattr(i, 'reorder_priority') and i.reorder_priority == 'HIGH'])
        trending_count = len([i for i in insights if hasattr(i, 'trend_classification') and 'Trending' in i.trend_classification])
        recent_revenue = summary_metrics.get('total_recent_revenue', 0)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Products Analyzed", f'{len(insights):,}', f'In {duration:.1f}s')

        with col2:
            st.metric("Revenue Analyzed", f'${recent_revenue:,.0f}', 'Recent period')

        with col3:
            st.metric("Action Required", f'{critical_count + high_priority}', f'{critical_count} critical')

        with col4:
            st.metric("Growth Opportunities", f'{trending_count}', 'Trending up')

    except Exception as e:
        st.warning(f"⚠️ Could not calculate summary metrics: {e}")

    st.markdown("---")

    # Callout
    st.success(
        "✅ **Analysis Complete!** Use the sidebar to explore detailed insights, reorder recommendations, and trend analysis. "
        "Critical items requiring immediate attention are highlighted throughout the platform."
    )

    # Best Sellers
    st.subheader("🏆 Top Performing Products")
    st.caption("Best selling items across your store locations")

    try:
        if not recent_orders_df.empty:
            bestsellers = (
                recent_orders_df
                .groupby(['product_id', 'Style Number', 'Description', 'vendor'])
                .agg({'quantity': 'sum', 'total_value': 'sum'})
                .reset_index()
                .sort_values('quantity', ascending=False)
                .head(10)
            )

            if not bestsellers.empty:
                for idx, row in bestsellers.iterrows():
                    col1, col2, col3, col4 = st.columns([2, 4, 2, 2])

                    with col1:
                        if st.button(f"📊 {row['Style Number']}", key=f"bestseller_{idx}"):
                            st.session_state['selected_product_id'] = int(row['product_id'])
                            st.session_state['selected_style_number'] = str(row['Style Number'])
                            st.rerun()

                    with col2:
                        desc = str(row['Description'])
                        short_desc = desc[:50] + '...' if len(desc) > 50 else desc
                        st.write(f"**{short_desc}**")
                        st.caption(f"Brand: {row['vendor']}")

                    with col3:
                        st.metric("Units Sold", f"{int(row['quantity']):,}")

                    with col4:
                        st.metric("Revenue", f"${row['total_value']:,.0f}")

                    if idx < len(bestsellers) - 1:
                        st.markdown("---")
            else:
                st.info("No sales data available for best sellers analysis")
        else:
            st.info("No product insights available for best sellers analysis")
    except Exception as e:
        st.error(f"❌ Error displaying best sellers: {e}")

    # Quick Action Buttons
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🚨 View Critical Alerts", use_container_width=True):
            st.session_state['analysis_navigation'] = "🎯 Reorder Intelligence"
            st.rerun()

    with col2:
        if st.button("📈 See Trends", use_container_width=True):
            st.session_state['analysis_navigation'] = "📈 Trend Analysis"
            st.rerun()

    with col3:
        if st.button("📋 Create Orders", use_container_width=True):
            st.session_state['analysis_navigation'] = "📋 Order Sheets"
            st.rerun()

    with col4:
        if st.button("📊 Full Metrics", use_container_width=True):
            st.session_state['analysis_navigation'] = "📊 Business Metrics"
            st.rerun()

def display_business_metrics_page(insights, summary_metrics):
    """Dedicated page for business metrics"""
    
    st.title("📊 Business Performance Dashboard")
    st.caption("Comprehensive metrics and key performance indicators")
    
    try:
        from ui.dashboard import display_business_metrics_native
        display_business_metrics_native(insights, summary_metrics)
    except ImportError:
        # Fallback implementation
        st.subheader("📊 Business Performance Overview")
        
        # Prepare metrics data
        recent_revenue = summary_metrics.get('total_recent_revenue', 0)
        growth_rate = summary_metrics.get('revenue_growth_rate', 0)
        total_products = len(insights)
        trending_up = summary_metrics.get('trending_up_count', 0)
        critical_reorders = summary_metrics.get('critical_reorders', 0)
        high_priority = summary_metrics.get('high_priority_reorders', 0)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Revenue", 
                f"${recent_revenue:,.0f}", 
                f"{growth_rate:+.1f}% vs historical"
            )
        
        with col2:
            st.metric(
                "Products Analyzed", 
                f"{total_products:,}", 
                f"{trending_up} trending up"
            )
        
        with col3:
            st.metric(
                "Reorder Alerts", 
                f"{critical_reorders + high_priority}", 
                f"{critical_reorders} critical"
            )
        
        with col4:
            inventory_at_risk = summary_metrics.get('inventory_at_risk', 0)
            st.metric(
                "Inventory Risk", 
                f"{inventory_at_risk} products", 
                "≤30 days stock"
            )
        
        st.info("💡 This is a simplified view. Full business metrics require additional dashboard components.")
    
    except Exception as e:
        st.error(f"❌ Error in business metrics: {e}")

def display_reorder_intelligence_page(insights):
    """Dedicated page for reorder recommendations"""
    
    st.title("🎯 Reorder Intelligence")
    st.caption("AI-powered recommendations based on demand forecasting and trend analysis")
    
    try:
        from ui.dashboard import display_reorder_recommendations_native
        display_reorder_recommendations_native(insights)
    except ImportError:
        # Fallback implementation
        st.subheader("🎯 Smart Reorder Recommendations")
        
        if not insights:
            st.info("No reorder recommendations available at this time.")
            return
        
        # Filter for products needing reorder
        reorder_needed = [i for i in insights if hasattr(i, 'reorder_priority') and i.reorder_priority in ['CRITICAL', 'HIGH', 'MEDIUM']]
        
        if not reorder_needed:
            st.success("✅ No products currently need reordering!")
            return
        
        st.markdown(f"**📋 {len(reorder_needed)} products need reordering:**")
        
        # Simple table view
        for idx, insight in enumerate(reorder_needed[:20]):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 3, 1, 1, 1])
                
                with col1:
                    priority_colors = {
                        'CRITICAL': '🔴',
                        'HIGH': '🟠', 
                        'MEDIUM': '🟡',
                        'LOW': '🟢'
                    }
                    priority_color = priority_colors.get(insight.reorder_priority, '')
                    
                    if st.button(f"{priority_color} {insight.style_number}", key=f"reorder_simple_{idx}"):
                        st.session_state['selected_product_id'] = insight.product_id
                        st.session_state['selected_style_number'] = insight.style_number
                        st.rerun()
                
                with col2:
                    desc = insight.description[:40] + "..." if len(insight.description) > 40 else insight.description
                    st.write(f"**{desc}**")
                    st.caption(f"{insight.vendor} - {insight.reorder_priority}")
                
                with col3:
                    if hasattr(insight, 'recent_daily_demand'):
                        st.metric("Daily Demand", f"{insight.recent_daily_demand:.1f}")
                    else:
                        st.write("N/A")
                
                with col4:
                    if hasattr(insight, 'current_inventory'):
                        st.metric("Current Stock", f"{insight.current_inventory:,}")
                    else:
                        st.write("N/A")
                
                with col5:
                    if hasattr(insight, 'recommended_qty'):
                        st.metric("Recommended", f"{insight.recommended_qty:,}")
                    else:
                        st.write("N/A")
                
                if idx < len(reorder_needed[:20]) - 1:
                    st.markdown("---")
        
        st.info("💡 This is a simplified view. Full reorder intelligence requires additional dashboard components.")
    
    except Exception as e:
        st.error(f"❌ Error in reorder intelligence: {e}")

def display_trend_analysis_page(insights):
    """Dedicated page for trend analysis"""
    
    st.title("📈 Trend Analysis")
    st.caption("Machine learning powered trend detection and velocity analysis")
    
    try:
        from ui.dashboard import display_trend_analysis_native
        display_trend_analysis_native(insights)
    except ImportError:
        # Fallback implementation
        st.subheader("📈 Product Trend Analysis")
        
        if not insights:
            st.warning("No trend data available for analysis.")
            return
        
        # Trend distribution
        trend_counts = {}
        for insight in insights:
            if hasattr(insight, 'trend_classification'):
                trend_counts[insight.trend_classification] = trend_counts.get(insight.trend_classification, 0) + 1
        
        if trend_counts:
            st.markdown("**📊 Trend Distribution:**")
            
            # Display trend summary
            col1, col2 = st.columns(2)
            
            with col1:
                for trend, count in sorted(trend_counts.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / len(insights)) * 100
                    
                    # Trend emoji mapping
                    trend_emoji = {
                        'Trending Up': '📈',
                        'Hot Seller': '🔥',
                        'Declining': '📉',
                        'Stable': '➡️',
                        'New Strong Seller': '✨'
                    }
                    
                    emoji = trend_emoji.get(trend, '📊')
                    st.write(f"{emoji} **{trend}:** {count} products ({percentage:.1f}%)")
            
            with col2:
                # Show top trending products
                trending_products = [i for i in insights if hasattr(i, 'trend_classification') and 'Trending' in i.trend_classification]
                
                if trending_products:
                    st.markdown("**🔥 Top Trending Products:**")
                    
                    for i, product in enumerate(trending_products[:5]):
                        velocity = f" (+{product.velocity_change:.1f}%)" if hasattr(product, 'velocity_change') else ""
                        st.write(f"{i+1}. **{product.style_number}**{velocity}")
                        if hasattr(product, 'vendor'):
                            st.caption(f"   {product.vendor}")
        
        st.info("💡 This is a simplified view. Full trend analysis requires additional dashboard components.")
    
    except Exception as e:
        st.error(f"❌ Error in trend analysis: {e}")

def display_seasonal_insights_page(seasonal_insights):
    """Dedicated page for seasonal analysis"""
    
    st.title("📅 Seasonal Intelligence")
    st.caption("Advanced seasonal pattern detection and product elevation analysis")
    
    try:
        from ui.dashboard import display_seasonal_analysis_native
        display_seasonal_analysis_native(seasonal_insights)
    except ImportError:
        # Fallback implementation
        st.subheader("📅 Seasonal Intelligence")
        
        if not seasonal_insights:
            st.warning("No seasonal data available for analysis.")
            return
        
        # Basic seasonal overview
        st.markdown("**🌟 Seasonal Overview:**")
        
        seasonal_data = []
        for season in seasonal_insights:
            seasonal_data.append({
                'Month': season.month_name,
                'Avg Daily Demand': f"{season.avg_daily_demand:.1f}",
                'Seasonal Multiplier': f"{season.seasonal_multiplier:.2f}x",
                'Peak Products': len(season.peak_products) if season.peak_products else 0
            })
        
        if seasonal_data:
            df = pd.DataFrame(seasonal_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Highlight peak months
            peak_months = [s for s in seasonal_insights if s.seasonal_multiplier > 1.1]
            if peak_months:
                st.markdown("**🔥 Peak Months:**")
                for month in peak_months:
                    st.write(f"• **{month.month_name}:** {month.seasonal_multiplier:.2f}x average demand")
        
        st.info("💡 This is a simplified view. Full seasonal analysis requires additional dashboard components.")
    
    except Exception as e:
        st.error(f"❌ Error in seasonal analysis: {e}")

def display_transfer_recommendations_page(recent_orders_df, inventory_df, insights, location_config, user_profile):
    """Dedicated page for transfer recommendations"""
    
    st.title("🔄 Transfer Recommendations")
    st.caption("Smart inventory redistribution suggestions")
    
    try:
        from ui.dashboard import display_transfer_recommendations_native
        display_transfer_recommendations_native(recent_orders_df, inventory_df, insights, location_config, user_profile)
    except ImportError:
        st.subheader("🔄 Inventory Transfer Analysis")
        st.info("Transfer recommendations require additional setup and analysis components.")
        
        # Basic placeholder
        if not recent_orders_df.empty and not inventory_df.empty:
            st.write("**📊 Transfer analysis would include:**")
            st.write("• Products with uneven distribution across stores")
            st.write("• Locations with excess inventory")
            st.write("• Stores running low on popular items")
            st.write("• Recommended transfer quantities and priorities")
        else:
            st.warning("Need both sales and inventory data for transfer analysis")
    
    except Exception as e:
        st.error(f"❌ Error in transfer recommendations: {e}")

def display_order_sheets_page(insights, recent_orders_df, inventory_df, location_config, user_profile):
    """Enhanced order sheet generation with smart recommendations"""
    
    st.title("📋 Order Sheet Generator")
    st.caption("Create purchase orders based on AI recommendations")
    
    try:
        # Initialize order manager
        if 'order_sheet_manager' not in st.session_state:
            from order_management.order_sheet_manager import OrderSheetManager
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
        
        # Show basic order management interface
        brand_insights = [i for i in insights if i.vendor == selected_brand]
        reorder_needed = [i for i in brand_insights if hasattr(i, 'reorder_priority') and i.reorder_priority in ['CRITICAL', 'HIGH']]
        
        if reorder_needed:
            st.write(f"**📊 {len(reorder_needed)} products ready for ordering:**")
            
            for insight in reorder_needed[:10]:
                col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
                
                with col1:
                    st.write(f"**{insight.style_number}**")
                
                with col2:
                    desc = insight.description[:40] + "..." if len(insight.description) > 40 else insight.description
                    st.write(desc)
                
                with col3:
                    st.write(f"Recommended: {insight.recommended_qty:,}")
                
                with col4:
                    if st.button("Add", key=f"add_{insight.product_id}"):
                        st.success(f"Added {insight.style_number} to order list")
        else:
            st.success("✅ No products currently need reordering!")
            
    except ImportError as e:
        st.info("📋 Order sheet functionality requires additional components.")
        
        # Basic placeholder showing what would be available
        if insights:
            reorder_needed = [i for i in insights if hasattr(i, 'reorder_priority') and i.reorder_priority in ['CRITICAL', 'HIGH']]
            
            if reorder_needed:
                st.write(f"**📊 {len(reorder_needed)} products ready for ordering:**")
                
                # Group by vendor
                by_vendor = {}
                for insight in reorder_needed:
                    vendor = getattr(insight, 'vendor', 'Unknown')
                    if vendor not in by_vendor:
                        by_vendor[vendor] = []
                    by_vendor[vendor].append(insight)
                
                for vendor, products in by_vendor.items():
                    total_recommended = sum(getattr(p, 'recommended_qty', 0) for p in products)
                    st.write(f"• **{vendor}:** {len(products)} styles, {total_recommended:,} total units recommended")
            else:
                st.success("✅ No products currently need reordering!")
        else:
            st.info("No product insights available for order generation")
    
    except Exception as e:
        st.error(f"❌ Error in order sheets: {e}")


"""
SharpStock Main Interface - Part 4: Enterprise UI and Main Function
Enhanced dashboard pages and main application entry point
"""

def _show_dashboard_page(db_manager, user_id, profile):
    """Enhanced dashboard page with enterprise UI"""
    
    # Page header with enterprise styling
    enterprise_page_header(
        "Business Intelligence Dashboard",
        "Your comprehensive view of store performance and analytics",
        "📊"
    )
    
    # Check if analysis has been run
    if not st.session_state.get('data_fetched', False):
        _show_welcome_dashboard(db_manager, user_id, profile)
    else:
        _show_analysis_results_dashboard()

def _show_welcome_dashboard(db_manager, user_id, profile):
    """Welcome dashboard for new users or before analysis"""
    
    # Check profile status
    if not profile or not hasattr(profile, 'shop_name') or not profile.shop_name:
        enterprise_alert(
            "👋 **Welcome to SharpStock!** Please complete your profile setup to get started with AI-powered business intelligence.",
            "info"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔧 Complete Profile Setup", type="primary", use_container_width=True):
                st.session_state['current_page'] = 'profile'
                st.rerun()
        return
    
    # Profile is complete - show analysis options
    enterprise_section_header(
        "Ready to Analyze Your Data",
        "Launch comprehensive AI-powered analysis of your store performance",
        "🚀"
    )
    
    # Quick metrics about the store
    metrics_data = [
        {
            'title': 'Store Connected',
            'value': profile.shop_name,
            'delta': 'Ready for analysis',
            'icon': '🏪',
            'variant': 'success'
        },
        {
            'title': 'Analysis Engine',
            'value': 'AI-Powered',
            'delta': 'Advanced algorithms',
            'icon': '🧠',
            'variant': 'primary'
        },
        {
            'title': 'Last Analysis',
            'value': 'None yet',
            'delta': 'Run your first analysis',
            'icon': '📊',
            'variant': 'warning'
        }
    ]
    
    enterprise_metric_dashboard(metrics_data)
    
    # Analysis launch section
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🚀 Launch Analysis")
        
        # Quick analysis options
        analysis_type = st.selectbox(
            "Analysis Type:",
            [
                "🚀 Quick Analysis (Top 50 products)",
                "📊 Full Analysis (All products)",
                "🛡️ Safe Mode (Minimal data)"
            ]
        )
        
        if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
            # Set analysis parameters based on selection
            if "Quick" in analysis_type:
                st.session_state['test_mode'] = True
                st.session_state['safe_mode'] = True
            elif "Safe" in analysis_type:
                st.session_state['safe_mode'] = True
                st.session_state['test_mode'] = True
            else:
                st.session_state['test_mode'] = False
                st.session_state['safe_mode'] = False
            
            # Run analysis
            with st.spinner("🧠 Analyzing your data..."):
                try:
                    # Call the existing analysis function
                    _run_comprehensive_analysis(db_manager, user_id, profile)
                except Exception as e:
                    enterprise_alert(f"❌ Analysis failed: {e}", "error")

def _show_analysis_results_dashboard():
    """Show dashboard with analysis results"""
    
    # Get analysis results
    insights = st.session_state.get('insights', [])
    summary_metrics = st.session_state.get('summary_metrics', {})
    recent_orders_df = st.session_state.get('recent_orders_df', pd.DataFrame())
    location_config = st.session_state.get('location_config', {})
    
    # Key metrics dashboard
    enterprise_section_header(
        "Key Performance Indicators",
        "Real-time insights from your latest analysis",
        "📊"
    )
    
    # Calculate metrics
    critical_alerts = len([i for i in insights if hasattr(i, 'reorder_priority') and i.reorder_priority == 'CRITICAL'])
    high_alerts = len([i for i in insights if hasattr(i, 'reorder_priority') and i.reorder_priority == 'HIGH'])
    trending_up = len([i for i in insights if hasattr(i, 'trend_classification') and 'Trending' in i.trend_classification])
    revenue = summary_metrics.get('total_recent_revenue', 0)
    
    metrics_data = [
        {
            'title': 'Products Analyzed',
            'value': f'{len(insights):,}',
            'delta': f'{trending_up} trending up',
            'delta_type': 'positive' if trending_up > 0 else 'neutral',
            'icon': '📦',
            'variant': 'primary'
        },
        {
            'title': 'Revenue (30d)',
            'value': f'${revenue:,.0f}',
            'delta': 'Recent period',
            'icon': '💰',
            'variant': 'success'
        },
        {
            'title': 'Critical Alerts',
            'value': str(critical_alerts),
            'delta': f'{high_alerts} high priority',
            'delta_type': 'negative' if critical_alerts > 0 else 'positive',
            'icon': '🚨',
            'variant': 'error' if critical_alerts > 0 else 'success'
        },
        {
            'title': 'Opportunities',
            'value': str(trending_up),
            'delta': 'Growth potential',
            'delta_type': 'positive',
            'icon': '📈',
            'variant': 'primary'
        }
    ]
    
    enterprise_metric_dashboard(metrics_data)
    
    # Alerts for critical items
    if critical_alerts > 0:
        enterprise_alert(
            f"🚨 **{critical_alerts} products need immediate reordering!** Click 'View Reorder Alerts' to see details.",
            "error"
        )
    elif high_alerts > 0:
        enterprise_alert(
            f"⚠️ **{high_alerts} products need reordering soon.** Review your inventory recommendations.",
            "warning"
        )
    else:
        enterprise_alert(
            "✅ **All inventory levels look healthy!** Continue monitoring for optimal performance.",
            "success"
        )
    
    # Best sellers section
    _show_best_sellers_section(recent_orders_df, location_config)
    
    # Quick action buttons
    _show_dashboard_quick_actions()

def _show_best_sellers_section(recent_orders_df, location_config):
    """Enhanced best sellers section"""
    
    enterprise_section_header(
        "Top Performing Products",
        "Best selling items across your store locations",
        "🏆"
    )
    
    if recent_orders_df.empty:
        enterprise_alert("No sales data available for best sellers analysis", "info")
        return
    
    # Calculate best sellers
    try:
        bestsellers = (
            recent_orders_df
            .groupby(['product_id', 'Style Number', 'Description', 'vendor'])
            .agg({'quantity': 'sum', 'total_value': 'sum'})
            .reset_index()
            .sort_values('quantity', ascending=False)
            .head(10)
        )
        
        if not bestsellers.empty:
            # Enhanced display
            for idx, row in bestsellers.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([0.5, 2, 3, 1.5, 1.5])
                    
                    with col1:
                        # Rank with medals
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
                            st.session_state['current_page'] = 'trends'
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
        else:
            enterprise_alert("No sales data available", "info")
            
    except Exception as e:
        st.error(f"❌ Error displaying best sellers: {e}")

def _show_dashboard_quick_actions():
    """Enhanced quick action buttons"""
    
    enterprise_section_header(
        "Quick Actions",
        "Navigate to key areas of your business intelligence platform",
        "⚡"
    )
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🚨 Reorder Alerts", type="primary", use_container_width=True):
            st.session_state['current_page'] = 'reorder'
            st.rerun()
    
    with col2:
        if st.button("📈 Trend Analysis", type="secondary", use_container_width=True):
            st.session_state['current_page'] = 'trends'
            st.rerun()
    
    with col3:
        if st.button("📋 Generate Orders", type="secondary", use_container_width=True):
            st.session_state['current_page'] = 'orders'
            st.rerun()
    
    with col4:
        if st.button("🔄 Transfer Recs", type="secondary", use_container_width=True):
            st.session_state['current_page'] = 'transfers'
            st.rerun()

def _show_reorder_alerts_page():
    """Reorder alerts page with enterprise UI"""
    
    enterprise_page_header(
        "Reorder Alerts",
        "Products requiring immediate attention",
        "🚨"
    )
    
    insights = st.session_state.get('insights', [])
    if not insights:
        enterprise_alert("No analysis data available. Please run analysis first.", "warning")
        return
    
    # Filter for alerts
    alerts = [i for i in insights if hasattr(i, 'reorder_priority') and i.reorder_priority in ['CRITICAL', 'HIGH']]
    
    if not alerts:
        render_empty_state(
            title="All Good!",
            description="No critical or high priority reorders needed at this time.",
            icon="✅",
            action_label="View All Products",
            action_callback=lambda: st.session_state.update({'current_page': 'trends'}) or st.rerun()
        )
        return
    
    # Display alerts with enhanced styling
    critical_alerts = [i for i in alerts if i.reorder_priority == 'CRITICAL']
    high_alerts = [i for i in alerts if i.reorder_priority == 'HIGH']
    
    # Summary metrics
    metrics_data = [
        {
            'title': 'Critical Alerts',
            'value': str(len(critical_alerts)),
            'delta': 'Need immediate action',
            'icon': '🔴',
            'variant': 'error'
        },
        {
            'title': 'High Priority',
            'value': str(len(high_alerts)),
            'delta': 'Order this week',
            'icon': '🟠',
            'variant': 'warning'
        }
    ]
    
    enterprise_metric_dashboard(metrics_data, columns=2)
    
    # Display alerts using enhanced components
    if critical_alerts:
        enterprise_section_header("🚨 Critical Priority", "Order immediately to avoid stockouts")
        _display_alert_list(critical_alerts)
    
    if high_alerts:
        enterprise_section_header("⚠️ High Priority", "Order this week")
        _display_alert_list(high_alerts)

def _display_alert_list(alerts):
    """Display list of alerts with enhanced formatting"""
    
    for idx, insight in enumerate(alerts[:10]):  # Limit for performance
        with st.expander(
            f"{enterprise_status_badge(insight.reorder_priority)} **{insight.style_number}** - {insight.description[:50]}...",
            expanded=idx == 0
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**📊 Current Status**")
                st.metric("Current Inventory", f"{insight.current_inventory:,}")
                if hasattr(insight, 'days_until_stockout'):
                    st.metric("Days Until Stockout", f"{insight.days_until_stockout}")
            
            with col2:
                st.markdown("**📈 Performance**")
                st.metric("Daily Demand", f"{insight.recent_daily_demand:.1f}")
                st.metric("Trend", insight.trend_classification)
            
            with col3:
                st.markdown("**🎯 Recommendation**")
                st.metric("Recommended Qty", f"{insight.recommended_qty:,}")
                st.metric("Priority", insight.reorder_priority)
            
            # Quick actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 View Details", key=f"detail_{insight.product_id}_{idx}"):
                    st.session_state['selected_product_id'] = insight.product_id
                    st.session_state['selected_style_number'] = insight.style_number
                    st.session_state['current_page'] = 'trends'
                    st.rerun()
            
            with col2:
                if st.button("🛒 Add to Order", key=f"order_{insight.product_id}_{idx}"):
                    enterprise_alert("Added to order sheet!", "success")

def _show_trend_analysis_page():
    """Trend analysis page with enterprise UI"""
    
    enterprise_page_header(
        "Trend Analysis",
        "Deep dive into product performance and market trends",
        "📈"
    )
    
    insights = st.session_state.get('insights', [])
    if not insights:
        enterprise_alert("No analysis data available. Please run analysis first.", "warning")
        return
    
    # Call the existing trend analysis display function
    try:
        display_trend_analysis_page(insights)
    except Exception as e:
        st.error(f"❌ Error in trend analysis: {e}")

def _show_transfer_recommendations_page():
    """Transfer recommendations with enterprise UI"""
    
    enterprise_page_header(
        "Transfer Recommendations",
        "Optimize inventory distribution across store locations",
        "🔄"
    )
    
    # Get analysis data
    recent_orders_df = st.session_state.get('recent_orders_df', pd.DataFrame())
    inventory_df = st.session_state.get('inventory_df', pd.DataFrame())
    insights = st.session_state.get('insights', [])
    location_config = st.session_state.get('location_config', {})
    user_profile = st.session_state.get('user_profile')
    
    if not insights:
        enterprise_alert("No analysis data available. Please run analysis first.", "warning")
        return
    
    # Call the existing transfer recommendations function
    try:
        display_transfer_recommendations_page(recent_orders_df, inventory_df, insights, location_config, user_profile)
    except Exception as e:
        st.error(f"❌ Error in transfer recommendations: {e}")

def _show_order_management_page():
    """Order management with enterprise UI"""
    
    enterprise_page_header(
        "Order Management",
        "Generate smart order sheets for your suppliers",
        "📋"
    )
    
    # Get analysis data
    insights = st.session_state.get('insights', [])
    recent_orders_df = st.session_state.get('recent_orders_df', pd.DataFrame())
    inventory_df = st.session_state.get('inventory_df', pd.DataFrame())
    location_config = st.session_state.get('location_config', {})
    user_profile = st.session_state.get('user_profile')
    
    if not insights:
        enterprise_alert("No analysis data available. Please run analysis first.", "warning")
        return
    
    # Call the existing order sheets function
    try:
        display_order_sheets_page(insights, recent_orders_df, inventory_df, location_config, user_profile)
    except Exception as e:
        st.error(f"❌ Error in order management: {e}")

def _show_pending_orders_page(profile):
    """Pending orders page with enterprise UI"""
    
    enterprise_page_header(
        "Pending Orders Management",
        "Track orders placed but not yet received",
        "📦"
    )
    
    if PENDING_ORDERS_AVAILABLE and profile:
        try:
            location_config = getattr(profile, 'location_config', {})
            display_pending_orders_interface(profile, location_config)
        except Exception as e:
            st.error(f"❌ Error in pending orders: {e}")
    else:
        enterprise_alert("Pending orders feature not available.", "info")

def _show_profile_settings_page(db_manager, user_id):
    """Profile settings with enhanced enterprise UI"""
    
    enterprise_page_header(
        "Profile & Settings", 
        "Configure your store connection and account preferences",
        "⚙️"
    )
    
    # Call the existing profile management function
    try:
        show_profile_management_tab(db_manager, user_id)
    except Exception as e:
        st.error(f"❌ Error in profile management: {e}")

def _run_comprehensive_analysis(db_manager, user_id, profile):
    """Run the comprehensive analysis with enterprise feedback"""
    
    try:
        # Get analysis parameters from session state
        test_mode = st.session_state.get('test_mode', True)
        safe_mode = st.session_state.get('safe_mode', True)
        
        # Set default date range
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        historical_years = 2
        
        # Get credentials
        if st.session_state.get('demo_mode', False):
            shop_name = "naturally-birkenstock"
            api_version = "2023-10"
            access_token = "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"
            location_config = get_demo_profile().location_config
        else:
            shop_name = profile.shop_name
            api_version = "2023-10"
            access_token = db_manager.decrypt_token(profile.encrypted_api_token)
            location_config = profile.location_config
        
        location_ids = list(location_config.keys()) if location_config else [1]
        
        # Initialize client
        client = AdvancedShopifyClient(shop_name, api_version, access_token, location_ids)
        
        # Load brand lead times
        brand_lead_times = {}
        if not st.session_state.get('demo_mode', False):
            try:
                brand_lead_times = db_manager.get_brand_lead_times(user_id)
            except Exception:
                pass
        
        # Initialize BI engine
        bi_engine = EnhancedBusinessIntelligenceEngine(profile, brand_lead_times)
        
        # Fetch data
        recent_orders, historical_orders = client.fetch_comprehensive_orders(
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time()),
            use_cache=True,
            user_id=user_id,
            db_manager=db_manager,
            historical_years=historical_years
        )
        
        # Apply safe mode limits
        if safe_mode:
            if recent_orders and len(recent_orders) > 100:
                recent_orders = recent_orders[:100]
            if historical_orders and len(historical_orders) > 200:
                historical_orders = historical_orders[:200]
        
        # Process orders
        recent_orders_df = pd.DataFrame()
        historical_orders_df = pd.DataFrame()
        
        if recent_orders:
            recent_orders_df = process_orders_fast(recent_orders, location_config)
        if historical_orders:
            historical_orders_df = process_orders_fast(historical_orders, location_config)
        
        # Combine for product identification
        all_orders_df = pd.DataFrame()
        if not recent_orders_df.empty and not historical_orders_df.empty:
            all_orders_df = pd.concat([recent_orders_df, historical_orders_df], ignore_index=True)
        elif not recent_orders_df.empty:
            all_orders_df = recent_orders_df.copy()
        elif not historical_orders_df.empty:
            all_orders_df = historical_orders_df.copy()
        
        # Determine products to analyze
        if test_mode:
            top_products = all_orders_df.groupby('product_id')['quantity'].sum().sort_values(ascending=False).head(50).index.tolist()
            product_ids = top_products
        else:
            product_ids = all_orders_df['product_id'].unique().tolist()
        
        # Fetch variants and inventory
        variants_data, inventory_levels = client.fetch_variants_and_inventory(product_ids)
        
        # Create inventory dataframe
        inventory_df = create_inventory_dataframe_fast(all_orders_df, variants_data, inventory_levels, location_config)
        
        # Integrate pending orders if enabled
        inventory_df = integrate_pending_orders_if_enabled(inventory_df, profile, location_config)
        
        # Run BI analysis
        cached_historical_df = None
        if user_id and db_manager:
            try:
                cached_historical_df = db_manager.load_cached_historical_data(user_id, historical_years)
            except Exception:
                pass
        
        insights, seasonal_insights, summary_metrics = bi_engine.analyze_comprehensive_performance(
            recent_orders_df, historical_orders_df, inventory_df, cached_historical_df
        )
        
        # Update cache for non-demo users
        if not st.session_state.get('demo_mode', False) and historical_orders and profile:
            try:
                profile.last_cache_update = datetime.now()
                db_manager.save_user_profile(profile)
            except Exception:
                pass
        
        # Store results in session state
        st.session_state.update({
            'insights': insights,
            'seasonal_insights': seasonal_insights,
            'summary_metrics': summary_metrics,
            'recent_orders_df': recent_orders_df,
            'historical_orders_df': historical_orders_df,
            'inventory_df': inventory_df,
            'analysis_duration': time.time() - time.time(),  # Will be updated with actual duration
            'data_fetched': True,
            'location_config': location_config,
            'user_profile': profile
        })
        
        enterprise_alert("✅ Analysis completed successfully!", "success")
        
    except Exception as e:
        enterprise_alert(f"❌ Analysis failed: {e}", "error")
        raise

# MAIN FUNCTION - The single entry point
def main():
    """Enhanced main application entry point with enterprise UI"""
    
    try:
        # Initialize database and auth managers
        try:
            db_manager = DatabaseManager()
            auth_manager = AuthenticationManager(db_manager)
        except Exception as e:
            st.error(f"❌ **System Initialization Error:** {str(e)}")
            st.stop()

        # Authentication
        try:
            user_id = auth_manager.show_auth_interface()
            if not user_id:
                return
        except Exception as e:
            st.error(f"❌ **Authentication Error:** {str(e)}")
            st.stop()

        # Load user profile
        profile = None
        try:
            profile = db_manager.load_user_profile(user_id)
        except Exception as e:
            st.warning(f"⚠️ Could not load user profile: {e}")

        # Handle demo mode
        if st.session_state.get('demo_mode', False):
            try:
                profile = get_demo_profile()
            except Exception as e:
                st.error(f"❌ Demo profile error: {e}")

        # ENTERPRISE NAVIGATION SYSTEM (or fallback)
        if ENTERPRISE_UI_AVAILABLE:
            enterprise_sidebar_navigation()
        else:
            # Fallback navigation
            st.sidebar.title("⚡ SharpStock")
            if st.sidebar.button("🏠 Dashboard"):
                st.session_state['current_page'] = 'dashboard'
            if st.sidebar.button("🚨 Reorder Alerts"):
                st.session_state['current_page'] = 'reorder'
            if st.sidebar.button("📈 Trend Analysis"):
                st.session_state['current_page'] = 'trends'
            if st.sidebar.button("📋 Orders"):
                st.session_state['current_page'] = 'orders'
            if st.sidebar.button("⚙️ Settings"):
                st.session_state['current_page'] = 'profile'
        
        # Get current page from navigation
        current_page = st.session_state.get('current_page', 'dashboard')
        
        # ROUTE TO APPROPRIATE PAGE
        if current_page == 'dashboard':
            _show_dashboard_page(db_manager, user_id, profile)
        elif current_page == 'reorder':
            _show_reorder_alerts_page()
        elif current_page == 'trends':
            _show_trend_analysis_page()
        elif current_page == 'transfers':
            _show_transfer_recommendations_page()
        elif current_page == 'orders':
            _show_order_management_page()
        elif current_page == 'pending':
            _show_pending_orders_page(profile)
        elif current_page == 'profile':
            _show_profile_settings_page(db_manager, user_id)
        else:
            # Default to dashboard
            _show_dashboard_page(db_manager, user_id, profile)

    except Exception as e:
        st.error(f"❌ **Application Startup Error:** {str(e)}")
        logger.error(f"Application startup failed: {e}")
        st.stop()

# Run the app
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ **Fatal Application Error:** {str(e)}")
        logger.critical(f"Fatal error: {e}")
        st.stop()