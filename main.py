"""
Advanced Shopify Business Intelligence Dashboard
Main Entry Point
"""
import streamlit as st
import logging
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the main application function
from app.main_interface import main

if __name__ == "__main__":
    main()
