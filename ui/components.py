"""
SharpStock Native Streamlit Components
Clean, maintainable, professional UI using Streamlit's native theming system
"""
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
from ui.enterprise_components import *
from ui.enterprise_styles import apply_enterprise_styles

# Apply styling immediately when this module is imported
apply_enterprise_styles()

# Create wrapper functions to maintain compatibility
def sharpstock_page_header(title, subtitle="", icon="", show_back_button=False):
    return enterprise_page_header(title, subtitle, icon, show_back_button)

def sharpstock_metric_card_enhanced(title, value, delta="", icon="📊", variant="default", delta_type="neutral"):
    return enterprise_metric_card(title, value, delta, delta_type, icon, "", variant)

def sharpstock_alert_banner(message, alert_type="info"):
    return enterprise_alert(message, alert_type)

def sharpstock_section_header(title, description="", icon=""):
    return enterprise_section_header(title, description, icon)

def sharpstock_metric_dashboard(metrics_data, title=""):
    return enterprise_metric_dashboard(metrics_data)

def sharpstock_enhanced_table(data, title=""):
    return enterprise_data_table(data, title)

def create_sharpstock_chart_enhanced(*args, **kwargs):
    return create_enterprise_chart(*args, **kwargs)

# =====================================
# CORE BRAND SYSTEM
# =====================================

def apply_sharpstock_branding():
    """Apply SharpStock logo and brand header using native Streamlit"""
    
    # Professional logo header with minimal HTML
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; margin-bottom: 1rem;">
        <div style="font-size: 4rem; margin-bottom: 0.5rem;">⚡</div>
        <h1 style="margin: 0; color: #0EA5E9; font-weight: 800; font-size: 3rem;">SharpStock</h1>
        <p style="margin: 0.5rem 0 0 0; color: #9CA3AF; font-size: 1.2rem;">Advanced Business Intelligence Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

def sharpstock_metric_card(title: str, value: str, delta: str = "", 
                          help_text: str = "", icon: str = "📊"):
    """Enhanced metric display with SharpStock styling"""
    
    # Create container for custom styling
    with st.container():
        col1, col2 = st.columns([1, 5])
        
        with col1:
            st.markdown(f"""
            <div style="
                text-align: center; 
                font-size: 2.5rem; 
                margin-top: 1rem;
                filter: drop-shadow(0 0 10px rgba(14, 165, 233, 0.3));
            ">{icon}</div>
            """, unsafe_allow_html=True)
        
        with col2:
            if delta:
                st.metric(
                    label=title,
                    value=value,
                    delta=delta,
                    help=help_text
                )
            else:
                st.metric(
                    label=title,
                    value=value,
                    help=help_text
                )

def sharpstock_status_badge(status: str) -> str:
    """Professional status indicators"""
    status_map = {
        'CRITICAL': '🔴 CRITICAL',
        'HIGH': '🟠 HIGH', 
        'MEDIUM': '🟡 MEDIUM',
        'LOW': '🟢 LOW',
        'SUCCESS': '✅ SUCCESS',
        'WARNING': '⚠️ WARNING',
        'INFO': 'ℹ️ INFO',
        'TRENDING': '📈 TRENDING',
        'DECLINING': '📉 DECLINING',
        'NEW': '✨ NEW'
    }
    return status_map.get(status.upper(), f"⚪ {status}")

def sharpstock_trend_indicator(trend: str, change: float) -> str:
    """Clean trend indicators with proper formatting"""
    if "Trending Up" in trend or "Hot" in trend:
        return f"📈 {trend} (+{change:.1f}%)"
    elif "Declining" in trend:
        return f"📉 {trend} ({change:.1f}%)"
    elif "New" in trend:
        return f"✨ {trend}"
    else:
        return f"➡️ {trend}"

# =====================================
# LAYOUT COMPONENTS
# =====================================

def sharpstock_page_header(title: str, subtitle: str = "", icon: str = ""):
    """Professional page headers with consistent styling"""
    
    if icon:
        col1, col2 = st.columns([1, 10])
        with col1:
            st.markdown(f"""
            <div style="
                font-size: 3rem; 
                text-align: center;
                margin-top: 0.5rem;
                filter: drop-shadow(0 0 15px rgba(14, 165, 233, 0.4));
            ">{icon}</div>
            """, unsafe_allow_html=True)
        with col2:
            st.title(title)
            if subtitle:
                st.caption(subtitle)
    else:
        st.title(title)
        if subtitle:
            st.caption(subtitle)

def sharpstock_section_header(title: str, description: str = "", icon: str = ""):
    """Clean section headers with optional icons"""
    if icon:
        st.markdown(f"## {icon} {title}")
    else:
        st.subheader(title)
    
    if description:
        st.caption(description)
    st.markdown("---")

def sharpstock_info_box(message: str, box_type: str = "info"):
    """Native Streamlit info boxes with consistent styling"""
    if box_type == "success":
        st.success(message)
    elif box_type == "warning":
        st.warning(message)
    elif box_type == "error":
        st.error(message)
    else:
        st.info(message)

def sharpstock_sidebar_header():
    """Professional sidebar branding"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 2rem;">⚡</div>
            <h3 style="margin: 0; color: #0EA5E9;">SharpStock</h3>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

# =====================================
# PROFESSIONAL CHARTS
# =====================================

def create_sharpstock_chart(data, chart_type: str = "bar", title: str = "", **kwargs):
    """Professional charts with SharpStock brand theme"""
    
    # SharpStock color palette - consistent with brand
    colors = [
        '#0EA5E9',  # Primary blue
        '#38BDF8',  # Light blue  
        '#0284C7',  # Dark blue
        '#10B981',  # Success green
        '#F59E0B',  # Warning amber
        '#EF4444',  # Error red
        '#8B5CF6',  # Purple accent
        '#9CA3AF',  # Neutral gray
        '#06B6D4',  # Cyan
        '#84CC16'   # Lime
    ]
    
    # Create chart based on type
    if chart_type == "bar":
        fig = px.bar(data, color_discrete_sequence=colors, **kwargs)
    elif chart_type == "line":
        fig = px.line(data, color_discrete_sequence=colors, **kwargs)
    elif chart_type == "pie":
        fig = px.pie(data, color_discrete_sequence=colors, **kwargs)
    elif chart_type == "scatter":
        fig = px.scatter(data, color_discrete_sequence=colors, **kwargs)
    else:
        fig = px.bar(data, color_discrete_sequence=colors, **kwargs)
    
    # Apply SharpStock theme
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#FFFFFF'}
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': '#FFFFFF', 'family': 'Inter, sans-serif'},
        xaxis={
            'gridcolor': 'rgba(255,255,255,0.1)',
            'color': '#D1D5DB'
        },
        yaxis={
            'gridcolor': 'rgba(255,255,255,0.1)',
            'color': '#D1D5DB'
        },
        legend={
            'font': {'color': '#D1D5DB'},
            'bgcolor': 'rgba(55, 65, 81, 0.8)',
            'bordercolor': 'rgba(14, 165, 233, 0.3)',
            'borderwidth': 1
        }
    )
    
    return fig

# =====================================
# DATA DISPLAY COMPONENTS  
# =====================================

def sharpstock_dataframe(df, title: str = "", height: int = 400, key: str = None):
    """Professional dataframe display with SharpStock styling"""
    if title:
        st.subheader(title)
    
    st.dataframe(
        df,
        height=height,
        use_container_width=True,
        hide_index=True,
        key=key
    )

def sharpstock_data_table(data: List[Dict], columns: List[str], title: str = "", 
                         clickable_columns: List[str] = None):
    """Clean data table with optional clickable elements"""
    if title:
        st.subheader(title)
    
    if not data:
        sharpstock_info_box("No data available", "info")
        return
    
    # Headers
    cols = st.columns(len(columns))
    for i, col_name in enumerate(columns):
        with cols[i]:
            st.markdown(f"**{col_name}**")
    
    st.markdown("---")
    
    # Data rows
    for idx, row in enumerate(data):
        cols = st.columns(len(columns))
        for i, col_name in enumerate(columns):
            with cols[i]:
                value = row.get(col_name, "")
                
                # Make certain columns clickable
                if clickable_columns and col_name in clickable_columns:
                    if st.button(str(value), key=f"{col_name}_{idx}_{value}"):
                        return {"clicked_column": col_name, "clicked_value": value, "row_data": row}
                else:
                    st.write(str(value))
    
    return None

# =====================================
# FORM COMPONENTS
# =====================================

def sharpstock_form_header(title: str, description: str = ""):
    """Professional form headers"""
    st.markdown(f"### {title}")
    if description:
        st.caption(description)
    st.markdown("")

def sharpstock_button_group(buttons: List[Dict], key_prefix: str = ""):
    """Create button groups with consistent styling"""
    cols = st.columns(len(buttons))
    
    results = {}
    for i, button_config in enumerate(buttons):
        with cols[i]:
            label = button_config.get('label', f'Button {i+1}')
            button_type = button_config.get('type', 'secondary')
            disabled = button_config.get('disabled', False)
            help_text = button_config.get('help', '')
            
            if st.button(
                label, 
                type=button_type, 
                disabled=disabled,
                help=help_text,
                use_container_width=True,
                key=f"{key_prefix}_{label}_{i}"
            ):
                results['clicked'] = label
                results['index'] = i
    
    return results

# =====================================
# NAVIGATION COMPONENTS
# =====================================

def sharpstock_tab_navigation(tabs: List[str], key: str = "main_tabs"):
    """Enhanced tab navigation with SharpStock styling"""
    return st.tabs([f"{'⚡ ' if i == 0 else ''}{tab}" for i, tab in enumerate(tabs)])

def sharpstock_breadcrumb(items: List[str]):
    """Simple breadcrumb navigation"""
    breadcrumb_html = " > ".join([f"<span style='color: #9CA3AF;'>{item}</span>" for item in items])
    st.markdown(f"<p style='font-size: 0.9rem; margin-bottom: 1rem;'>{breadcrumb_html}</p>", 
                unsafe_allow_html=True)

# =====================================
# LOADING AND PROGRESS
# =====================================

def sharpstock_loading_message(message: str = "Processing..."):
    """Professional loading indicator"""
    with st.spinner(f"⚡ {message}"):
        pass

def sharpstock_progress_bar(progress: float, message: str = ""):
    """Enhanced progress bar with message"""
    if message:
        st.caption(message)
    
    progress_bar = st.progress(progress)
    
    if progress >= 1.0:
        st.success("✅ Complete!")
        progress_bar.empty()

# =====================================
# UTILITY FUNCTIONS
# =====================================

def apply_minimal_css():
    """Minimal CSS injection for fine-tuning only when absolutely necessary"""
    st.markdown("""
    <style>
    /* Minimal overrides for SharpStock branding */
    
    /* Main container spacing */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    
    /* Button hover effects */
    .stButton > button:hover {
        background-color: #38BDF8 !important;
        border-color: #38BDF8 !important;
        color: white !important;
        transform: translateY(-1px);
        transition: all 0.2s ease;
    }
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background: rgba(55, 65, 81, 0.5);
        border: 1px solid rgba(14, 165, 233, 0.3);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #0EA5E9;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(55, 65, 81, 0.5);
        border-radius: 8px;
        padding: 0.25rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0EA5E9 !important;
        color: white !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: #1F2937;
    }
    
    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #374151;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #0EA5E9;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #38BDF8;
    }
    </style>
    """, unsafe_allow_html=True)

# =====================================
# SPECIALIZED COMPONENTS
# =====================================

def sharpstock_metric_dashboard(metrics: List[Dict], title: str = ""):
    """Display multiple metrics in a professional dashboard layout"""
    if title:
        sharpstock_section_header(title)
    
    # Determine number of columns based on metrics count
    num_metrics = len(metrics)
    if num_metrics <= 4:
        cols = st.columns(num_metrics)
    else:
        # For more than 4 metrics, create rows
        cols = st.columns(4)
    
    for i, metric in enumerate(metrics):
        col_index = i % 4 if num_metrics > 4 else i
        
        with cols[col_index]:
            sharpstock_metric_card(
                title=metric.get('title', 'Metric'),
                value=metric.get('value', '0'),
                delta=metric.get('delta', ''),
                help_text=metric.get('help', ''),
                icon=metric.get('icon', '📊')
            )

def sharpstock_alert_banner(message: str, alert_type: str = "info", dismissible: bool = True):
    """Professional alert banners"""
    
    alert_configs = {
        'info': {'emoji': 'ℹ️', 'color': '#0EA5E9'},
        'success': {'emoji': '✅', 'color': '#10B981'},
        'warning': {'emoji': '⚠️', 'color': '#F59E0B'},
        'error': {'emoji': '❌', 'color': '#EF4444'}
    }
    
    config = alert_configs.get(alert_type, alert_configs['info'])
    
    alert_html = f"""
    <div style="
        background: linear-gradient(90deg, {config['color']}22 0%, transparent 100%);
        border-left: 4px solid {config['color']};
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        font-weight: 500;
    ">
        {config['emoji']} {message}
    </div>
    """
    
    st.markdown(alert_html, unsafe_allow_html=True)

# =====================================
# RESPONSIVE COMPONENTS
# =====================================

def sharpstock_responsive_columns(items: List[Any], max_cols: int = 4):
    """Create responsive columns that adapt to content"""
    num_items = len(items)
    num_cols = min(num_items, max_cols)
    
    if num_cols == 0:
        return []
    
    cols = st.columns(num_cols)
    return cols

def sharpstock_mobile_friendly_table(data: List[Dict], mobile_columns: List[str] = None):
    """Table that adapts for mobile viewing"""
    if not data:
        sharpstock_info_box("No data available", "info")
        return
    
    # For mobile-friendly display, show fewer columns or stack vertically
    if mobile_columns:
        # Show only essential columns for mobile
        for item in data[:10]:  # Limit items for performance
            with st.expander(f"{item.get(mobile_columns[0], 'Item')}", expanded=False):
                for key, value in item.items():
                    if key in mobile_columns:
                        st.write(f"**{key}:** {value}")
    else:
        # Default table display
        sharpstock_dataframe(pd.DataFrame(data))

# Export commonly used functions
__all__ = [
    'apply_sharpstock_branding',
    'sharpstock_metric_card', 
    'sharpstock_section_header',
    'sharpstock_info_box',
    'create_sharpstock_chart',
    'sharpstock_dataframe',
    'apply_minimal_css',
    'sharpstock_page_header',
    'sharpstock_status_badge',
    'sharpstock_trend_indicator',
    'sharpstock_metric_dashboard'
]
