"""
Safe data processing utilities with robust error handling
Fixes list index out of range errors
"""
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any
from models.data_models import UserProfile

def process_orders_fast(orders: List[Dict], location_config: Dict[int, str]) -> pd.DataFrame:
    """
    FIXED: Process Shopify orders with proper store location mapping
    """
    
    if not orders:
        return pd.DataFrame()
    
    processed_orders = []
    
    # Create reverse mapping for location lookup
    location_id_to_name = location_config  # {location_id: store_name}
    location_name_to_id = {v: k for k, v in location_config.items()}  # {store_name: location_id}
    
    for order in orders:
        try:
            order_number = order.get('name', order.get('order_number', 'Unknown'))
            order_id = order.get('id')
            created_at = pd.to_datetime(order.get('created_at'))
            
            # ENHANCED LOCATION DETECTION
            store_location = "Unknown"
            location_id = None
            
            # Method 1: Check order-level location_id
            if order.get('location_id'):
                location_id = int(order['location_id'])
                store_location = location_config.get(location_id, "Unknown")
            
            # Method 2: Check fulfillments for location_id
            elif order.get('fulfillments'):
                for fulfillment in order['fulfillments']:
                    if fulfillment.get('location_id'):
                        location_id = int(fulfillment['location_id'])
                        store_location = location_config.get(location_id, "Unknown")
                        break
            
            # Method 3: Check line items for fulfillment_service or properties
            elif order.get('line_items'):
                for line_item in order['line_items']:
                    # Check if fulfillment_service indicates a specific location
                    fulfillment_service = line_item.get('fulfillment_service')
                    if fulfillment_service and fulfillment_service != 'manual':
                        # Try to match fulfillment service to location names
                        for loc_name in location_config.values():
                            if loc_name.lower() in fulfillment_service.lower():
                                store_location = loc_name
                                location_id = location_name_to_id.get(loc_name)
                                break
                        if store_location != "Unknown":
                            break
                    
                    # Check line item properties for location hints
                    if line_item.get('properties'):
                        for prop in line_item['properties']:
                            prop_name = prop.get('name', '').lower()
                            prop_value = str(prop.get('value', '')).lower()
                            
                            if 'location' in prop_name or 'store' in prop_name:
                                for loc_name in location_config.values():
                                    if loc_name.lower() in prop_value:
                                        store_location = loc_name
                                        location_id = location_name_to_id.get(loc_name)
                                        break
                                if store_location != "Unknown":
                                    break
                        if store_location != "Unknown":
                            break
            
            # Method 4: Check shipping address for location hints (for pickup orders)
            if store_location == "Unknown" and order.get('shipping_address'):
                shipping_address = order['shipping_address']
                city = shipping_address.get('city', '').lower()
                
                # Map common city names to store locations
                city_to_store = {
                    'hilo': 'Hilo',
                    'kailua': 'Kailua', 
                    'kailua-kona': 'Kailua',
                    'kapaa': 'Kapaa',
                    'wailuku': 'Wailuku'
                }
                
                for city_name, store_name in city_to_store.items():
                    if city_name in city and store_name in location_config.values():
                        store_location = store_name
                        location_id = location_name_to_id.get(store_name)
                        break
            
            # Method 5: Check order tags for location information
            if store_location == "Unknown" and order.get('tags'):
                tags = order['tags'].lower()
                for loc_name in location_config.values():
                    if loc_name.lower() in tags:
                        store_location = loc_name
                        location_id = location_name_to_id.get(loc_name)
                        break
            
            # Method 6: Fallback - if still unknown, try to distribute based on customer location
            if store_location == "Unknown" and order.get('billing_address'):
                billing_address = order['billing_address']
                zip_code = billing_address.get('zip', '')
                
                # Basic Hawaii zip code to store mapping
                zip_to_store = {
                    '96720': 'Hilo',    # Hilo area
                    '96740': 'Kailua',  # Kailua-Kona area  
                    '96746': 'Kapaa',   # Kapaa area
                    '96793': 'Wailuku'  # Wailuku area
                }
                
                store_location = zip_to_store.get(zip_code, "Unknown")
                if store_location != "Unknown":
                    location_id = location_name_to_id.get(store_location)
            
            # Process line items
            line_items = order.get('line_items', [])
            
            for line_item in line_items:
                try:
                    # Basic line item data
                    product_id = line_item.get('product_id')
                    variant_id = line_item.get('variant_id') 
                    quantity = int(line_item.get('quantity', 0))
                    price = float(line_item.get('price', 0))
                    total_value = quantity * price
                    
                    # Product information
                    title = line_item.get('title', 'Unknown Product')
                    vendor = line_item.get('vendor', 'Unknown')
                    sku = line_item.get('sku', '')
                    
                    # Enhanced variant parsing
                    variant_title = line_item.get('variant_title', 'Default Title')
                    
                    # Parse style number from SKU or title
                    style_number = sku if sku else extract_style_number_from_title(title)
                    
                    # Parse color and size from variant_title
                    color, size = parse_variant_title(variant_title)
                    
                    processed_orders.append({
                        'order_id': order_id,
                        'order_number': order_number,
                        'created_at': created_at,
                        'product_id': product_id,
                        'variant_id': variant_id,
                        'quantity': quantity,
                        'price': price,
                        'total_value': total_value,
                        'title': title,
                        'Description': title,  # For compatibility
                        'vendor': vendor,
                        'Style Number': style_number,
                        'variant_title': variant_title,
                        'color': color,
                        'size': size,
                        'Store Location': store_location,  # FIXED: Now properly mapped
                        'location_id': location_id
                    })
                    
                except Exception as e:
                    print(f"Error processing line item: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error processing order {order.get('id', 'unknown')}: {e}")
            continue
    
    if not processed_orders:
        return pd.DataFrame()
    
    df = pd.DataFrame(processed_orders)
    
    # Data quality check
    unknown_count = len(df[df['Store Location'] == 'Unknown'])
    total_count = len(df)
    
    if unknown_count > 0:
        print(f"⚠️ Data Quality Warning: {unknown_count}/{total_count} ({unknown_count/total_count*100:.1f}%) line items have 'Unknown' store location")
        print("Consider improving location detection logic or checking Shopify order data")
    
    return df

def extract_style_number_from_title(title: str) -> str:
    """Extract style number from product title"""
    import re
    
    # Common patterns for style numbers
    patterns = [
        r'\b(\d{6})\b',  # 6-digit numbers
        r'\b([A-Z]{2,}\d+)\b',  # Letters followed by numbers
        r'\b(\d+[A-Z]+)\b',  # Numbers followed by letters
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            return match.group(1)
    
    # Fallback: use first word if no pattern found
    return title.split()[0] if title else 'Unknown'

def parse_variant_title(variant_title: str) -> tuple:
    """Parse color and size from variant title"""
    if not variant_title or variant_title == 'Default Title':
        return 'Unknown', 'Unknown'
    
    # Handle "Color / Size" format
    if ' / ' in variant_title:
        parts = variant_title.split(' / ')
        return parts[0].strip(), parts[1].strip() if len(parts) > 1 else 'Unknown'
    
    # Handle other separators
    separators = [' - ', '_', '|']
    for sep in separators:
        if sep in variant_title:
            parts = variant_title.split(sep)
            return parts[0].strip(), parts[1].strip() if len(parts) > 1 else 'Unknown'
    
    # Single value - assume it's color
    return variant_title.strip(), 'Unknown'

def create_inventory_dataframe_fast(orders_df: pd.DataFrame, variants_data: Dict, inventory_levels: Dict, location_names: Dict[int, str]) -> pd.DataFrame:
    """Create inventory dataframe with robust error handling - FIXED VERSION"""
    inventory_data = []
    
    # Validate inputs
    if variants_data is None:
        variants_data = {}
    if inventory_levels is None:
        inventory_levels = {}
    if location_names is None:
        location_names = {}
    
    total_variants_processed = 0
    error_count = 0
    
    for product_id, variants in variants_data.items():
        try:
            if not variants or not isinstance(variants, list):
                continue
            
            # SAFE product info extraction
            product_orders = orders_df[orders_df['product_id'] == product_id] if not orders_df.empty else pd.DataFrame()
            
            if not product_orders.empty:
                # SAFE access to first row with validation
                first_row = product_orders.iloc[0]
                style_number = str(first_row.get('Style Number', '')).strip()
                description = str(first_row.get('Description', '')).strip()
                vendor = str(first_row.get('vendor', '')).strip()
            else:
                style_number = description = vendor = ''
            
            # Clean empty values
            if style_number in ['None', 'nan', '', 'null']:
                style_number = f'Product_{product_id}'
            if description in ['None', 'nan', '', 'null']:
                description = 'No description'
            if vendor in ['None', 'nan', '', 'null']:
                vendor = 'Unknown'
            
            for variant_idx, variant in enumerate(variants):
                try:
                    if not isinstance(variant, dict):
                        continue
                    
                    variant_id = variant.get('id')
                    if variant_id is None:
                        continue
                    
                    try:
                        variant_id = int(variant_id)
                    except (ValueError, TypeError):
                        continue
                    
                    total_variants_processed += 1
                    
                    # SAFE variant sales calculation
                    try:
                        variant_sales = 0
                        if not orders_df.empty and 'variant_id' in orders_df.columns:
                            variant_orders = orders_df[orders_df['variant_id'] == variant_id]
                            if not variant_orders.empty:
                                variant_sales = int(variant_orders['quantity'].sum())
                    except Exception:
                        variant_sales = 0
                    
                    # SAFE variant title parsing
                    variant_title = str(variant.get('title', '')).strip()
                    if variant_title in ['None', 'nan', '', 'null']:
                        variant_title = f'Variant_{variant_id}'
                    
                    # SAFE color/size extraction
                    if ' / ' in variant_title:
                        try:
                            parts = variant_title.split(' / ')
                            color = parts[0].strip() if len(parts) > 0 else ''
                            size = parts[1].strip() if len(parts) > 1 else ''
                        except (IndexError, AttributeError):
                            color, size = variant_title, ''
                    else:
                        color, size = variant_title, ''
                    
                    # Build inventory row safely
                    row = {
                        'product_id': product_id,
                        'variant_id': variant_id,
                        'style_number': style_number,
                        'description': description,
                        'vendor': vendor,
                        'variant_title': variant_title,
                        'color': color,
                        'size': size,
                        'total_sold': max(0, variant_sales)
                    }
                    
                    # SAFE inventory levels extraction
                    variant_inventory = inventory_levels.get(variant_id, {})
                    if not isinstance(variant_inventory, dict):
                        variant_inventory = {}
                    
                    total_inventory = 0
                    
                    # Add inventory for each location safely
                    for location_id, location_name in location_names.items():
                        try:
                            # Convert location_id to int for lookup
                            location_id_int = int(location_id)
                            
                            inventory_qty = variant_inventory.get(location_id_int, 0)
                            if inventory_qty is None:
                                inventory_qty = 0
                            
                            try:
                                inventory_qty = int(inventory_qty)
                                inventory_qty = max(0, min(inventory_qty, 100000))  # Reasonable bounds
                            except (ValueError, TypeError):
                                inventory_qty = 0
                            
                            # Create column name safely
                            column_name = f'inventory_{location_name.lower().replace(" ", "_")}'
                            row[column_name] = inventory_qty
                            total_inventory += inventory_qty
                            
                        except Exception as e:
                            # Set default for this location
                            column_name = f'inventory_{location_name.lower().replace(" ", "_")}'
                            row[column_name] = 0
                    
                    row['total_inventory'] = max(0, total_inventory)
                    inventory_data.append(row)
                    
                except Exception as e:
                    error_count += 1
                    if error_count < 5:
                        st.warning(f"⚠️ Error processing variant {variant_idx}: {str(e)[:100]}")
                    continue
                    
        except Exception as e:
            error_count += 1
            if error_count < 5:
                st.warning(f"⚠️ Error processing product {product_id}: {str(e)[:100]}")
            continue
    
    # Create DataFrame safely
    if not inventory_data:
        st.warning("⚠️ No inventory data found")
        return pd.DataFrame()
    
    try:
        df = pd.DataFrame(inventory_data)
        
        # Validate DataFrame
        if df.empty:
            st.warning("⚠️ Created empty inventory DataFrame")
            return df
        
        # Clean up data
        df = df.dropna(subset=['product_id', 'variant_id'])
        df = df[(df['product_id'] > 0) & (df['variant_id'] > 0)]
        
        total_inventory_sum = df['total_inventory'].sum() if 'total_inventory' in df.columns else 0
        variants_with_inventory = (df['total_inventory'] > 0).sum() if 'total_inventory' in df.columns else 0
        
        st.success(f"📊 Inventory processed: {len(df)} variants ({variants_with_inventory:,} with inventory), Total: {total_inventory_sum:,} units")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error creating inventory DataFrame: {e}")
        return pd.DataFrame()

def get_demo_profile() -> UserProfile:
    """Return demo profile configuration - SAFE VERSION"""
    try:
        return UserProfile(
            user_id="demo_user_123",
            username="demo_user",
            email="demo@example.com",
            shop_name="naturally-birkenstock",
            encrypted_api_token="demo_encrypted_token",
            location_config={
                65859125301: 'Hilo',
                36727324725: 'Kailua', 
                36727390261: 'Kapaa',
                1223720986: 'Wailuku'
            },
            default_lead_time=14,
            created_at=datetime.now(),
            last_cache_update=None
        )
    except Exception as e:
        st.error(f"❌ Error creating demo profile: {e}")
        # Return minimal profile
        return UserProfile(
            user_id="demo_user_123",
            username="demo_user",
            email="demo@example.com",
            shop_name="demo-store",
            encrypted_api_token="demo_token",
            location_config={1: 'Store 1'},
            default_lead_time=14,
            created_at=datetime.now(),
            last_cache_update=None
        )