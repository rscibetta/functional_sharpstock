"""
Enterprise Navigation System for SharpStock
Professional sidebar navigation with consistent UX patterns
"""
import streamlit as st
from typing import Dict, List, Any, Optional

def enterprise_sidebar_navigation():
    """Professional sidebar navigation with SharpStock branding"""
    
    with st.sidebar:
        # SharpStock Logo/Brand Header
        st.markdown("""
        <div style="
            text-align: center;
            padding: 24px 16px 32px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 24px;
        ">
            <div style="
                font-size: 3rem;
                margin-bottom: 12px;
                filter: drop-shadow(0 0 20px rgba(14, 165, 233, 0.5));
            ">⚡</div>
            <h1 style="
                margin: 0;
                font-size: 1.75rem;
                font-weight: 800;
                background: linear-gradient(135deg, #0EA5E9, #38BDF8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            ">SharpStock</h1>
            <p style="
                margin: 4px 0 0 0;
                color: #64748B;
                font-size: 0.875rem;
                font-weight: 500;
            ">Business Intelligence</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation Menu
        nav_items = [
            {
                'label': 'Dashboard',
                'icon': '🏠',
                'page': 'dashboard',
                'description': 'Overview & metrics'
            },
            {
                'label': 'Reorder Alerts',
                'icon': '🚨',
                'page': 'reorder',
                'description': 'Critical inventory alerts',
                'badge': _get_alert_count()
            },
            {
                'label': 'Trend Analysis',
                'icon': '📈', 
                'page': 'trends',
                'description': 'Product performance insights'
            },
            {
                'label': 'Transfer Recommendations',
                'icon': '🔄',
                'page': 'transfers', 
                'description': 'Optimize inventory distribution'
            },
            {
                'label': 'Order Management',
                'icon': '📋',
                'page': 'orders',
                'description': 'Generate supplier orders'
            },
            {
                'label': 'Pending Orders',
                'icon': '📦',
                'page': 'pending',
                'description': 'Track incoming inventory'
            }
        ]
        
        # Render navigation items
        current_page = st.session_state.get('current_page', 'dashboard')
        
        for item in nav_items:
            is_active = current_page == item['page']
            
            # Create navigation button
            if _render_nav_item(item, is_active):
                st.session_state['current_page'] = item['page']
                st.rerun()
        
        # Settings section
        st.markdown("""
        <div style="
            margin-top: 32px;
            padding-top: 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        ">
        </div>
        """, unsafe_allow_html=True)
        
        # Settings and profile
        settings_items = [
            {
                'label': 'Profile & Settings',
                'icon': '⚙️',
                'page': 'profile',
                'description': 'Account configuration'
            }
        ]
        
        for item in settings_items:
            is_active = current_page == item['page']
            if _render_nav_item(item, is_active):
                st.session_state['current_page'] = item['page']
                st.rerun()
        
        # Footer with version info
        st.markdown("""
        <div style="
            position: absolute;
            bottom: 16px;
            left: 16px;
            right: 16px;
            text-align: center;
            color: #64748B;
            font-size: 0.75rem;
        ">
            SharpStock v2.0<br>
            Enterprise Edition
        </div>
        """, unsafe_allow_html=True)

def _render_nav_item(item: Dict, is_active: bool) -> bool:
    """Render individual navigation item with professional styling"""
    
    # Active state styling
    active_style = """
        background: linear-gradient(135deg, var(--primary), var(--primary-dark));
        color: white;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4);
        border: 1px solid var(--primary);
    """ if is_active else """
        background: transparent;
        color: var(--text-secondary);
        border: 1px solid transparent;
    """
    
    hover_style = "" if is_active else """
        .nav-item:hover {
            background: rgba(255, 255, 255, 0.05) !important;
            color: var(--text-primary) !important;
            border-color: rgba(255, 255, 255, 0.1) !important;
            transform: translateX(4px);
        }
    """
    
    # Badge for notifications
    badge_html = ""
    if item.get('badge') and item['badge'] > 0:
        badge_html = f"""
        <span style="
            background: var(--error);
            color: white;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 10px;
            min-width: 18px;
            height: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
        ">{item['badge']}</span>
        """
    
    # Render the navigation item
    nav_html = f"""
    <style>
    {hover_style}
    </style>
    <div class="nav-item" style="
        {active_style}
        padding: 12px 16px;
        margin: 4px 0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 12px;
        text-decoration: none;
        font-weight: 500;
    ">
        <span style="font-size: 1.25rem;">{item['icon']}</span>
        <div style="flex: 1;">
            <div style="font-size: 0.9rem; line-height: 1.2;">
                {item['label']}
            </div>
            <div style="
                font-size: 0.75rem;
                opacity: 0.7;
                margin-top: 2px;
                line-height: 1.2;
            ">
                {item['description']}
            </div>
        </div>
        {badge_html}
    </div>
    """
    
    # Use a unique key for each navigation item
    button_key = f"nav_{item['page']}"
    
    # Create an invisible button that covers the entire area
    clicked = st.button(
        item['label'],
        key=button_key,
        help=item['description'],
        use_container_width=True,
        type="primary" if is_active else "secondary"
    )
    
    # Overlay the styled HTML
    st.markdown(nav_html, unsafe_allow_html=True)
    
    return clicked

def enterprise_breadcrumbs(items: List[str]):
    """Professional breadcrumb navigation"""
    
    if len(items) <= 1:
        return
    
    breadcrumb_items = []
    for i, item in enumerate(items):
        if i == len(items) - 1:
            # Last item (current page) - no link
            breadcrumb_items.append(f'<span style="color: var(--text-primary); font-weight: 600;">{item}</span>')
        else:
            # Clickable items
            breadcrumb_items.append(f'<span style="color: var(--text-tertiary);">{item}</span>')
    
    breadcrumb_html = f"""
    <div style="
        margin: 16px 0 24px 0;
        padding: 12px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    ">
        <nav style="
            font-size: 0.875rem;
            color: var(--text-tertiary);
        ">
            {' <span style="margin: 0 8px; color: var(--text-muted);">→</span> '.join(breadcrumb_items)}
        </nav>
    </div>
    """
    
    st.markdown(breadcrumb_html, unsafe_allow_html=True)

def enterprise_tab_navigation(tabs: List[str], icons: List[str] = None, key: str = "main_tabs"):
    """Enhanced tab navigation with icons and professional styling"""
    
    # Prepare tab labels with icons
    if icons and len(icons) == len(tabs):
        tab_labels = [f"{icon} {tab}" for icon, tab in zip(icons, tabs)]
    else:
        tab_labels = tabs
    
    # Custom styling for tabs
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card);
        border-radius: var(--radius-lg);
        padding: 6px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        gap: 4px;
        margin-bottom: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: var(--radius-md);
        font-weight: 600;
        padding: 12px 20px;
        transition: all var(--transition-fast);
        border: none;
        color: var(--text-tertiary);
        font-size: 0.9rem;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.05);
        color: var(--text-secondary);
        transform: translateY(-1px);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
        transform: translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    return st.tabs(tab_labels)

def enterprise_command_palette():
    """Professional command palette for power users"""
    
    # This would be implemented as a modal/popup in a full system
    # For now, provide a search interface
    
    st.markdown("""
    <div style="
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
    ">
        <button style="
            background: var(--bg-card);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: var(--radius-md);
            color: var(--text-secondary);
            padding: 8px 12px;
            font-size: 0.875rem;
            cursor: pointer;
            transition: all var(--transition-fast);
        " onclick="alert('Command palette (Ctrl+K) - Feature coming soon!')">
            ⌘K
        </button>
    </div>
    """, unsafe_allow_html=True)

def _get_alert_count() -> int:
    """Get current alert count for navigation badge"""
    
    insights = st.session_state.get('insights', [])
    if not insights:
        return 0
    
    critical_count = len([i for i in insights if hasattr(i, 'reorder_priority') and i.reorder_priority == 'CRITICAL'])
    high_count = len([i for i in insights if hasattr(i, 'reorder_priority') and i.reorder_priority == 'HIGH'])
    
    return critical_count + high_count

def enterprise_quick_actions():
    """Floating action buttons for common tasks"""
    
    st.markdown("""
    <div style="
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 1000;
        display: flex;
        flex-direction: column;
        gap: 12px;
    ">
        <button style="
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            box-shadow: 0 8px 24px rgba(14, 165, 233, 0.4);
            transition: all var(--transition-fast);
        " onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" title="Quick Analysis">
            ⚡
        </button>
        <button style="
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: var(--bg-tertiary);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: var(--text-secondary);
            font-size: 1.25rem;
            cursor: pointer;
            transition: all var(--transition-fast);
        " onmouseover="this.style.background='var(--primary)'; this.style.color='white'" onmouseout="this.style.background='var(--bg-tertiary)'; this.style.color='var(--text-secondary)'" title="Export Data">
            📊
        </button>
        <button style="
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: var(--bg-tertiary);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: var(--text-secondary);
            font-size: 1.25rem;
            cursor: pointer;
            transition: all var(--transition-fast);
        " onmouseover="this.style.background='var(--success)'; this.style.color='white'" onmouseout="this.style.background='var(--bg-tertiary)'; this.style.color='var(--text-secondary)'" title="Quick Order">
            🛒
        </button>
    </div>
    """, unsafe_allow_html=True)

# =====================================
# RESPONSIVE NAVIGATION HELPERS
# =====================================

def get_current_page() -> str:
    """Get current page from session state"""
    return st.session_state.get('current_page', 'dashboard')

def set_current_page(page: str):
    """Set current page in session state"""
    st.session_state['current_page'] = page

def is_mobile() -> bool:
    """Detect if user is on mobile (placeholder for responsive design)"""
    # In a full implementation, this would check viewport width
    return False

def enterprise_mobile_navigation():
    """Mobile-optimized navigation (for responsive design)"""
    
    if not is_mobile():
        return
    
    # Mobile navigation would be implemented here
    # Bottom tab bar, hamburger menu, etc.
    pass

# =====================================
# PAGE ROUTING SYSTEM
# =====================================

class EnterpriseRouter:
    """Professional page routing system"""
    
    def __init__(self):
        self.routes = {
            'dashboard': {
                'title': 'Dashboard',
                'icon': '🏠',
                'component': None,  # Will be set by the main app
                'breadcrumbs': ['Dashboard']
            },
            'reorder': {
                'title': 'Reorder Alerts',
                'icon': '🚨', 
                'component': None,
                'breadcrumbs': ['Dashboard', 'Reorder Alerts']
            },
            'trends': {
                'title': 'Trend Analysis',
                'icon': '📈',
                'component': None,
                'breadcrumbs': ['Dashboard', 'Trend Analysis']
            },
            'transfers': {
                'title': 'Transfer Recommendations',
                'icon': '🔄',
                'component': None,
                'breadcrumbs': ['Dashboard', 'Transfer Recommendations']
            },
            'orders': {
                'title': 'Order Management',
                'icon': '📋',
                'component': None,
                'breadcrumbs': ['Dashboard', 'Order Management']
            },
            'pending': {
                'title': 'Pending Orders',
                'icon': '📦',
                'component': None,
                'breadcrumbs': ['Dashboard', 'Pending Orders']
            },
            'profile': {
                'title': 'Profile & Settings',
                'icon': '⚙️',
                'component': None,
                'breadcrumbs': ['Dashboard', 'Settings', 'Profile']
            }
        }
    
    def register_route(self, route: str, config: Dict):
        """Register a new route"""
        self.routes[route] = config
    
    def get_route_config(self, route: str) -> Dict:
        """Get configuration for a route"""
        return self.routes.get(route, self.routes['dashboard'])
    
    def navigate_to(self, route: str):
        """Navigate to a specific route"""
        if route in self.routes:
            st.session_state['current_page'] = route
            st.rerun()
    
    def get_current_route_config(self) -> Dict:
        """Get current route configuration"""
        current_page = get_current_page()
        return self.get_route_config(current_page)

# Global router instance
router = EnterpriseRouter()

# =====================================
# CONTEXT-AWARE NAVIGATION
# =====================================

def show_contextual_navigation():
    """Show context-aware navigation aids"""
    
    current_page = get_current_page()
    
    # Show relevant quick actions based on current page
    if current_page == 'reorder':
        st.sidebar.markdown("""
        **Quick Actions:**
        - View all critical alerts
        - Generate order sheets
        - Export alert summary
        """)
    
    elif current_page == 'trends':
        st.sidebar.markdown("""
        **Analysis Tools:**
        - Product performance
        - Velocity analysis
        - Seasonal patterns
        """)
    
    elif current_page == 'orders':
        st.sidebar.markdown("""
        **Order Management:**
        - Create new orders
        - Review pending sheets
        - Supplier contacts
        """)

def show_navigation_shortcuts():
    """Display keyboard shortcuts for power users"""
    
    with st.sidebar.expander("⌨️ Shortcuts", expanded=False):
        st.markdown("""
        **Navigation:**
        - `1` → Dashboard
        - `2` → Reorder Alerts  
        - `3` → Trend Analysis
        - `4` → Transfer Recs
        - `5` → Order Management
        
        **Actions:**
        - `Ctrl+K` → Command palette
        - `R` → Refresh data
        - `E` → Export current view
        - `?` → Help
        """)

# =====================================
# EXPORT ALL NAVIGATION COMPONENTS
# =====================================

__all__ = [
    'enterprise_sidebar_navigation',
    'enterprise_breadcrumbs',
    'enterprise_tab_navigation', 
    'enterprise_command_palette',
    'enterprise_quick_actions',
    'enterprise_mobile_navigation',
    'EnterpriseRouter',
    'router',
    'get_current_page',
    'set_current_page',
    'show_contextual_navigation',
    'show_navigation_shortcuts'
]
