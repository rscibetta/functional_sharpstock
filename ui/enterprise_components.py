"""
Enterprise-grade UI components for SharpStock
Professional, reusable components with consistent design language
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# =====================================
# ENTERPRISE BRANDING & HEADERS
# =====================================

def enterprise_page_header(title: str, subtitle: str = "", icon: str = "", show_back_button: bool = False):
    """Professional page header with consistent branding"""
    
    if show_back_button:
        col1, col2 = st.columns([1, 10])
        with col1:
            if st.button("←", help="Go back", key="back_button"):
                # Navigate back logic here
                st.rerun()
        with col2:
            _render_header_content(title, subtitle, icon)
    else:
        _render_header_content(title, subtitle, icon)

def _render_header_content(title: str, subtitle: str, icon: str):
    """Render header content with enterprise styling"""
    
    if icon:
        st.markdown(f"""
        <div class="animate-fade-in" style="
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 24px;
            padding: 24px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        ">
            <div style="
                font-size: 3rem;
                filter: drop-shadow(0 0 20px rgba(14, 165, 233, 0.4));
            ">{icon}</div>
            <div>
                <h1 style="
                    margin: 0;
                    font-size: 2.5rem;
                    font-weight: 800;
                    background: linear-gradient(135deg, #0EA5E9, #38BDF8);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                ">{title}</h1>
                {f'<p style="margin: 8px 0 0 0; color: #94A3B8; font-size: 1.1rem; font-weight: 500;">{subtitle}</p>' if subtitle else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="animate-fade-in" style="
            margin-bottom: 24px;
            padding: 24px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        ">
            <h1 style="
                margin: 0;
                font-size: 2.5rem;
                font-weight: 800;
                background: linear-gradient(135deg, #0EA5E9, #38BDF8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            ">{title}</h1>
            {f'<p style="margin: 8px 0 0 0; color: #94A3B8; font-size: 1.1rem; font-weight: 500;">{subtitle}</p>' if subtitle else ''}
        </div>
        """, unsafe_allow_html=True)

def enterprise_section_header(title: str, description: str = "", icon: str = "", actions: List[Dict] = None):
    """Professional section headers with optional actions"""
    
    col1, col2 = st.columns([3, 1]) if actions else st.columns([1])
    
    with col1:
        header_content = f"{icon} {title}" if icon else title
        st.markdown(f"""
        <div style="margin: 32px 0 16px 0;">
            <h2 style="
                margin: 0;
                font-size: 1.5rem;
                font-weight: 700;
                color: #FFFFFF;
                display: flex;
                align-items: center;
                gap: 12px;
            ">{header_content}</h2>
            {f'<p style="margin: 8px 0 0 0; color: #94A3B8; font-size: 0.95rem;">{description}</p>' if description else ''}
        </div>
        """, unsafe_allow_html=True)
    
    if actions and col2:
        with col2:
            for action in actions:
                if st.button(
                    action.get('label', 'Action'),
                    type=action.get('type', 'secondary'),
                    key=action.get('key', f"action_{action.get('label')}")
                ):
                    action.get('callback', lambda: None)()

# =====================================
# ENTERPRISE METRICS & KPIs
# =====================================

def enterprise_metric_card(
    title: str, 
    value: str, 
    delta: str = "", 
    delta_type: str = "neutral",
    icon: str = "📊", 
    help_text: str = "",
    variant: str = "default",
    click_callback: callable = None
):
    """Professional metric card with enhanced styling"""
    
    # Determine delta styling
    delta_class = ""
    delta_display = ""
    if delta:
        if delta_type == "positive" or (delta.startswith("+") and delta_type == "neutral"):
            delta_class = "positive"
            delta_display = f"<span class='metric-delta positive'>{delta}</span>"
        elif delta_type == "negative" or (delta.startswith("-") and delta_type == "neutral"):
            delta_class = "negative" 
            delta_display = f"<span class='metric-delta negative'>{delta}</span>"
        else:
            delta_class = "neutral"
            delta_display = f"<span class='metric-delta neutral'>{delta}</span>"
    
    # Variant-specific styling
    variant_styles = {
        "default": "",
        "primary": "border-left: 4px solid var(--primary);",
        "success": "border-left: 4px solid var(--success);",
        "warning": "border-left: 4px solid var(--warning);",
        "error": "border-left: 4px solid var(--error);"
    }
    
    card_style = variant_styles.get(variant, "")
    
    # Render the card
    card_html = f"""
    <div class="enterprise-metric-card animate-fade-in" style="{card_style}" title="{help_text}">
        <div class="metric-icon">{icon}</div>
        <div class="metric-label">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_display}
    </div>
    """
    
    if click_callback:
        # Make it clickable
        if st.button("", key=f"metric_{title}_{value}", help=help_text):
            click_callback()
        st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.markdown(card_html, unsafe_allow_html=True)

def enterprise_metric_dashboard(metrics: List[Dict], columns: int = 4):
    """Display multiple metrics in a professional dashboard layout"""
    
    # Calculate responsive columns
    if len(metrics) < columns:
        columns = len(metrics)
    
    # Create rows of metrics
    for i in range(0, len(metrics), columns):
        row_metrics = metrics[i:i + columns]
        cols = st.columns(len(row_metrics))
        
        for j, metric in enumerate(row_metrics):
            with cols[j]:
                enterprise_metric_card(
                    title=metric.get('title', 'Metric'),
                    value=metric.get('value', '0'),
                    delta=metric.get('delta', ''),
                    delta_type=metric.get('delta_type', 'neutral'),
                    icon=metric.get('icon', '📊'),
                    help_text=metric.get('help_text', ''),
                    variant=metric.get('variant', 'default'),
                    click_callback=metric.get('click_callback')
                )

# =====================================
# ENTERPRISE ALERTS & NOTIFICATIONS
# =====================================

def enterprise_alert(
    message: str, 
    alert_type: str = "info", 
    dismissible: bool = False,
    icon: str = None,
    actions: List[Dict] = None
):
    """Professional alert system with enhanced styling"""
    
    # Alert type configurations
    alert_configs = {
        'info': {'emoji': '💡', 'class': 'info'},
        'success': {'emoji': '✅', 'class': 'success'},
        'warning': {'emoji': '⚠️', 'class': 'warning'},
        'error': {'emoji': '🚨', 'class': 'error'},
        'primary': {'emoji': '⚡', 'class': 'primary'}
    }
    
    config = alert_configs.get(alert_type, alert_configs['info'])
    display_icon = icon or config['emoji']
    
    # Create alert container
    alert_html = f"""
    <div class="enterprise-alert glass-card animate-fade-in" style="
        padding: 16px 20px;
        margin: 16px 0;
        border-left: 4px solid var(--{config['class']});
        background: var(--{config['class']}-bg);
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 500;
    ">
        <span style="font-size: 1.25rem;">{display_icon}</span>
        <div style="flex: 1;">{message}</div>
        {_render_alert_actions(actions) if actions else ''}
    </div>
    """
    
    st.markdown(alert_html, unsafe_allow_html=True)
    
    # Handle actions
    if actions:
        for action in actions:
            if st.button(
                action.get('label', 'Action'),
                key=action.get('key', f"alert_action_{action.get('label')}"),
                type=action.get('type', 'secondary')
            ):
                action.get('callback', lambda: None)()

def _render_alert_actions(actions: List[Dict]) -> str:
    """Render action buttons for alerts"""
    if not actions:
        return ""
    
    # For now, return empty string - buttons handled separately
    # In a full implementation, you'd render inline buttons
    return ""

# =====================================
# ENTERPRISE STATUS INDICATORS
# =====================================

def enterprise_status_badge(
    status: str, 
    variant: str = "default",
    size: str = "md",
    pulse: bool = False
) -> str:
    """Professional status badges with consistent styling"""
    
    status_configs = {
        'CRITICAL': {'color': 'var(--error)', 'bg': 'var(--error-bg)', 'icon': '🔴'},
        'HIGH': {'color': 'var(--warning)', 'bg': 'var(--warning-bg)', 'icon': '🟠'},
        'MEDIUM': {'color': 'var(--info)', 'bg': 'var(--info-bg)', 'icon': '🟡'},
        'LOW': {'color': 'var(--success)', 'bg': 'var(--success-bg)', 'icon': '🟢'},
        'SUCCESS': {'color': 'var(--success)', 'bg': 'var(--success-bg)', 'icon': '✅'},
        'WARNING': {'color': 'var(--warning)', 'bg': 'var(--warning-bg)', 'icon': '⚠️'},
        'ERROR': {'color': 'var(--error)', 'bg': 'var(--error-bg)', 'icon': '❌'},
        'INFO': {'color': 'var(--info)', 'bg': 'var(--info-bg)', 'icon': 'ℹ️'},
        'TRENDING': {'color': 'var(--success)', 'bg': 'var(--success-bg)', 'icon': '📈'},
        'DECLINING': {'color': 'var(--error)', 'bg': 'var(--error-bg)', 'icon': '📉'},
        'NEW': {'color': 'var(--primary)', 'bg': 'var(--primary-glow)', 'icon': '✨'},
        'ACTIVE': {'color': 'var(--success)', 'bg': 'var(--success-bg)', 'icon': '●'},
        'INACTIVE': {'color': 'var(--gray-500)', 'bg': 'rgba(100, 116, 139, 0.1)', 'icon': '○'}
    }
    
    config = status_configs.get(status.upper(), {
        'color': 'var(--text-tertiary)', 
        'bg': 'rgba(148, 163, 184, 0.1)', 
        'icon': '○'
    })
    
    size_configs = {
        'sm': {'padding': '4px 8px', 'font_size': '0.75rem'},
        'md': {'padding': '6px 12px', 'font_size': '0.875rem'},
        'lg': {'padding': '8px 16px', 'font_size': '1rem'}
    }
    
    size_config = size_configs.get(size, size_configs['md'])
    pulse_class = 'animate-pulse' if pulse else ''
    
    return f"""
    <span class="enterprise-status-badge {pulse_class}" style="
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: {size_config['padding']};
        background: {config['bg']};
        color: {config['color']};
        border: 1px solid {config['color']};
        border-radius: var(--radius-md);
        font-size: {size_config['font_size']};
        font-weight: 600;
        line-height: 1;
        letter-spacing: 0.025em;
    ">
        <span>{config['icon']}</span>
        <span>{status}</span>
    </span>
    """

def enterprise_progress_bar(
    progress: float, 
    label: str = "", 
    show_percentage: bool = True,
    variant: str = "primary",
    size: str = "md"
):
    """Professional progress bar with smooth animations"""
    
    # Clamp progress between 0 and 1
    progress = max(0, min(1, progress))
    percentage = int(progress * 100)
    
    variant_colors = {
        'primary': 'var(--primary)',
        'success': 'var(--success)',
        'warning': 'var(--warning)',
        'error': 'var(--error)'
    }
    
    size_configs = {
        'sm': '6px',
        'md': '8px',
        'lg': '12px'
    }
    
    color = variant_colors.get(variant, variant_colors['primary'])
    height = size_configs.get(size, size_configs['md'])
    
    progress_html = f"""
    <div style="margin: 16px 0;">
        {f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;"><span style="color: var(--text-secondary); font-weight: 500;">{label}</span><span style="color: var(--text-tertiary); font-size: 0.875rem;">{percentage}%</span></div>' if label or show_percentage else ''}
        <div style="
            width: 100%;
            height: {height};
            background: var(--bg-tertiary);
            border-radius: var(--radius-md);
            overflow: hidden;
            position: relative;
        ">
            <div style="
                width: {percentage}%;
                height: 100%;
                background: linear-gradient(90deg, {color}, {color}88);
                border-radius: var(--radius-md);
                transition: width 0.8s ease-out;
                position: relative;
                overflow: hidden;
            ">
                <div style="
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                    animation: shimmer 2s infinite;
                "></div>
            </div>
        </div>
    </div>
    
    <style>
    @keyframes shimmer {{
        0% {{ transform: translateX(-100%); }}
        100% {{ transform: translateX(100%); }}
    }}
    </style>
    """
    
    st.markdown(progress_html, unsafe_allow_html=True)

# =====================================
# ENTERPRISE TABLES & DATA DISPLAY
# =====================================

def enterprise_data_table(
    data: Union[pd.DataFrame, List[Dict]], 
    title: str = "",
    searchable: bool = True,
    sortable: bool = True,
    clickable_rows: bool = False,
    actions: List[Dict] = None,
    max_height: int = 600
):
    """Professional data table with advanced features"""
    
    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()
    
    if df.empty:
        st.info("No data available")
        return
    
    # Table header
    if title:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <h3 style="
                margin: 0 0 16px 0;
                color: var(--text-primary);
                font-weight: 600;
            ">{title}</h3>
            """, unsafe_allow_html=True)
        
        if actions:
            with col2:
                for action in actions:
                    if st.button(
                        action.get('label', 'Action'),
                        key=action.get('key', f"table_action_{action.get('label')}"),
                        type=action.get('type', 'secondary')
                    ):
                        action.get('callback', lambda: None)()
    
    # Search functionality
    if searchable and len(df) > 10:
        search_term = st.text_input(
            "🔍 Search table",
            placeholder="Type to search...",
            key=f"search_{title}"
        )
        
        if search_term:
            # Search across all string columns
            mask = df.astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            df = df[mask]
    
    # Display table with custom styling
    st.markdown("""
    <style>
    .enterprise-table {
        background: var(--bg-card);
        border-radius: var(--radius-lg);
        border: 1px solid rgba(255, 255, 255, 0.1);
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Enhanced dataframe display
    st.dataframe(
        df,
        use_container_width=True,
        height=min(max_height, len(df) * 35 + 50),
        hide_index=True
    )
    
    # Table footer with row count
    st.caption(f"Showing {len(df)} {'row' if len(df) == 1 else 'rows'}")

# =====================================
# ENTERPRISE CHARTS & VISUALIZATIONS
# =====================================

def create_enterprise_chart(
    data: pd.DataFrame,
    chart_type: str = "bar",
    title: str = "",
    x: str = None,
    y: str = None,
    color: str = None,
    height: int = 400,
    **kwargs
):
    """Professional charts with SharpStock branding"""
    
    # SharpStock color palette
    colors = [
        '#0EA5E9',  # Primary blue
        '#38BDF8',  # Light blue
        '#0284C7',  # Dark blue
        '#10B981',  # Success green
        '#F59E0B',  # Warning amber
        '#EF4444',  # Error red
        '#8B5CF6',  # Purple accent
        '#06B6D4',  # Cyan
        '#84CC16',  # Lime
        '#F97316'   # Orange
    ]
    
    # Create chart based on type
    if chart_type == "bar":
        fig = px.bar(data, x=x, y=y, color=color, color_discrete_sequence=colors, **kwargs)
    elif chart_type == "line":
        fig = px.line(data, x=x, y=y, color=color, color_discrete_sequence=colors, **kwargs)
    elif chart_type == "pie":
        fig = px.pie(data, values=y, names=x, color_discrete_sequence=colors, **kwargs)
    elif chart_type == "scatter":
        fig = px.scatter(data, x=x, y=y, color=color, color_discrete_sequence=colors, **kwargs)
    elif chart_type == "area":
        fig = px.area(data, x=x, y=y, color=color, color_discrete_sequence=colors, **kwargs)
    else:
        fig = px.bar(data, x=x, y=y, color=color, color_discrete_sequence=colors, **kwargs)
    
    # Apply enterprise theme
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#FFFFFF', 'family': 'Inter'}
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': '#FFFFFF', 'family': 'Inter'},
        height=height,
        margin=dict(t=60, l=60, r=60, b=60),
        xaxis={
            'gridcolor': 'rgba(255,255,255,0.1)',
            'color': '#D1D5DB',
            'tickfont': {'size': 12},
            'titlefont': {'size': 14}
        },
        yaxis={
            'gridcolor': 'rgba(255,255,255,0.1)',
            'color': '#D1D5DB',
            'tickfont': {'size': 12},
            'titlefont': {'size': 14}
        },
        legend={
            'font': {'color': '#D1D5DB', 'size': 12},
            'bgcolor': 'rgba(55, 65, 81, 0.8)',
            'bordercolor': 'rgba(14, 165, 233, 0.3)',
            'borderwidth': 1
        },
        hovermode='x unified'
    )
    
    # Add subtle hover effects
    fig.update_traces(
        hovertemplate='<b>%{x}</b><br>%{y}<extra></extra>',
        hoverlabel=dict(
            bgcolor="rgba(55, 65, 81, 0.9)",
            bordercolor="rgba(14, 165, 233, 0.5)",
            font_color="white"
        )
    )
    
    return fig

# =====================================
# ENTERPRISE FORMS & INPUTS
# =====================================

def enterprise_form_section(title: str, description: str = "", collapsible: bool = False):
    """Professional form section headers"""
    
    if collapsible:
        with st.expander(f"📋 {title}", expanded=True):
            if description:
                st.caption(description)
            yield
    else:
        st.markdown(f"""
        <div style="
            margin: 24px 0 16px 0;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        ">
            <h3 style="
                margin: 0;
                color: var(--text-primary);
                font-weight: 600;
                font-size: 1.25rem;
            ">📋 {title}</h3>
            {f'<p style="margin: 8px 0 0 0; color: var(--text-tertiary); font-size: 0.9rem;">{description}</p>' if description else ''}
        </div>
        """, unsafe_allow_html=True)

def enterprise_button_group(
    buttons: List[Dict], 
    layout: str = "horizontal",
    full_width: bool = True
):
    """Professional button groups with consistent styling"""
    
    if layout == "horizontal":
        cols = st.columns(len(buttons))
        for i, button_config in enumerate(buttons):
            with cols[i]:
                _render_button(button_config, full_width)
    else:  # vertical
        for button_config in buttons:
            _render_button(button_config, full_width)

def _render_button(button_config: Dict, full_width: bool = True):
    """Render individual button with enterprise styling"""
    
    return st.button(
        button_config.get('label', 'Button'),
        type=button_config.get('type', 'secondary'),
        disabled=button_config.get('disabled', False),
        help=button_config.get('help', ''),
        use_container_width=full_width,
        key=button_config.get('key', f"btn_{button_config.get('label')}")
    )

# =====================================
# ENTERPRISE LOADING & FEEDBACK
# =====================================

def enterprise_loading_spinner(message: str = "Loading...", size: str = "md"):
    """Professional loading indicators"""
    
    size_configs = {
        'sm': '20px',
        'md': '32px', 
        'lg': '48px'
    }
    
    spinner_size = size_configs.get(size, size_configs['md'])
    
    loading_html = f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 48px 24px;
        text-align: center;
    ">
        <div style="
            width: {spinner_size};
            height: {spinner_size};
            border: 3px solid rgba(14, 165, 233, 0.3);
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 16px;
        "></div>
        <p style="
            color: var(--text-secondary);
            font-weight: 500;
            margin: 0;
        ">{message}</p>
    </div>
    
    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """
    
    return loading_html

def enterprise_skeleton_loader(lines: int = 3, height: str = "20px"):
    """Professional skeleton loading placeholders"""
    
    skeleton_html = "<div style='padding: 16px 0;'>"
    
    for i in range(lines):
        width = "100%" if i < lines - 1 else "60%"
        skeleton_html += f"""
        <div style="
            height: {height};
            background: linear-gradient(90deg, rgba(255,255,255,0.1) 25%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.1) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: var(--radius-sm);
            margin-bottom: 12px;
            width: {width};
        "></div>
        """
    
    skeleton_html += """
    </div>
    
    <style>
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    </style>
    """
    
    return skeleton_html

# =====================================
# UTILITY FUNCTIONS
# =====================================

def render_empty_state(
    title: str = "No Data Available",
    description: str = "There's nothing to show here yet.",
    icon: str = "📭",
    action_label: str = None,
    action_callback: callable = None
):
    """Professional empty state display"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 64px 24px;
            background: var(--bg-card);
            border-radius: var(--radius-xl);
            border: 1px solid rgba(255, 255, 255, 0.1);
        ">
            <div style="font-size: 4rem; margin-bottom: 24px; opacity: 0.6;">{icon}</div>
            <h3 style="
                color: var(--text-primary);
                margin: 0 0 12px 0;
                font-weight: 600;
            ">{title}</h3>
            <p style="
                color: var(--text-tertiary);
                margin: 0 0 24px 0;
                font-size: 1rem;
                line-height: 1.5;
            ">{description}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if action_label and action_callback:
            if st.button(action_label, type="primary", use_container_width=True):
                action_callback()

def format_number(value: Union[int, float], format_type: str = "standard") -> str:
    """Format numbers for display with appropriate precision"""
    
    if pd.isna(value) or value is None:
        return "—"
    
    if format_type == "currency":
        if abs(value) >= 1000000:
            return f"${value/1000000:.1f}M"
        elif abs(value) >= 1000:
            return f"${value/1000:.1f}K"
        else:
            return f"${value:,.0f}"
    
    elif format_type == "percentage":
        return f"{value:.1f}%"
    
    elif format_type == "compact":
        if abs(value) >= 1000000:
            return f"{value/1000000:.1f}M"
        elif abs(value) >= 1000:
            return f"{value/1000:.1f}K"
        else:
            return f"{value:,.0f}"
    
    else:  # standard
        return f"{value:,.0f}" if isinstance(value, int) else f"{value:,.1f}"

# =====================================
# EXPORT ALL COMPONENTS
# =====================================

__all__ = [
    'enterprise_page_header',
    'enterprise_section_header', 
    'enterprise_metric_card',
    'enterprise_metric_dashboard',
    'enterprise_alert',
    'enterprise_status_badge',
    'enterprise_progress_bar',
    'enterprise_data_table',
    'create_enterprise_chart',
    'enterprise_form_section',
    'enterprise_button_group',
    'enterprise_loading_spinner',
    'enterprise_skeleton_loader',
    'render_empty_state',
    'format_number'
]
