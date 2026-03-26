
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

    def _get_chrome_path(self) -> Optional[str]:
        """Detect Chrome/Chromium binary with multiple fallbacks"""
        possible_paths = [
            os.getenv('CHROME_BIN'),           # Custom env var
            '/usr/bin/chromium',               # Aptfile default
            '/usr/bin/chromium-browser',       # Alternative name
            '/usr/bin/google-chrome',          # Google Chrome
            '/usr/bin/google-chrome-stable',
            '/snap/bin/chromium',              # Snap install
        ]

        for path in possible_paths:
            if path and os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"✓ Found Chrome binary at: {path}")
                return path

        logger.warning("⚠ Chrome binary not found at any known location")
        return None

    def _get_chromedriver_path(self) -> Optional[str]:
        """Detect chromedriver with multiple fallbacks"""
        # Priority 1: Explicit env vars
        for env_var in ['CHROMEDRIVER_PATH', 'SE_CHROMEDRIVER']:
            path = os.getenv(env_var)
            if path and os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"✓ Using chromedriver from {env_var}: {path}")
                return path

        # Priority 2: System locations
        system_paths = [
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver',
        ]

        for path in system_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"✓ Found system chromedriver at: {path}")
                return path

        logger.info("ℹ No system chromedriver found - Selenium will auto-download")
        return None

    def _validate_chrome_setup(self, chrome_path: str) -> bool:
        """Validate Chrome binary can actually run"""
        try:
            import subprocess
            result = subprocess.run(
                [chrome_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"✓ Chrome validation passed: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"✗ Chrome validation failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"✗ Chrome validation error: {e}")
            return False

    def _create_driver(self):
        """Create Chrome driver with comprehensive path detection"""
        try:
            options = Options()

            # Detect and validate Chrome binary
            chrome_path = self._get_chrome_path()
            if chrome_path:
                # Validate it works
                if self._validate_chrome_setup(chrome_path):
                    options.binary_location = chrome_path
                    logger.info(f"✓ Chrome binary configured: {chrome_path}")
                else:
                    logger.error(f"✗ Chrome at {chrome_path} failed validation")
                    raise Exception(f"Chrome binary at {chrome_path} is not functional")
            else:
                logger.error("✗ CRITICAL: No Chrome binary found")
                raise Exception("Chrome binary not found - check Aptfile installation")

            if self.headless:
                options.add_argument('--headless=new')

            # Anti-detection measures
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
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
            chromedriver_path = self._get_chromedriver_path()
            if chromedriver_path:
                service = Service(executable_path=chromedriver_path)
                logger.info(f"✓ Using explicit chromedriver: {chromedriver_path}")
            else:
                # Explicitly create Service() to enable Selenium-Manager auto-download
                # but with Chrome binary already configured, it should work
                service = Service()
                logger.info("ℹ Using Selenium-Manager for chromedriver auto-detection")

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

            logger.info("✓ Selenium driver created successfully")
            return driver

        except Exception as e:
            logger.error(f"✗ Failed to create driver: {e}")
            raise
