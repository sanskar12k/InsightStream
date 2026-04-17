import logging
import time

from Base_Scrapper import BaseScraper
from typing import List, Optional

from selenium.webdriver.common.by import By
from urllib.parse import quote_plus

import Products
from Playwright_Driver import PlaywrightDriver as Selenium_Driver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlipkartScraper(BaseScraper):
    """Flipkart scraper with Selenium"""
    
    def __init__(self, proxy_manager=None, captcha_solver=None):
        super().__init__(proxy_manager, captcha_solver)
        self.base_url = "https://www.flipkart.com"
    
    def scrape(self, product_name: str, category: Optional[str] = None) -> List[Products]: # type: ignore
        """Scrape Flipkart products using Selenium"""
        products = []
        search_url = f"{self.base_url}/search?q={quote_plus(product_name)}"
        
        for attempt in range(self.config.MAX_RETRIES):
            proxy = self.proxy_manager.get_proxy() if self.proxy_manager else None
            proxy_str = proxy['http'].replace('http://', '') if proxy else None
            
            try:
                with Selenium_Driver(proxy=proxy_str, headless=False) as driver:
                    logger.info(f"Loading Flipkart search page (attempt {attempt + 1})")
                    driver.get(search_url)
                    
                    # Close login popup if appears
                    try:
                        close_btn = driver.wait_for_selector('button._2KpZ6l._2doB4z', timeout=5)
                        if close_btn:
                            close_btn.click()
                    except:
                        pass

                    # Wait for products
                    driver.wait_for_selector('[data-id]', timeout=10)
                    
                    # Check for CAPTCHA
                    if "captcha" in driver.page_source.lower() or "verify" in driver.page_source.lower():
                        logger.warning("CAPTCHA/verification detected")
                        if not self._handle_captcha(driver, search_url):
                            continue
                    
                    # Scroll
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(1.5)
                    
                    # Parse products
                    product_elements = driver.find_elements(By.CSS_SELECTOR, '[data-id]')
                    
                    for elem in product_elements[:3]:
                        try:
                            title_elem = elem.find_element(By.CSS_SELECTOR, 'a[title]')
                            price_elem = elem.find_element(By.CSS_SELECTOR, 'div._30jeq3')
                            
                            title = title_elem.get_attribute('title')
                            price = self._parse_price(self._extract_text(price_elem))
                            
                            rating = None
                            review_count = 0
                            url = ""
                            
                            try:
                                rating_elem = elem.find_element(By.CSS_SELECTOR, 'div._3LWZlK')
                                rating = self._parse_rating(self._extract_text(rating_elem))
                            except:
                                pass
                            
                            try:
                                review_elem = elem.find_element(By.CSS_SELECTOR, 'span._2_R_DZ')
                                review_count = self._parse_review_count(self._extract_text(review_elem))
                            except:
                                pass
                            
                            try:
                                url = title_elem.get_attribute('href')
                            except:
                                pass
                            
                            brand = title.split()[0] if title else "Unknown"
                            
                            if price and title:
                                product = Products(
                                    brand=brand,
                                    name=title,
                                    price=price,
                                    rating=rating,
                                    review_count=review_count,
                                    url=url,
                                    review_summary=None,
                                    platform="Flipkart"
                                )
                                products.append(product)
                        
                        except Exception as e:
                            logger.debug(f"Error parsing product: {e}")
                            continue
                    
                    if products:
                        logger.info(f"Successfully scraped {len(products)} products from Flipkart")
                        return products
                    
            except TimeoutException:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if proxy_str and self.proxy_manager:
                    self.proxy_manager.mark_failed(proxy_str)
                
            except Exception as e:
                logger.error(f"Error scraping Flipkart: {e}")
                if proxy_str and self.proxy_manager:
                    self.proxy_manager.mark_failed(proxy_str)
            
            if attempt < self.config.MAX_RETRIES - 1:
                delay = self.config.RETRY_DELAY * (2 ** attempt)
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
        
        logger.error("Failed to scrape Flipkart after all attempts")
        return products
