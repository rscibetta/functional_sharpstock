"""
Enterprise-grade CSS styling for SharpStock
Comprehensive visual overhaul to achieve professional SaaS appearance
"""
import streamlit as st

def apply_enterprise_styles():
    """Apply comprehensive enterprise styling to override Streamlit defaults"""
    
    st.markdown("""
    <style>
    /* ========================================
       ENTERPRISE CSS FRAMEWORK - SHARPSTOCK
       ======================================== */
    
    /* Import Professional Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* CSS Variables - Design System */
    :root {
        /* Brand Colors */
        --primary: #0EA5E9;
        --primary-dark: #0284C7;
        --primary-light: #38BDF8;
        --primary-glow: rgba(14, 165, 233, 0.2);
        
        /* Neutrals */
        --gray-50: #F8FAFC;
        --gray-100: #F1F5F9;
        --gray-200: #E2E8F0;
        --gray-300: #CBD5E1;
        --gray-400: #94A3B8;
        --gray-500: #64748B;
        --gray-600: #475569;
        --gray-700: #334155;
        --gray-800: #1E293B;
        --gray-900: #0F172A;
        
        /* Semantic Colors */
        --success: #10B981;
        --success-light: #34D399;
        --success-bg: rgba(16, 185, 129, 0.1);
        --warning: #F59E0B;
        --warning-light: #FBBF24;
        --warning-bg: rgba(245, 158, 11, 0.1);
        --error: #EF4444;
        --error-light: #F87171;
        --error-bg: rgba(239, 68, 68, 0.1);
        --info: #3B82F6;
        --info-bg: rgba(59, 130, 246, 0.1);
        
        /* Backgrounds */
        --bg-primary: #0F172A;
        --bg-secondary: #1E293B;
        --bg-tertiary: #334155;
        --bg-elevated: #475569;
        --bg-glass: rgba(255, 255, 255, 0.05);
        --bg-card: rgba(255, 255, 255, 0.02);
        
        /* Text */
        --text-primary: #FFFFFF;
        --text-secondary: #E2E8F0;
        --text-tertiary: #94A3B8;
        --text-muted: #64748B;
        
        /* Spacing Scale */
        --space-xs: 4px;
        --space-sm: 8px;
        --space-md: 16px;
        --space-lg: 24px;
        --space-xl: 32px;
        --space-2xl: 48px;
        --space-3xl: 64px;
        
        /* Border Radius */
        --radius-sm: 6px;
        --radius-md: 8px;
        --radius-lg: 12px;
        --radius-xl: 16px;
        --radius-2xl: 24px;
        
        /* Shadows */
        --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        --shadow-glow: 0 0 20px var(--primary-glow);
        --shadow-glow-lg: 0 0 40px var(--primary-glow);
        
        /* Transitions */
        --transition-fast: 150ms ease;
        --transition-normal: 300ms ease;
        --transition-slow: 500ms ease;
    }
    
    /* ========================================
       GLOBAL OVERRIDES
       ======================================== */
    
    /* Remove Streamlit branding and defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Global font and background */
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--text-primary);
    }
    
    /* Main container improvements */
    .main .block-container {
        padding: var(--space-lg) var(--space-xl);
        max-width: 100%;
        background: transparent;
    }
    
    /* ========================================
       ENHANCED METRIC CARDS
       ======================================== */
    
    .enterprise-metric-card {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: var(--radius-lg);
        padding: var(--space-lg);
        transition: all var(--transition-normal);
        position: relative;
        overflow: hidden;
    }
    
    .enterprise-metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary), var(--primary-light));
        opacity: 0;
        transition: opacity var(--transition-normal);
    }
    
    .enterprise-metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-glow);
        border-color: var(--primary);
    }
    
    .enterprise-metric-card:hover::before {
        opacity: 1;
    }
    
    .metric-icon {
        font-size: 2rem;
        margin-bottom: var(--space-sm);
        filter: drop-shadow(0 0 10px var(--primary-glow));
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.2;
        margin: var(--space-sm) 0;
    }
    
    .metric-label {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: var(--space-xs);
    }
    
    .metric-delta {
        font-size: 0.75rem;
        font-weight: 500;
        padding: 2px 8px;
        border-radius: var(--radius-sm);
        display: inline-block;
    }
    
    .metric-delta.positive {
        background: var(--success-bg);
        color: var(--success-light);
    }
    
    .metric-delta.negative {
        background: var(--error-bg);
        color: var(--error-light);
    }
    
    .metric-delta.neutral {
        background: var(--info-bg);
        color: var(--text-tertiary);
    }
    
    /* ========================================
       PROFESSIONAL NAVIGATION
       ======================================== */
    
    /* Enhanced sidebar */
    .css-1d391kg, .css-1lcbmhc {
        background: var(--bg-secondary);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card);
        border-radius: var(--radius-lg);
        padding: var(--space-xs);
        border: 1px solid rgba(255, 255, 255, 0.1);
        gap: var(--space-xs);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: var(--radius-md);
        font-weight: 500;
        padding: var(--space-md) var(--space-lg);
        transition: all var(--transition-fast);
        border: none;
        color: var(--text-tertiary);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.05);
        color: var(--text-secondary);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary) !important;
        color: white !important;
        box-shadow: var(--shadow-glow);
    }
    
    /* ========================================
       ENHANCED BUTTONS
       ======================================== */
    
    .stButton > button {
        background: var(--bg-tertiary);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: var(--radius-md);
        color: var(--text-primary);
        font-weight: 500;
        padding: var(--space-md) var(--space-lg);
        transition: all var(--transition-fast);
        font-family: inherit;
    }
    
    .stButton > button:hover {
        background: var(--primary);
        border-color: var(--primary);
        transform: translateY(-1px);
        box-shadow: var(--shadow-glow);
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary), var(--primary-dark));
        border-color: var(--primary);
        color: white;
        font-weight: 600;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--primary-light), var(--primary));
        box-shadow: var(--shadow-glow-lg);
    }
    
    .stButton > button[kind="secondary"] {
        background: transparent;
        border-color: var(--gray-600);
        color: var(--text-secondary);
    }
    
    /* ========================================
       ENHANCED FORMS
       ======================================== */
    
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        background: var(--bg-card);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: var(--radius-md);
        color: var(--text-primary);
        font-family: inherit;
        transition: all var(--transition-fast);
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus-within,
    .stNumberInput > div > div > input:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px var(--primary-glow);
        outline: none;
    }
    
    /* ========================================
       ENHANCED TABLES
       ======================================== */
    
    .stDataFrame {
        background: var(--bg-card);
        border-radius: var(--radius-lg);
        border: 1px solid rgba(255, 255, 255, 0.1);
        overflow: hidden;
    }
    
    .stDataFrame table {
        font-family: inherit;
    }
    
    .stDataFrame thead th {
        background: var(--bg-tertiary);
        color: var(--text-secondary);
        font-weight: 600;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: var(--space-md);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stDataFrame tbody td {
        padding: var(--space-md);
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        color: var(--text-primary);
    }
    
    .stDataFrame tbody tr:hover {
        background: rgba(255, 255, 255, 0.02);
    }
    
    /* ========================================
       ENHANCED ALERTS
       ======================================== */
    
    .stAlert {
        border-radius: var(--radius-lg);
        border: none;
        backdrop-filter: blur(20px);
        font-weight: 500;
    }
    
    .stAlert[data-baseweb="notification"][kind="info"] {
        background: var(--info-bg);
        border-left: 4px solid var(--info);
    }
    
    .stAlert[data-baseweb="notification"][kind="success"] {
        background: var(--success-bg);
        border-left: 4px solid var(--success);
    }
    
    .stAlert[data-baseweb="notification"][kind="warning"] {
        background: var(--warning-bg);
        border-left: 4px solid var(--warning);
    }
    
    .stAlert[data-baseweb="notification"][kind="error"] {
        background: var(--error-bg);
        border-left: 4px solid var(--error);
    }
    
    /* ========================================
       ENHANCED METRICS
       ======================================== */
    
    [data-testid="metric-container"] {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: var(--radius-lg);
        padding: var(--space-lg);
        transition: all var(--transition-normal);
        position: relative;
        overflow: hidden;
    }
    
    [data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary), var(--primary-light));
        opacity: 0.8;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-glow);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    [data-testid="metric-container"] [data-testid="metric-label"] {
        color: var(--text-secondary);
        font-weight: 500;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    [data-testid="metric-container"] [data-testid="metric-delta"] {
        font-weight: 600;
        font-size: 0.75rem;
    }
    
    /* ========================================
       ENHANCED EXPANDERS
       ======================================== */
    
    .streamlit-expanderHeader {
        background: var(--bg-card);
        border-radius: var(--radius-lg);
        border: 1px solid rgba(255, 255, 255, 0.1);
        font-weight: 600;
        color: var(--text-primary);
        transition: all var(--transition-fast);
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--bg-tertiary);
        border-color: var(--primary);
    }
    
    .streamlit-expanderContent {
        background: var(--bg-card);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-top: none;
        border-radius: 0 0 var(--radius-lg) var(--radius-lg);
    }
    
    /* ========================================
       CUSTOM SCROLLBAR
       ======================================== */
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
        border-radius: var(--radius-sm);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--gray-600);
        border-radius: var(--radius-sm);
        transition: background var(--transition-fast);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary);
    }
    
    /* ========================================
       RESPONSIVE UTILITIES
       ======================================== */
    
    @media (max-width: 768px) {
        .main .block-container {
            padding: var(--space-md);
        }
        
        .enterprise-metric-card {
            padding: var(--space-md);
        }
        
        .metric-value {
            font-size: 1.5rem;
        }
    }
    
    /* ========================================
       ANIMATION UTILITIES
       ======================================== */
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    .animate-fade-in {
        animation: fadeInUp 0.5s ease-out;
    }
    
    .animate-pulse {
        animation: pulse 2s infinite;
    }
    
    /* ========================================
       UTILITY CLASSES
       ======================================== */
    
    .glass-card {
        background: var(--bg-glass);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: var(--radius-lg);
    }
    
    .gradient-border {
        position: relative;
        background: var(--bg-card);
        border-radius: var(--radius-lg);
    }
    
    .gradient-border::before {
        content: '';
        position: absolute;
        inset: 0;
        padding: 1px;
        background: linear-gradient(135deg, var(--primary), var(--primary-light));
        border-radius: inherit;
        mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        mask-composite: exclude;
    }
    
    .text-gradient {
        background: linear-gradient(135deg, var(--primary), var(--primary-light));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    </style>
    """, unsafe_allow_html=True)
