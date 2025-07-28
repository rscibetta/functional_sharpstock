#The DatabaseManager handles all database operations - user authentication, profile storage, caching, and encryption. 

"""Database management for user profiles and caching"""
import streamlit as st
import sqlite3
import os
import hashlib
import pickle
import base64
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet

try:
    import supabase
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

from models.data_models import UserProfile, BrandLeadTime, CachedOrderData

# DATABASE MANAGER CLASS - From attempt1.txt
class DatabaseManager:
    """Manages all database operations for user profiles and caching"""
    
    def __init__(self):
        # For production: Use Supabase
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if self.supabase_url and self.supabase_key and SUPABASE_AVAILABLE:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            self.use_supabase = True
            st.info("🌐 Connected to Supabase (Production Mode)")
        else:
            # Fallback to SQLite for local development
            self.use_supabase = False
            self._init_sqlite()
            st.info("💾 Using SQLite (Development Mode)")
        
        # Initialize encryption with persistent key
        self._init_encryption()
    
    def _init_encryption(self):
        """Initialize encryption with persistent key storage"""
        # Try to get key from environment first
        encryption_key = os.getenv("ENCRYPTION_KEY")
        
        if encryption_key:
            # Use provided key from environment
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()
            self.fernet = Fernet(encryption_key)
            st.info("🔐 Using encryption key from environment")
            return
        
        # For local development, store key in a file
        key_file = "encryption_key.key"
        
        try:
            # Try to load existing key
            if os.path.exists(key_file):
                with open(key_file, "rb") as f:
                    encryption_key = f.read()
                self.fernet = Fernet(encryption_key)
                st.info("🔐 Loaded existing encryption key")
            else:
                # Generate new key and save it
                encryption_key = Fernet.generate_key()
                with open(key_file, "wb") as f:
                    f.write(encryption_key)
                self.fernet = Fernet(encryption_key)
                st.warning("🔐 Generated new encryption key - stored in encryption_key.key")
                
        except Exception as e:
            # Fallback: use session-based key (will be lost on restart)
            encryption_key = Fernet.generate_key()
            self.fernet = Fernet(encryption_key)
            st.error(f"❌ Encryption key error: {e}")
            st.warning("⚠️ Using temporary encryption key - tokens will be lost on restart")
    
    def _init_sqlite(self):
        """Initialize SQLite database for local development"""
        self.db_path = "shopify_intelligence.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                shop_name TEXT NOT NULL,
                encrypted_api_token TEXT NOT NULL,
                location_config TEXT NOT NULL,
                default_lead_time INTEGER DEFAULT 14,
                last_cache_update TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brand_lead_times (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                brand_name TEXT NOT NULL,
                lead_time_days INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, brand_name),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cached_orders (
                cache_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                order_data BLOB NOT NULL,
                data_start_date DATE NOT NULL,
                data_end_date DATE NOT NULL,
                cache_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cache_period_years INTEGER DEFAULT 2,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # MIGRATION: Add cache_period_years column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE cached_orders ADD COLUMN cache_period_years INTEGER DEFAULT 2")
            conn.commit()
            print("✅ Migration: Added cache_period_years column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("✅ Migration: cache_period_years column already exists")
            else:
                print(f"⚠️ Migration warning: {e}")
        
        conn.commit()
        conn.close()
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt API token for secure storage"""
        try:
            return self.fernet.encrypt(token.encode()).decode()
        except Exception as e:
            st.error(f"❌ Failed to encrypt token: {e}")
            raise
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt API token for use"""
        try:
            return self.fernet.decrypt(encrypted_token.encode()).decode()
        except Exception as e:
            st.error(f"❌ Failed to decrypt token: {e}")
            st.info("💡 This usually means the encryption key has changed. Please re-enter your API token.")
            raise
    
    def create_user(self, username: str, email: str, password: str) -> str:
        """Create new user account"""
        user_id = hashlib.sha256(f"{username}{email}{datetime.now()}".encode()).hexdigest()[:16]
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if self.use_supabase:
            # Use Supabase authentication
            try:
                response = self.supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "username": username,
                            "user_id": user_id
                        }
                    }
                })
                return user_id
            except Exception as e:
                raise Exception(f"Failed to create user: {str(e)}")
        else:
            # SQLite fallback
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (user_id, username, email, password_hash) VALUES (?, ?, ?, ?)",
                    (user_id, username, email, password_hash)
                )
                conn.commit()
                return user_id
            except sqlite3.IntegrityError:
                raise Exception("Username or email already exists")
            finally:
                conn.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return user_id"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if self.use_supabase:
            # Use Supabase authentication
            try:
                response = self.supabase.auth.sign_in_with_password({
                    "email": username,  # Assuming username is email
                    "password": password
                })
                return response.user.user_metadata.get("user_id")
            except:
                return None
        else:
            # SQLite fallback
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id FROM users WHERE (username = ? OR email = ?) AND password_hash = ?",
                (username, username, password_hash)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
    
    def save_user_profile(self, profile: UserProfile) -> bool:
        """Save user profile to database"""
        if self.use_supabase:
            try:
                self.supabase.table("user_profiles").upsert({
                    "user_id": profile.user_id,
                    "shop_name": profile.shop_name,
                    "encrypted_api_token": profile.encrypted_api_token,
                    "location_config": json.dumps(profile.location_config),
                    "default_lead_time": profile.default_lead_time,
                    "last_cache_update": profile.last_cache_update.isoformat() if profile.last_cache_update else None
                }).execute()
                return True
            except Exception as e:
                st.error(f"Failed to save profile: {str(e)}")
                return False
        else:
            # SQLite fallback
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO user_profiles 
                    (user_id, shop_name, encrypted_api_token, location_config, default_lead_time, last_cache_update)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    profile.user_id,
                    profile.shop_name,
                    profile.encrypted_api_token,
                    json.dumps(profile.location_config),
                    profile.default_lead_time,
                    profile.last_cache_update
                ))
                conn.commit()
                return True
            except Exception as e:
                st.error(f"Failed to save profile: {str(e)}")
                return False
            finally:
                conn.close()
    
    def load_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Load user profile from database"""
        if self.use_supabase:
            try:
                response = self.supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
                if response.data:
                    data = response.data[0]
                    user_response = self.supabase.table("users").select("username, email").eq("user_id", user_id).execute()
                    user_data = user_response.data[0] if user_response.data else {}
                    
                    return UserProfile(
                        user_id=data["user_id"],
                        username=user_data.get("username", ""),
                        email=user_data.get("email", ""),
                        shop_name=data["shop_name"],
                        encrypted_api_token=data["encrypted_api_token"],
                        location_config=json.loads(data["location_config"]),
                        default_lead_time=data["default_lead_time"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        last_cache_update=datetime.fromisoformat(data["last_cache_update"]) if data["last_cache_update"] else None
                    )
                return None
            except Exception as e:
                st.error(f"Failed to load profile: {str(e)}")
                return None
        else:
            # SQLite fallback
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.username, u.email, p.shop_name, p.encrypted_api_token, 
                       p.location_config, p.default_lead_time, p.last_cache_update, u.created_at
                FROM users u
                JOIN user_profiles p ON u.user_id = p.user_id
                WHERE u.user_id = ?
            """, (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return UserProfile(
                    user_id=user_id,
                    username=result[0],
                    email=result[1],
                    shop_name=result[2],
                    encrypted_api_token=result[3],
                    location_config=json.loads(result[4]),
                    default_lead_time=result[5],
                    created_at=datetime.fromisoformat(result[7]),
                    last_cache_update=datetime.fromisoformat(result[6]) if result[6] else None
                )
            return None
    
    def save_brand_lead_time(self, user_id: str, brand_name: str, lead_time_days: int) -> bool:
        """Save brand-specific lead time"""
        if self.use_supabase:
            try:
                self.supabase.table("brand_lead_times").upsert({
                    "user_id": user_id,
                    "brand_name": brand_name,
                    "lead_time_days": lead_time_days
                }).execute()
                return True
            except Exception as e:
                st.error(f"Failed to save brand lead time: {str(e)}")
                return False
        else:
            # SQLite fallback
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO brand_lead_times (user_id, brand_name, lead_time_days)
                    VALUES (?, ?, ?)
                """, (user_id, brand_name, lead_time_days))
                conn.commit()
                return True
            except Exception as e:
                st.error(f"Failed to save brand lead time: {str(e)}")
                return False
            finally:
                conn.close()
    
    def get_brand_lead_times(self, user_id: str) -> Dict[str, int]:
        """Get all brand lead times for user"""
        if self.use_supabase:
            try:
                response = self.supabase.table("brand_lead_times").select("brand_name, lead_time_days").eq("user_id", user_id).execute()
                return {item["brand_name"]: item["lead_time_days"] for item in response.data}
            except Exception as e:
                st.error(f"Failed to load brand lead times: {str(e)}")
                return {}
        else:
            # SQLite fallback
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT brand_name, lead_time_days FROM brand_lead_times WHERE user_id = ?", (user_id,))
            results = cursor.fetchall()
            conn.close()
            return {brand: lead_time for brand, lead_time in results}
    
    def cache_historical_data(self, user_id: str, orders_df: pd.DataFrame, start_date: datetime, end_date: datetime, period_years: int) -> bool:
        """Cache historical order data with period tracking"""
        cache_id = hashlib.sha256(f"{user_id}{start_date}{end_date}{period_years}".encode()).hexdigest()[:16]
        pickled_data = pickle.dumps(orders_df)
        
        if self.use_supabase:
            try:
                # Note: For large data, consider using Supabase Storage instead
                encoded_data = base64.b64encode(pickled_data).decode()
                self.supabase.table("cached_orders").upsert({
                    "cache_id": cache_id,
                    "user_id": user_id,
                    "order_data": encoded_data,
                    "data_start_date": start_date.date().isoformat(),
                    "data_end_date": end_date.date().isoformat(),
                    "cache_period_years": period_years
                }).execute()
                return True
            except Exception as e:
                st.warning(f"Failed to cache data (large dataset): {str(e)}")
                return False
        else:
            # SQLite fallback
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO cached_orders 
                    (cache_id, user_id, order_data, data_start_date, data_end_date, cache_period_years)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (cache_id, user_id, pickled_data, start_date.date(), end_date.date(), period_years))
                conn.commit()
                return True
            except Exception as e:
                st.warning(f"Failed to cache data: {str(e)}")
                return False
            finally:
                conn.close()

    def load_cached_historical_data(self, user_id: str, period_years: int = None) -> Optional[pd.DataFrame]:
        """Load cached historical data for specific period or most recent"""
        if self.use_supabase:
            try:
                query = self.supabase.table("cached_orders").select("*").eq("user_id", user_id)
                if period_years:
                    query = query.eq("cache_period_years", period_years)
                response = query.order("cache_date", desc=True).limit(1).execute()
                
                if response.data:
                    data = response.data[0]
                    pickled_data = base64.b64decode(data["order_data"].encode())
                    return pickle.loads(pickled_data)
                return None
            except Exception as e:
                st.warning(f"Failed to load cached data: {str(e)}")
                return None
        else:
            # SQLite fallback
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if period_years:
                cursor.execute("""
                    SELECT order_data FROM cached_orders 
                    WHERE user_id = ? AND cache_period_years = ?
                    ORDER BY cache_date DESC 
                    LIMIT 1
                """, (user_id, period_years))
            else:
                cursor.execute("""
                    SELECT order_data FROM cached_orders 
                    WHERE user_id = ? 
                    ORDER BY cache_date DESC 
                    LIMIT 1
                """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                try:
                    return pickle.loads(result[0])
                except:
                    return None
            return None

    def get_available_cache_periods(self, user_id: str) -> List[Dict[str, Any]]:
        """Get list of available cached periods for user"""
        if self.use_supabase:
            try:
                response = self.supabase.table("cached_orders").select("cache_period_years, cache_date, data_start_date, data_end_date").eq("user_id", user_id).order("cache_period_years").execute()
                return response.data
            except Exception as e:
                st.warning(f"Failed to load cache info: {str(e)}")
                return []
        else:
            # SQLite fallback
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cache_period_years, cache_date, data_start_date, data_end_date 
                FROM cached_orders 
                WHERE user_id = ? 
                ORDER BY cache_period_years
            """, (user_id,))
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'cache_period_years': row[0],
                    'cache_date': row[1],
                    'data_start_date': row[2],
                    'data_end_date': row[3]
                }
                for row in results
            ]
        
