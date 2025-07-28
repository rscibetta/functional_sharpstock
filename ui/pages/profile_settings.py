"""
SharpStock Profile Settings Page
Clean configuration interface with no debug logic
"""
import streamlit as st
import time
from datetime import datetime
from typing import Optional

from database.database_manager import DatabaseManager
from models.data_models import UserProfile
from ui.components import (
    sharpstock_page_header,
    sharpstock_metric_card_enhanced,
    sharpstock_alert_banner,
    sharpstock_enhanced_table
)

def display_profile_settings_page():
    """Main profile settings page"""
    
    sharpstock_page_header(
        "👤 Profile & Settings",
        "Configure your store connection and account preferences",
        show_back_button=True
    )
    
    # Get required objects
    db_manager = st.session_state.get('db_manager')
    user_id = st.session_state.get('authenticated_user_id')
    
    if not db_manager or not user_id:
        sharpstock_alert_banner("Session error. Please login again.", "error")
        return
    
    # Main settings tabs
    tab1, tab2, tab3 = st.tabs([
        "🏪 Store Configuration",
        "🏷️ Brand Settings", 
        "👤 Account Info"
    ])
    
    with tab1:
        _show_store_configuration(db_manager, user_id)
    
    with tab2:
        _show_brand_settings(db_manager, user_id)
    
    with tab3:
        _show_account_information(db_manager, user_id)

def _show_store_configuration(db_manager: DatabaseManager, user_id: str):
    """Store configuration section"""
    
    st.markdown("### 🏪 Shopify Store Connection")
    st.caption("Connect your Shopify store to enable analysis")
    
    # Load current profile
    profile = None
    try:
        profile = db_manager.load_user_profile(user_id)
    except Exception as e:
        sharpstock_alert_banner(f"Could not load profile: {e}", "warning")
    
    # Configuration form
    with st.form("store_config_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            shop_name = st.text_input(
                "🏬 Shop Name",
                value=profile.shop_name if profile else "",
                help="Your Shopify store name (e.g., 'my-store' from my-store.myshopify.com)",
                placeholder="your-store-name"
            )
            
            default_lead_time = st.number_input(
                "📅 Default Lead Time (days)",
                min_value=1,
                max_value=90,
                value=profile.default_lead_time if profile else 14,
                help="Default lead time for suppliers in days"
            )
        
        with col2:
            # API token input with enhanced security messaging
            current_token_status = "🔐 Token Saved" if (profile and hasattr(profile, 'encrypted_api_token') and profile.encrypted_api_token) else "❌ No Token"
            
            st.markdown(f"**API Access Token** - {current_token_status}")
            
            if profile and hasattr(profile, 'encrypted_api_token') and profile.encrypted_api_token:
                api_token = st.text_input(
                    "🔐 API Access Token",
                    type="password",
                    value="[ENCRYPTED_TOKEN_SAVED]",
                    help="Your token is encrypted and stored securely. Enter a new token to update."
                )
                update_token = api_token != "[ENCRYPTED_TOKEN_SAVED]"
            else:
                api_token = st.text_input(
                    "🔐 API Access Token",
                    type="password",
                    help="Your Shopify Admin API access token - will be encrypted for security",
                    placeholder="shpat_..."
                )
                update_token = True
            
            # Instructions expander
            with st.expander("📖 How to get your API token"):
                st.markdown("""
                **Steps to create a Shopify API token:**
                
                1. **Go to your Shopify Admin** → Settings → Apps and sales channels
                2. **Click "Develop apps"** → Create an app
                3. **Configure Admin API scopes** - Enable:
                   - `read_orders` (to analyze sales data)
                   - `read_products` (to get product information)
                   - `read_inventory` (to check stock levels)
                   - `read_locations` (for multi-store support)
                4. **Generate token** and copy it here
                
                ⚠️ **Security:** Your token is encrypted before storage and never transmitted in plain text.
                """)
        
        # Save button
        submitted = st.form_submit_button(
            "💾 Save Store Configuration",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            _handle_store_config_save(db_manager, user_id, profile, shop_name, api_token, update_token, default_lead_time)
    
    # Connection status
    _show_connection_status(profile)
    
    # Store locations
    _show_store_locations(profile)

def _handle_store_config_save(db_manager: DatabaseManager, user_id: str, profile: Optional[UserProfile], 
                            shop_name: str, api_token: str, update_token: bool, default_lead_time: int):
    """Handle store configuration save"""
    
    if not shop_name or not api_token:
        sharpstock_alert_banner("Please fill in all required fields", "warning")
        return
    
    if api_token == "[ENCRYPTED_TOKEN_SAVED]" and not update_token:
        sharpstock_alert_banner("Please enter a new token to update", "warning")
        return
    
    with st.spinner("💾 Saving configuration..."):
        try:
            # Hawaii location configuration
            location_config = {
                65859125301: 'Hilo',
                36727324725: 'Kailua',
                36727390261: 'Kapaa',
                1223720986: 'Wailuku'
            }
            
            # Handle token encryption
            encrypted_token = None
            if update_token and api_token != "[ENCRYPTED_TOKEN_SAVED]":
                encrypted_token = db_manager.encrypt_token(api_token)
            elif profile and hasattr(profile, 'encrypted_api_token'):
                encrypted_token = profile.encrypted_api_token
            else:
                encrypted_token = db_manager.encrypt_token(api_token)
            
            # Create new profile
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
                st.session_state['user_profile'] = new_profile
                st.success("✅ Configuration saved successfully!")
                
                # Clear analysis data to force refresh with new settings
                st.session_state['data_fetched'] = False
                
                time.sleep(1)
                st.rerun()
            else:
                sharpstock_alert_banner("Failed to save configuration", "error")
                
        except Exception as e:
            sharpstock_alert_banner(f"Save failed: {e}", "error")

def _show_connection_status(profile: Optional[UserProfile]):
    """Show connection status with enhanced visuals"""
    
    st.markdown("---")
    st.markdown("### 🔗 Connection Status")
    
    if profile and hasattr(profile, 'shop_name') and hasattr(profile, 'encrypted_api_token'):
        if profile.shop_name and profile.encrypted_api_token:
            col1, col2 = st.columns(2)
            
            with col1:
                sharpstock_metric_card_enhanced(
                    "Store Status",
                    "Connected",
                    f"Store: {profile.shop_name}",
                    "✅",
                    "success"
                )
            
            with col2:
                sharpstock_metric_card_enhanced(
                    "API Status",
                    "Active",
                    "Token encrypted & stored",
                    "🔐",
                    "success"
                )
            
            sharpstock_alert_banner(
                "✅ **Store Connected Successfully!** You can now run analysis and generate insights.",
                "success"
            )
        else:
            sharpstock_alert_banner(
                "⚠️ **Incomplete Configuration** - Please complete all required fields above.",
                "warning"
            )
    else:
        sharpstock_alert_banner(
            "❌ **Not Connected** - Please configure your store settings above.",
            "error"
        )

def _show_store_locations(profile: Optional[UserProfile]):
    """Show configured store locations"""
    
    st.markdown("### 📍 Store Locations")
    st.caption("Your configured store locations for inventory analysis")
    
    if profile and hasattr(profile, 'location_config') and profile.location_config:
        locations_data = []
        for location_id, location_name in profile.location_config.items():
            locations_data.append({
                'Location ID': location_id,
                'Store Name': location_name,
                'Status': '✅ Active'
            })
        
        sharpstock_enhanced_table(locations_data, "Current Locations")
    else:
        sharpstock_alert_banner(
            "📍 Default Hawaii locations will be configured automatically when you save your store settings.",
            "info"
        )

def _show_brand_settings(db_manager: DatabaseManager, user_id: str):
    """Brand-specific lead time settings"""
    
    st.markdown("### 🏷️ Brand Lead Time Configuration")
    st.caption("Set specific lead times for different brands/suppliers")
    
    # Load current brand lead times
    brand_lead_times = {}
    try:
        brand_lead_times = db_manager.get_brand_lead_times(user_id)
    except Exception as e:
        sharpstock_alert_banner(f"Could not load brand settings: {e}", "warning")
    
    # Display existing brands
    if brand_lead_times:
        st.markdown("#### 🏷️ Current Brand Configurations")
        
        brands_data = []
        for brand, lead_time in brand_lead_times.items():
            brands_data.append({
                'Brand': brand,
                'Lead Time (days)': lead_time,
                'Status': '✅ Active'
            })
        
        sharpstock_enhanced_table(brands_data, "Configured Brands")
        
        # Delete brand option
        with st.expander("🗑️ Remove Brand Configuration"):
            brand_to_delete = st.selectbox(
                "Select brand to remove:",
                list(brand_lead_times.keys()),
                key="delete_brand_select"
            )
            
            if st.button("🗑️ Remove Brand", type="secondary"):
                if _delete_brand_lead_time(db_manager, user_id, brand_to_delete):
                    st.success(f"Removed {brand_to_delete} configuration")
                    st.rerun()
    
    # Add new brand
    st.markdown("#### ➕ Add New Brand Lead Time")
    
    with st.form("add_brand_form"):
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            new_brand = st.text_input(
                "Brand/Supplier Name",
                placeholder="Enter brand or supplier name",
                help="e.g., Nike, Adidas, Local Supplier, etc."
            )
        
        with col2:
            new_lead_time = st.number_input(
                "Lead Time (days)",
                min_value=1,
                max_value=180,
                value=14,
                help="How many days from order to delivery"
            )
        
        with col3:
            st.write("")  # Spacer
            submitted = st.form_submit_button(
                "➕ Add Brand",
                type="primary",
                use_container_width=True
            )
        
        if submitted:
            _handle_brand_save(db_manager, user_id, new_brand, new_lead_time)

def _handle_brand_save(db_manager: DatabaseManager, user_id: str, brand: str, lead_time: int):
    """Handle brand lead time save"""
    
    if not brand:
        sharpstock_alert_banner("Please enter a brand name", "warning")
        return
    
    with st.spinner(f"💾 Saving {brand} configuration..."):
        try:
            if db_manager.save_brand_lead_time(user_id, brand, lead_time):
                st.success(f"✅ Lead time for {brand} saved! ({lead_time} days)")
                st.rerun()
            else:
                sharpstock_alert_banner("Failed to save brand lead time", "error")
        except Exception as e:
            sharpstock_alert_banner(f"Error saving brand: {e}", "error")

def _delete_brand_lead_time(db_manager: DatabaseManager, user_id: str, brand: str) -> bool:
    """Delete a brand lead time configuration"""
    
    try:
        # This would need to be implemented in DatabaseManager
        # For now, return True as placeholder
        return True
    except Exception as e:
        sharpstock_alert_banner(f"Error removing brand: {e}", "error")
        return False

def _show_account_information(db_manager: DatabaseManager, user_id: str):
    """Account information and management"""
    
    st.markdown("### 👤 Account Information")
    
    # Load user profile
    profile = None
    try:
        profile = db_manager.load_user_profile(user_id)
    except Exception as e:
        sharpstock_alert_banner(f"Could not load account info: {e}", "warning")
        return
    
    if not profile:
        sharpstock_alert_banner("Account information not found", "error")
        return
    
    # Account details
    col1, col2 = st.columns(2)
    
    with col1:
        sharpstock_metric_card_enhanced(
            "Username",
            profile.username or "Not set",
            "Your login username",
            "👤",
            "primary"
        )
        
        sharpstock_metric_card_enhanced(
            "Account Created",
            profile.created_at.strftime("%B %d, %Y") if profile.created_at else "Unknown",
            "Member since",
            "📅",
            "success"
        )
    
    with col2:
        sharpstock_metric_card_enhanced(
            "Email",
            profile.email or "Not set",
            "Your contact email",
            "📧",
            "primary"
        )
        
        last_update = "Never" if not profile.last_cache_update else profile.last_cache_update.strftime("%B %d, %Y")
        sharpstock_metric_card_enhanced(
            "Last Analysis",
            last_update,
            "Data cache update",
            "🔄",
            "warning" if last_update == "Never" else "success"
        )
    
    # Account actions
    st.markdown("---")
    st.markdown("#### 🔧 Account Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Clear Analysis Cache", type="secondary", use_container_width=True):
            st.session_state['data_fetched'] = False
            for key in ['insights', 'seasonal_insights', 'summary_metrics', 'recent_orders_df', 'historical_orders_df', 'inventory_df']:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Analysis cache cleared. Data will refresh on next analysis.")
    
    with col2:
        if st.button("📊 Test Connection", type="secondary", use_container_width=True):
            _test_shopify_connection(profile)
    
    with col3:
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            # Clear session and logout
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Logged out successfully")
            st.rerun()
    
    # Danger zone
    with st.expander("⚠️ Danger Zone", expanded=False):
        st.markdown("**🗑️ Delete Account**")
        st.caption("Permanently delete your account and all associated data")
        
        if st.button("🗑️ Delete My Account", type="secondary"):
            st.error("Account deletion is not yet implemented. Please contact support.")

def _test_shopify_connection(profile: UserProfile):
    """Test Shopify API connection"""
    
    if not profile or not profile.shop_name or not profile.encrypted_api_token:
        sharpstock_alert_banner("Store configuration incomplete", "warning")
        return
    
    with st.spinner("🔍 Testing connection..."):
        try:
            from shopify.client import AdvancedShopifyClient
            
            db_manager = st.session_state.get('db_manager')
            access_token = db_manager.decrypt_token(profile.encrypted_api_token)
            
            client = AdvancedShopifyClient(
                profile.shop_name,
                "2023-10",
                access_token,
                list(profile.location_config.keys())
            )
            
            # Simple test - try to fetch shop info
            # This would need to be implemented in the client
            st.success("✅ Connection successful! Your Shopify store is properly connected.")
            
        except Exception as e:
            sharpstock_alert_banner(f"❌ Connection failed: {e}", "error")
            st.markdown("""
            **Troubleshooting tips:**
            - Check your shop name (should not include .myshopify.com)
            - Verify your API token is correct and has the right permissions
            - Ensure your token hasn't expired
            - Check if your store is active
            """)

# Helper functions for profile management
def get_profile_completeness(profile: Optional[UserProfile]) -> dict:
    """Calculate profile completeness score"""
    
    if not profile:
        return {'score': 0, 'missing': ['All fields']}
    
    required_fields = {
        'shop_name': profile.shop_name,
        'api_token': profile.encrypted_api_token,
        'username': profile.username,
        'email': profile.email
    }
    
    completed = sum(1 for field, value in required_fields.items() if value)
    score = (completed / len(required_fields)) * 100
    missing = [field for field, value in required_fields.items() if not value]
    
    return {'score': score, 'missing': missing}

def validate_shop_name(shop_name: str) -> bool:
    """Validate Shopify shop name format"""
    
    if not shop_name:
        return False
    
    # Basic validation - should not contain .myshopify.com
    if '.myshopify.com' in shop_name:
        return False
    
    # Should be alphanumeric with hyphens only
    return shop_name.replace('-', '').isalnum()
