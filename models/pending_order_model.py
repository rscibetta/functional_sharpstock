"""
Data model for pending orders
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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
    order_reference: Optional[str] = None
    unit_cost: Optional[float] = None
    supplier: Optional[str] = None
    confidence_level: float = 1.0  # 0.0 to 1.0, how confident we are this order will arrive