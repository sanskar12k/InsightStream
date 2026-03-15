import logging
import time
import requests
from scrapping.config import ScraperConfig 
from typing import List, Dict, Optional
from selenium.webdriver.common.by import By
from abc import ABC, abstractmethod
from scrapping.Products import Product 
import random
from scrapping.Proxy_Manager import ProxyManager
from scrapping.Captcha_Solver import CaptchaSolver
from threading import Lock

try:
    from twocaptcha import TwoCaptcha
    CAPTCHA_AVAILABLE = True
except ImportError:
    CAPTCHA_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("2captcha-python not installed. CAPTCHA solving disabled.")


logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all scrapers"""
    
    def __init__(self, proxy_manager: Optional[ProxyManager] = None,  # type: ignore
                 captcha_solver: Optional[CaptchaSolver] = None, max_detail_workers=8): # type: ignore
        self.session = requests.Session()
        self.config = ScraperConfig()
        self.proxy_manager = proxy_manager
        self.captcha_solver = captcha_solver
        self.max_detail_workers = max_detail_workers
        self.lock = Lock()
    
    def _get_headers(self) -> Dict:
        """Get randomized headers"""
        return {
            'User-Agent': random.choice(self.config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
    
    def _handle_captcha(self, driver, url: str) -> bool:
        """Detect and solve CAPTCHA"""
        try:
            # Check for reCAPTCHA
            recaptcha_frame = driver.find_elements(By.CSS_SELECTOR, 'iframe[src*="recaptcha"]')
            if recaptcha_frame:
                logger.info("reCAPTCHA detected")
                # Extract site key
                site_key = driver.execute_script(
                    "return document.querySelector('[data-sitekey]')?.getAttribute('data-sitekey')"
                )
                if site_key and self.captcha_solver:
                    solution = self.captcha_solver.solve_recaptcha(site_key, url)
                    if solution:
                        # Inject solution
                        driver.execute_script(
                            f'document.getElementById("g-recaptcha-response").innerHTML="{solution}";'
                        )
                        # Submit form or trigger callback
                        driver.execute_script(
                            'if(typeof ___grecaptcha_cfg !== "undefined") { '
                            'Object.values(___grecaptcha_cfg.clients).forEach(c => c.callback && c.callback()); }'
                        )
                        time.sleep(2)
                        return True
            
            # Check for hCaptcha
            hcaptcha_frame = driver.find_elements(By.CSS_SELECTOR, 'iframe[src*="hcaptcha"]')
            if hcaptcha_frame:
                logger.info("hCaptcha detected")
                site_key = driver.execute_script(
                    "return document.querySelector('[data-sitekey]')?.getAttribute('data-sitekey')"
                )
                if site_key and self.captcha_solver:
                    solution = self.captcha_solver.solve_hcaptcha(site_key, url)
                    if solution:
                        driver.execute_script(
                            f'document.querySelector("[name=h-captcha-response]").innerHTML="{solution}";'
                        )
                        time.sleep(2)
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error handling CAPTCHA: {e}")
            return False
    
    def _extract_text(self, element, default: str = "") -> str:
        """Safely extract text"""
        try:
            if hasattr(element, 'text'):  # Selenium element
                return element.text.strip()
            elif hasattr(element, 'get_text'):  # BeautifulSoup element
                return element.get_text(strip=True)
            elif hasattr(element, 'textContent'):
                return element.get_attribute("textContent").strip()
            return default
        except:
            return default
    
    def _parse_price(self, price_str: str) -> Optional[float]:
        """Parse price string to float"""
        try:
            cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
            return float(cleaned) if cleaned else None
        except:
            return None
    
    def _parse_rating(self, rating_str: str) -> Optional[float]:
        """Parse rating string to float"""
        try:
            cleaned = ''.join(c for c in rating_str if c.isdigit() or c == '.')
            rating = float(cleaned)
            return min(rating, 5.0)
        except:
            return None
    
    def _parse_review_count(self, count_str: str) -> int:
        """Parse review count string to int"""
        try:
            cleaned = ''.join(c for c in count_str if c.isdigit())
            return int(cleaned) if cleaned else 0
        except:
            return 0
    
    @abstractmethod
    def scrape(self, product_name: str, category: Optional[str] = None) -> List[Product]:
        """Scrape products - must be implemented by subclasses"""
        pass
