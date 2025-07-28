"""
Shopify Intelligence Application Module
This file provides an alternative entry point for the application
"""

# Import the main function from main_interface
from .main_interface import main

# Make main available when importing from app
__all__ = ['main']

# Allow running from this module directly
if __name__ == "__main__":
    main()
