"""
SharpStock UI Pages Package
Clean, focused page components for the SharpStock application
"""

# Import all page display functions for easy access
from .dashboard import display_dashboard_page
from .reorder_alerts import display_reorder_alerts_page
from .trend_analysis import display_trend_analysis_page
from .transfer_recommendations import display_transfer_recommendations_page
from .order_management import display_order_management_page
from .pending_orders import display_pending_orders_page
from .profile_settings import display_profile_settings_page

# Export page functions
__all__ = [
    'display_dashboard_page',
    'display_reorder_alerts_page',
    'display_trend_analysis_page',
    'display_transfer_recommendations_page',
    'display_order_management_page',
    'display_pending_orders_page',
    'display_profile_settings_page'
]

# Page registry for easy routing
PAGE_REGISTRY = {
    'dashboard': display_dashboard_page,
    'reorder': display_reorder_alerts_page,
    'trends': display_trend_analysis_page,
    'transfers': display_transfer_recommendations_page,
    'orders': display_order_management_page,
    'pending': display_pending_orders_page,
    'profile': display_profile_settings_page
}

def get_page_function(page_key: str):
    """Get page display function by key"""
    return PAGE_REGISTRY.get(page_key, display_dashboard_page)
