"""Enhanced Authentication Interface with Native Streamlit Styling"""
import streamlit as st
import hashlib
import time
from datetime import datetime
from typing import Optional

from database.database_manager import DatabaseManager
from ui.components import (
    apply_sharpstock_branding,
    apply_minimal_css,
    sharpstock_info_box,
    sharpstock_section_header,
    sharpstock_metric_card
)

class AuthenticationManager:
    """Enhanced authentication manager with native Streamlit styling"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def show_auth_interface(self) -> Optional[str]:
        """Show enhanced login/registration interface with SharpStock branding"""
        
        if 'authenticated_user_id' in st.session_state:
            return st.session_state['authenticated_user_id']
        
        # Apply minimal CSS only when needed
        apply_minimal_css()
        
        # SharpStock branding using new native function
        apply_sharpstock_branding()
        
        # Main authentication area
        col1, col2 = st.columns([3, 1])
        
        with col2:
            # Enhanced demo mode section
            st.markdown("### 🚀 Try Demo Mode")
            
            sharpstock_info_box(
                "Experience SharpStock with sample data - no setup required!",
                "info"
            )
            
            if st.button("🚀 Launch Demo", type="secondary", use_container_width=True):
                demo_user_id = "demo_user_123"
                st.session_state['authenticated_user_id'] = demo_user_id
                st.session_state['demo_mode'] = True
                st.rerun()
        
        with col1:
            # Enhanced authentication tabs
            tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Create Account"])
            
            with tab1:
                self._show_enhanced_login_form()
            
            with tab2:
                self._show_enhanced_registration_form()
        
        # Features showcase using native components
        st.markdown("---")
        sharpstock_section_header("🌟 Platform Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📊 Advanced Analytics**")
            st.write("• 2-year trend analysis")
            st.write("• Smart reorder recommendations")
            st.write("• Seasonal insights")
        
        with col2:
            st.markdown("**🎯 Business Intelligence**")
            st.write("• AI-powered insights")
            st.write("• Product performance tracking")
            st.write("• Revenue growth analysis")
        
        with col3:
            st.markdown("**⚙️ Multi-Store Support**")
            st.write("• Brand-specific lead times")
            st.write("• Cached historical data")
            st.write("• Hawaii location optimization")
        
        return None
    
    def _show_enhanced_login_form(self):
        """Enhanced login form with native Streamlit styling"""
        
        with st.form("enhanced_login_form"):
            st.markdown("### Welcome Back!")
            
            username = st.text_input(
                "👤 Username or Email",
                placeholder="Enter your username or email",
                help="Use the email address you registered with"
            )
            
            password = st.text_input(
                "🔐 Password",
                type="password",
                placeholder="Enter your password",
                help="Your account password"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                remember_me = st.checkbox("Remember me", value=True)
            
            with col2:
                st.markdown("*Forgot password?*")
            
            submitted = st.form_submit_button(
                "🚀 Sign In",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                if username and password:
                    user_id = self.db.authenticate_user(username, password)
                    if user_id:
                        st.session_state['authenticated_user_id'] = user_id
                        st.session_state['demo_mode'] = False
                        
                        st.success("✅ Login successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ **Authentication Failed** - Invalid username or password. Please check your credentials and try again.")
                else:
                    st.warning("⚠️ **Missing Information** - Please fill in all required fields.")
    
    def _show_enhanced_registration_form(self):
        """Enhanced registration form with native Streamlit styling"""
        
        with st.form("enhanced_registration_form"):
            st.markdown("### Create Your SharpStock Account")
            
            new_username = st.text_input(
                "👤 Username",
                placeholder="Choose a unique username",
                help="This will be your login identifier"
            )
            
            new_email = st.text_input(
                "📧 Email Address",
                placeholder="Enter your email address",
                help="We'll use this for account recovery and updates"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_password = st.text_input(
                    "🔐 Password",
                    type="password",
                    placeholder="Create a strong password",
                    help="Minimum 6 characters recommended"
                )
            
            with col2:
                confirm_password = st.text_input(
                    "🔐 Confirm Password",
                    type="password",
                    placeholder="Confirm your password",
                    help="Re-enter your password"
                )
            
            # Terms and conditions
            agree_terms = st.checkbox(
                "I agree to the Terms of Service and Privacy Policy",
                help="You must agree to our terms to create an account"
            )
            
            submitted = st.form_submit_button(
                "🚀 Create Account",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                # Validation
                if not all([new_username, new_email, new_password, confirm_password]):
                    st.warning("⚠️ **Missing Information** - Please fill in all required fields.")
                elif new_password != confirm_password:
                    st.error("❌ **Password Mismatch** - Passwords don't match. Please try again.")
                elif len(new_password) < 6:
                    st.warning("⚠️ **Weak Password** - Password must be at least 6 characters long.")
                elif not agree_terms:
                    st.warning("⚠️ **Terms Required** - You must agree to the Terms of Service to create an account.")
                else:
                    try:
                        user_id = self.db.create_user(new_username, new_email, new_password)
                        
                        st.success("✅ **Account Created Successfully!** Welcome to SharpStock! Please sign in with your new credentials.")
                        
                        # Auto-switch to login tab would be ideal here
                        st.balloons()
                        
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            st.error("❌ **Account Exists** - Username or email already exists. Please try different credentials or sign in instead.")
                        else:
                            st.error(f"❌ **Registration Failed** - {str(e)}")
    
    def logout(self):
        """Enhanced logout with cleanup"""
        
        # Clear all session state
        keys_to_clear = [
            'authenticated_user_id', 
            'user_profile', 
            'demo_mode',
            'insights',
            'seasonal_insights',
            'summary_metrics',
            'data_fetched'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        st.success("👋 Logged out successfully!")
        time.sleep(1)
        st.rerun()