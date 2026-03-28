# config.py
"""Shared configuration and constants"""

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check available libraries
try:
    from twocaptcha import TwoCaptcha
    CAPTCHA_AVAILABLE = True
except ImportError:
    CAPTCHA_AVAILABLE = False
    logger.warning("2captcha-python not installed. CAPTCHA solving disabled.")

try:
    from selenium_stealth import stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas not installed.")


class ScraperConfig:
    """Configuration for scraper behavior"""
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    TIMEOUT = 10
    RATE_LIMIT_DELAY = (1, 2)

    # Auto-detect environment and adjust timeouts
    import os
    if os.getenv('RAILWAY_ENVIRONMENT'):
        PAGE_LOAD_TIMEOUT = 45  # Railway needs longer timeout due to network constraints
        IMPLICIT_WAIT = 15
        logger.info("Railway environment: Using extended timeouts (45s page load)")
    else:
        PAGE_LOAD_TIMEOUT = 20  # Local environment
        IMPLICIT_WAIT = 10
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]


class ScraperMethod:
    """Scraping methods"""
    API = "API"
    SELENIUM = "Selenium"
    REQUESTS = "Requests"