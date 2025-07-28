#These are data models - they define the structure of the data objects

"""Data models for Shopify Intelligence Platform"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# DATACLASSES
@dataclass
class ProductInsight:
    product_id: int
    style_number: str
    description: str
    vendor: str
    
    # Recent performance (user-selected period)
    recent_daily_demand: float
    recent_total_sales: int
    recent_revenue: float
    recent_days: int
    
    # Historical performance (2-year baseline)
    historical_daily_demand: float
    historical_total_sales: int
    historical_revenue: float
    historical_days: int
    
    # Trend analysis
    trend_classification: str  # 'Trending Up', 'Hot Seller', 'Stable', 'Declining', 'New Product'
    velocity_change: float     # % change in daily demand
    trend_strength: str        # 'Strong', 'Moderate', 'Weak'
    
    # Inventory status
    current_inventory: int
    days_until_stockout: int
    inventory_turnover: float
    
    # Recommendations
    reorder_priority: str      # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    recommended_qty: int
    reorder_timing: str        # 'Order Now', 'Order This Week', 'Monitor', 'No Action'
    reasoning: str

@dataclass
class SeasonalInsight:
    month: int
    month_name: str
    avg_daily_demand: float
    peak_products: List[Dict[str, Any]]  # Enhanced to include elevation data
    seasonal_multiplier: float

@dataclass
class UserProfile:
    user_id: str
    username: str
    email: str
    shop_name: str
    encrypted_api_token: str
    location_config: Dict[int, str]
    default_lead_time: int
    created_at: datetime
    last_cache_update: Optional[datetime] = None

@dataclass
class BrandLeadTime:
    user_id: str
    brand_name: str
    lead_time_days: int
    created_at: datetime

@dataclass
class CachedOrderData:
    user_id: str
    cache_id: str
    order_data: bytes  # Pickled DataFrame
    data_start_date: datetime
    data_end_date: datetime
    cache_date: datetime
    cache_period_years: int  # NEW: Track cache period (1, 2, 3, 4, or 5 years)

@dataclass
class TransferRecommendation:
    product_id: int
    style_number: str
    description: str
    vendor: str
    variant_id: int
    variant_title: str
    
    # Source location (has excess)
    from_location_id: int
    from_location_name: str
    from_inventory: int
    from_daily_demand: float
    from_days_of_stock: int
    
    # Destination location (needs stock)
    to_location_id: int
    to_location_name: str
    to_inventory: int
    to_daily_demand: float
    to_days_of_stock: int
    
    # Transfer details
    recommended_transfer_qty: int
    transfer_urgency: str  # 'URGENT', 'HIGH', 'MEDIUM', 'LOW'
    financial_impact: float  # Potential revenue gain
    opportunity_cost: float  # Lost sales without transfer
    
    # Analysis
    demand_imbalance_score: float  # How mismatched the inventory is
    transfer_efficiency: float     # Cost-benefit ratio
    reasoning: str

@dataclass
class VariantDemand:
    """Represents demand analysis for a specific variant"""
    product_id: int
    variant_id: int
    style_number: str
    description: str
    vendor: str
    variant_title: str
    color: str
    size: str
    
    # Store-specific demand
    store_demand: Dict[str, float]  # store_name -> daily_demand
    store_inventory: Dict[str, int]  # store_name -> current_inventory
    store_recommended: Dict[str, int]  # store_name -> recommended_qty
    
    # Overall metrics
    total_recommended: int
    total_current_inventory: int
    total_daily_demand: float
    priority_score: int

@dataclass
class OrderSheetItem:
    """Represents an item selected for an order sheet"""
    product_id: int
    variant_id: int
    style_number: str
    description: str
    color: str
    size: str
    vendor: str
    
    # Quantities by store
    qty_hilo: int = 0
    qty_kailua: int = 0
    qty_kapaa: int = 0
    qty_wailuku: int = 0
    
    # Metadata
    priority: str = "MEDIUM"
    notes: str = ""
    unit_cost: float = 0.0   

@dataclass
class PendingOrder:
    """Represents an order that has been placed but not yet received"""
    style_number: str
    variant_info: str  # Color / Size combination
    color: str
    size: str
    quantity: int
    location_name: str
    location_id: int
    expected_arrival: datetime
    brand: str
    notes: str = ""
    
    # Optional fields for enhanced tracking
   # order_reference: Optional[str] = None
   # unit_cost: Optional[float] = None
   # supplier: Optional[str] = None
   # confidence_level: float = 1.0  # 0.0 to 1.0, how confident we are this order will arrive