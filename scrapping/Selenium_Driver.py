
import logging
import random
import os
from typing import List, Dict, Optional
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from scrapping.Base_Scrapper import ScraperConfig
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium import webdriver

try:
    from selenium_stealth import stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class SeleniumDriver:
    """Manages Selenium WebDriver with anti-detection"""
    
    def __init__(self, proxy: Optional[str] = None, headless: bool = True):
        self.proxy = proxy
        self.headless = headless
        self.driver = None
    
    def __enter__(self):
        self.driver = self._create_driver()
        return self.driver
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
    
    def _create_driver(self):
        """Create Chrome driver with anti-detection"""
        try:
            options = Options()

            # Set Chrome binary location for production environments
            chrome_bin = os.getenv('CHROME_BIN', '/usr/bin/chromium')
            if os.path.exists(chrome_bin):
                options.binary_location = chrome_bin
                logger.info(f"Using Chrome binary at: {chrome_bin}")

            if self.headless:
                options.add_argument('--headless=new')

            # Anti-detection measures
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-infobars')
            options.add_argument(f'user-agent={random.choice(ScraperConfig.USER_AGENTS)}')

            # Exclude automation switches
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            # Proxy configuration
            if self.proxy:
                options.add_argument(f'--proxy-server={self.proxy}')

            # Configure ChromeDriver service
            service = None
            chromedriver_path = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
            if os.path.exists(chromedriver_path):
                service = Service(executable_path=chromedriver_path)
                logger.info(f"Using chromedriver at: {chromedriver_path}")

            # Create driver
            driver = webdriver.Chrome(service=service, options=options)
            
            # Set timeouts
            driver.set_page_load_timeout(ScraperConfig.PAGE_LOAD_TIMEOUT)
            driver.implicitly_wait(ScraperConfig.IMPLICIT_WAIT)
            
            # Execute CDP commands to further mask automation
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": random.choice(ScraperConfig.USER_AGENTS)
            })
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Apply selenium-stealth if available
            if STEALTH_AVAILABLE:
                stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                )
            
            logger.info("Selenium driver created successfully")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to create driver: {e}")
            raise
