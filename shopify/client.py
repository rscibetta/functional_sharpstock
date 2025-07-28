"""Enhanced Shopify API client with optimized data fetching"""
import requests
import pandas as pd
import streamlit as st
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from urllib.parse import urlencode


# Configure logging
logger = logging.getLogger(__name__)

from database.database_manager import DatabaseManager
from utils.data_processing import process_orders_fast, create_inventory_dataframe_fast

# SHOPIFY CLIENT
class AdvancedShopifyClient:
    """
    Enhanced client that combines the WORKING inventory fetching from basic.txt
    with the advanced features from attempt1.txt
    """
    
    def __init__(self, shop_name: str, api_version: str, access_token: str, location_ids: List[int]):
        self.shop_name = shop_name
        self.api_version = api_version
        self.access_token = access_token
        self.location_ids = location_ids
        self.base_url = f'https://{shop_name}.myshopify.com/admin/api/{api_version}'
        self.headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Optimized settings from basic.txt
        self.max_workers = 12  # Higher concurrency
        self.request_delay = 0.08  # Faster requests (12.5 per second)
        self.cache = {}  # Simple caching
        self.lock = threading.Lock()
    
    def _make_request_fast(self, url: str, cache_key: str = None) -> Optional[Dict]:
        """Ultra-fast request method with minimal overhead - from basic.txt"""
        
        # Check cache first
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Minimal delay for rate limiting
            time.sleep(self.request_delay)
            
            response = self.session.get(url, timeout=20)
            
            # Simple rate limit handling
            if response.status_code == 429:
                time.sleep(2)
                response = self.session.get(url, timeout=20)
            
            response.raise_for_status()
            data = response.json()
            
            # Cache successful responses
            if cache_key:
                with self.lock:
                    self.cache[cache_key] = data
            
            return data
            
        except Exception as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return None
    
    def fetch_comprehensive_orders(self, recent_start: datetime, recent_end: datetime, use_cache: bool = True, user_id: str = None, db_manager: DatabaseManager = None, historical_years: int = 2) -> Tuple[List[Dict], List[Dict]]:
        """
        Fetch both recent orders and historical data with flexible year selection and caching
        """
        # Try to load cached historical data first
        cached_historical = None
        if use_cache and user_id and db_manager:
            cached_historical = db_manager.load_cached_historical_data(user_id, historical_years)
            if cached_historical is not None and not cached_historical.empty:
                st.success(f"📚 Using cached {historical_years}-year historical data")
        
        # Calculate historical period based on selected years
        historical_start = recent_end - timedelta(days=365 * historical_years)
        
        # Simple progress indicator
        with st.spinner(f"Fetching comprehensive order data ({historical_years} years historical)..."):
            # Step 1: Fetch recent orders
            recent_orders = self._fetch_orders_period(recent_start, recent_end, "recent")
            
            # Step 2: Fetch or use cached historical orders
            if cached_historical is not None and not cached_historical.empty:
                # Convert cached DataFrame back to order format for compatibility
                historical_orders = []
            else:
                historical_orders = self._fetch_orders_period(historical_start, recent_start, f"{historical_years}-year historical")
                
                # Cache the historical data if we have user info
                if user_id and db_manager and historical_orders:
                    historical_df = process_orders_fast(historical_orders, {
                        65859125301: 'Hilo', 36727324725: 'Kailua', 
                        36727390261: 'Kapaa', 1223720986: 'Wailuku'
                    })
                    if db_manager.cache_historical_data(user_id, historical_df, historical_start, recent_start, historical_years):
                        st.success(f"💾 {historical_years}-year historical data cached successfully")
        
        st.success(f"✅ Data collection complete: {len(recent_orders)} recent orders, {len(historical_orders)} {historical_years}-year historical orders")
        return recent_orders, historical_orders
    
    def _fetch_orders_period(self, start_date: datetime, end_date: datetime, period_name: str) -> List[Dict]:
        """Fetch orders for a specific period - optimized from basic.txt"""
        orders = []
        
        # Only fetch essential fields to reduce payload
        params = {
            'status': 'any',
            'created_at_min': start_date.isoformat(),
            'created_at_max': end_date.isoformat(),
            'limit': 250,
            'fields': 'id,order_number,created_at,line_items,fulfillments'
        }
        
        url = f'{self.base_url}/orders.json?{urlencode(params)}'
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        page = 1
        
        while url and page < 150:  # Safety limit
            status_text.text(f"📦 Fetching {period_name} orders - page {page}...")
            
            cache_key = f"{period_name}_orders_{hash(url)}"
            data = self._make_request_fast(url, cache_key)
            
            if not data or 'orders' not in data:
                break
            
            current_orders = data['orders']
            orders.extend(current_orders)
            
            # Handle pagination - EXACT method from basic.txt
            try:
                response = self.session.get(url)
                link_header = response.headers.get('Link', '')
                
                if 'rel="next"' in link_header:
                    for link in link_header.split(','):
                        if 'rel="next"' in link:
                            url = link.split(';')[0].strip('<> ')
                            break
                    else:
                        url = None
                else:
                    url = None
                        
            except:
                break
            
            page += 1
            progress_bar.progress(min(1.0, page * 0.01))
            
            # Show progress update every 10 pages
            if page % 10 == 0:
                status_text.text(f"📦 {period_name} orders: {len(orders)} fetched...")
        
        progress_bar.progress(1.0)
        status_text.text(f"✅ {period_name} orders: {len(orders)} total")
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
        
        return orders

    def fetch_variants_and_inventory(self, product_ids: List[int]) -> Tuple[Dict[int, List[Dict]], Dict[int, Dict[int, int]]]:
        """
        FIXED METHOD: Uses the WORKING variant and inventory fetching from basic.txt
        This is the key fix that was missing in attempt1.txt
        """
        
        progress_container = st.container()
        with progress_container:
            overall_progress = st.progress(0)
            status_text = st.empty()
        
        # Step 1: Fetch variants using the EXACT working method from basic.txt
        status_text.text("🏷️ Fetching product variants...")
        variants_data = self._fetch_all_variants_ultra_fast_WORKING(product_ids)
        overall_progress.progress(0.6)
        
        # Step 2: Fetch inventory using the EXACT working method from basic.txt
        status_text.text("📦 Fetching inventory levels...")
        inventory_levels = self._fetch_inventory_ultra_fast_WORKING(variants_data)
        overall_progress.progress(1.0)
        
        status_text.text("✅ Variants and inventory complete!")
        time.sleep(0.5)
        progress_container.empty()
        
        return variants_data, inventory_levels

    def _fetch_all_variants_ultra_fast_WORKING(self, product_ids: List[int]) -> Dict[int, List[Dict]]:
        """EXACT WORKING method from basic.txt - DO NOT MODIFY"""
        variants_data = {pid: [] for pid in product_ids}  # Initialize all
        
        # Convert to set for O(1) lookup
        target_products = set(product_ids)
        
        st.info("🚀 Fetching variants using proven working method...")
        
        # STRATEGY 1: Try bulk fetch first (fastest possible) - EXACT from basic.txt
        try:
            all_variants = self._fetch_all_variants_bulk_WORKING()
            if all_variants:
                # Filter and group in one pass
                for variant in all_variants:
                    product_id = variant.get('product_id')
                    if product_id in target_products:
                        variants_data[product_id].append(variant)
                
                st.success(f"⚡ Bulk fetched {sum(len(v) for v in variants_data.values())} variants!")
                return variants_data
        except Exception as e:
            logger.warning(f"Bulk fetch failed: {e}")
        
        # STRATEGY 2: Individual fetching - EXACT from basic.txt
        st.info("⚡ Using individual product fetching...")
        
        def fetch_product_variants(product_id: int) -> Tuple[int, List[Dict]]:
            """Fetch variants for one product - minimal fields only"""
            url = f'{self.base_url}/products/{product_id}/variants.json?fields=id,product_id,title,inventory_item_id'
            cache_key = f"variants_{product_id}"
            data = self._make_request_fast(url, cache_key)
            if data and 'variants' in data:
                return product_id, data['variants']
            return product_id, []
        
        # Process with same threading as basic.txt
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(fetch_product_variants, pid): pid for pid in product_ids}
            
            for future in as_completed(futures):
                try:
                    product_id, variants = future.result(timeout=15)
                    variants_data[product_id] = variants
                except Exception as e:
                    product_id = futures[future]
                    logger.error(f"Failed to fetch variants for {product_id}: {e}")
                    variants_data[product_id] = []
        
        return variants_data

    def _fetch_all_variants_bulk_WORKING(self) -> List[Dict]:
        """EXACT working bulk fetch from basic.txt - DO NOT MODIFY"""
        all_variants = []
        url = f'{self.base_url}/variants.json?limit=250&fields=id,product_id,title,inventory_item_id'
        
        pages = 0
        while url and pages < 20:  # Same limit as basic.txt
            cache_key = f"bulk_variants_{pages}"
            data = self._make_request_fast(url, cache_key)
            
            if not data or 'variants' not in data:
                break
                
            all_variants.extend(data['variants'])
            
            # Same pagination logic as basic.txt
            try:
                response = self.session.get(url)
                link_header = response.headers.get('Link', '')
                
                if 'rel="next"' in link_header:
                    for link in link_header.split(','):
                        if 'rel="next"' in link:
                            url = link.split(';')[0].strip('<> ')
                            break
                    else:
                        url = None
                else:
                    url = None
            except:
                break
                
            pages += 1
        
        return all_variants

    def _fetch_inventory_ultra_fast_WORKING(self, variants_data: Dict[int, List[Dict]]) -> Dict[int, Dict[int, int]]:
        """EXACT working inventory fetch from basic.txt - DO NOT MODIFY"""
        variant_inventory_levels = {}
        
        # Collect all inventory item IDs (same as basic.txt)
        inventory_items = []
        item_to_variant = {}
        
        for product_id, variants in variants_data.items():
            for variant in variants:
                inv_item_id = variant.get('inventory_item_id')
                if inv_item_id:
                    inventory_items.append(inv_item_id)
                    item_to_variant[inv_item_id] = variant['id']
        
        if not inventory_items:
            st.warning("⚠️ No inventory items found - variants may not have inventory_item_id")
            return variant_inventory_levels
        
        st.info(f"📦 Found {len(inventory_items)} inventory items to fetch")
        
        # Same batching logic as basic.txt
        batch_size = 40
        
        def fetch_inventory_batch(batch_items: List[int], batch_num: int) -> Dict[int, Dict[int, int]]:
            """Same batch logic as basic.txt"""
            batch_results = {}
            
            try:
                # Same request format as basic.txt
                item_ids = ','.join(map(str, batch_items))
                location_ids = ','.join(map(str, self.location_ids))
                
                url = f'{self.base_url}/inventory_levels.json'
                params = {
                    'inventory_item_ids': item_ids,
                    'location_ids': location_ids,
                    'limit': 250
                }
                
                cache_key = f"inventory_batch_{batch_num}"
                data = self._make_request_fast(f"{url}?{urlencode(params)}", cache_key)
                
                if data and 'inventory_levels' in data:
                    st.info(f"📦 Batch {batch_num}: Got {len(data['inventory_levels'])} inventory records")
                    
                    for item in data['inventory_levels']:
                        inv_item_id = item.get('inventory_item_id')
                        location_id = item.get('location_id')
                        available = item.get('available', 0) or 0
                        
                        variant_id = item_to_variant.get(inv_item_id)
                        if variant_id:
                            if variant_id not in batch_results:
                                batch_results[variant_id] = {}
                            batch_results[variant_id][location_id] = available
                else:
                    st.warning(f"⚠️ Batch {batch_num}: No inventory data returned")
                
                return batch_results
                
            except Exception as e:
                logger.error(f"Inventory batch {batch_num} failed: {e}")
                st.error(f"❌ Batch {batch_num} failed: {e}")
                return {}
        
        # Same parallel processing as basic.txt
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            
            for i in range(0, len(inventory_items), batch_size):
                batch = inventory_items[i:i + batch_size]
                batch_num = i // batch_size
                future = executor.submit(fetch_inventory_batch, batch, batch_num)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    batch_results = future.result(timeout=20)
                    
                    # Merge results
                    for variant_id, location_data in batch_results.items():
                        if variant_id not in variant_inventory_levels:
                            variant_inventory_levels[variant_id] = {}
                        variant_inventory_levels[variant_id].update(location_data)
                        
                except Exception as e:
                    logger.error(f"Inventory batch failed: {e}")
        
        st.success(f"⚡ Fetched inventory for {len(variant_inventory_levels)} variants")
        return variant_inventory_levels


