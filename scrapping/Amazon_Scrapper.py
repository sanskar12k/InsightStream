import logging
import time
from scrapping.Base_Scrapper import BaseScraper
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from scrapping.config import ScraperConfig
from scrapping.Products import Product
from scrapping.Playwright_Driver import PlaywrightDriver as SeleniumDriver
import concurrent.futures
from playwright.sync_api import sync_playwright, TimeoutError
import urllib.parse
from urllib.parse import quote_plus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AmazonScraper(BaseScraper):
    """Amazon scraper with Selenium"""
    
    def __init__(self, proxy_manager=None, captcha_solver=None, api_key: Optional[str] = None):
        super().__init__(proxy_manager, captcha_solver)
        self.api_key = api_key
        self.base_url = "https://www.amazon.in"

    def clean_amazon_url(self, raw_url: str) -> str:
        """
        Cleans and formats Amazon URLs.
        Handles relative paths and extracts true URLs from sponsored ad redirects.
        """
        if not raw_url:
            return ""

        import urllib.parse
        
        try:
            # 1. Handle Sponsored links: Extract actual product URL from redirect payload
            if '/sspa/click' in raw_url:
                parsed_url = urllib.parse.urlparse(raw_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                if 'url' in query_params:
                    # Decode the embedded URL (e.g., %2FGranola... -> /Granola...)
                    raw_url = urllib.parse.unquote(query_params['url'][0])
            
            # 2. Convert relative URLs to absolute URLs
            if raw_url.startswith('/'):
                return urllib.parse.urljoin(self.base_url, raw_url)
            
            return raw_url
            
        except Exception as e:
            logger.debug(f"Error cleaning URL '{raw_url}': {e}")
            return raw_url  # Fallback to the original URL if parsing fails 

    # def scrape_basic_product_details_helper(self, driver, max_products: int = 80) -> Optional[Dict[str, Optional[str]]]:
    #     product_data = []
    #     fields_mapping = {
    #         'title': ['title', 'name'],
    #         'price': ['.a-price-whole'],
    #         'rating': ['rating', 'stars'],
    #         'review_count': ['#averageCustomerReviews_feature_div #acrCustomerReviewText', '.s-underline-text']
    #     }
    #     logger.info("Inside helper basic product details")
    #     product_elements = driver.query_selector_all(By.CSS_SELECTOR, '[data-component-type="s-search-result"]')
    #     length = min(max_products, len(product_elements))
    #     for elem in product_elements[:length]:
    #         try:
    #         # logger.info(f"{elem.text}")
    #             title_elem = elem.find_element(By.CSS_SELECTOR, 'h2 span')
    #             price_elem = elem.find_element(By.CSS_SELECTOR, fields_mapping['price'][0])
    #             title = self._extract_text(title_elem)
    #             cur_price = self._parse_price(self._extract_text(price_elem))
    #             rating = None
    #             review_count = 0
    #             url = "" 

    #             try:
    #                 # rating_elem = elem.find_element(By.CSS_SELECTOR, '[data-cy="reviews-block"] .a-size-small span')
    #                 rating_elem = elem.find_element(By.CSS_SELECTOR, '.a-size-small span')
    #                 rating = self._parse_rating(self._extract_text(rating_elem))
    #             except:
    #                 pass
                
    #             try:
    #                 link_elem = elem.find_element(By.CSS_SELECTOR, '.a-link-normal')
    #                 url = self.clean_amazon_url(link_elem.get_attribute('href'))
    #             except:
    #                 pass
    #             if cur_price and title:
    #                 product_data.append({
    #                     'title': title,
    #                     'cur_price': cur_price,
    #                     'rating': rating,
    #                     'review_count': review_count,
    #                     'url': url
    #                 })
    #         except Exception as e:
    #             logger.debug(f"Error parsing product: {e}")
    #             continue
    #     try:
    #         next_page_elem = driver.query_selector_all(By.CSS_SELECTOR, '.s-pagination-next')[0]

    #         if 'a-disabled' in next_page_elem.get_attribute('class'):
    #             logger.info("No next page available")
    #             return product_data

    #         next_page_url =  self.clean_amazon_url(next_page_elem.get_attribute('href'))

    #         if next_page_url:
    #             logger.info("Next page URL found. Navigating..." + next_page_url)

    #             driver.get(next_page_url)
            
    #         else:
    #             logger.info("Navigating to next page by clicking button"+next_page_url)
    #             driver.execute_script("arguments[0].click();", next_page_url)
    #         time.sleep(1)
    #         driver.wait_for_selector('[data-component-type="s-search-result"]', timeout=10)
    #         product_data.extend(self.scrape_basic_product_details_helper(driver))
    #     except:            
    #         logger.info("No next page found")
    #         pass
    #     return product_data
    
    def scrape_basic_product_details_helper(self, driver, max_products: int = 80) -> List[Dict[str, Optional[str]]]:
        product_data = []
        fields_mapping = {
            'price': ['.a-price-whole']
        }
        
        # Iterative approach instead of recursion
        while len(product_data) < max_products:
            logger.info(f"Scraping basic details. Current count: {len(product_data)}/{max_products}")
            
            try:
                # Wait for products to load on the current page
                driver.wait_for_selector('[data-component-type="s-search-result"]', timeout=self.config.PAGE_LOAD_TIMEOUT)
            except Exception as e:
                logger.warning(f"Timeout waiting for search results: {e}")
                break

            product_elements = driver.query_selector_all( '[data-component-type="s-search-result"]')
            
            # Calculate exactly how many more products we need to hit our max
            remaining_needed = max_products - len(product_data)
            
            # Slice the elements list so we don't process more than we need
            elements_to_process = product_elements[:remaining_needed]
            
            for elem in elements_to_process:
                try:
                    # Using the stricter title selector from our previous fix
                    title_elem = elem.query_selector( 'h2 span')
                    price_elem = elem.query_selector( fields_mapping['price'][0])
                    
                    title = self._extract_text(title_elem)
                    cur_price = self._parse_price(self._extract_text(price_elem))
                    rating = None
                    review_count = 0
                    url = "" 

                    try:
                        rating_elem = elem.query_selector( '.a-size-small span')
                        rating = self._parse_rating(self._extract_text(rating_elem))
                    except:
                        pass
                    
                    try:
                        link_elem = elem.query_selector('.a-link-normal')
                        url = self.clean_amazon_url(link_elem.get_attribute('href'))
                    except:
                        pass
                    if cur_price and title:
                        product_data.append({
                            'title': title,
                            'cur_price': cur_price,
                            'rating': rating,
                            'review_count': review_count,
                            'url': url
                        })
                except Exception as e:
                    logger.debug(f"Error parsing product element: {e}")
                    continue
            
            # Check if we hit our quota after processing the page
            if len(product_data) >= max_products:
                logger.info(f"Target of {max_products} products reached.")
                break
            logger.info(f" product_data len: {len(product_data)}")
            # --- Pagination Logic ---
            try:
                next_page_elements = driver.query_selector_all('.s-pagination-next')
                
                if not next_page_elements:
                    logger.info("No next page button found in DOM.")
                    break
                    
                next_page_elem = next_page_elements[0]

                if 'a-disabled' in next_page_elem.get_attribute('class'):
                    logger.info("Next page button is disabled (last page reached).")
                    break

                next_page_url = self.clean_amazon_url(next_page_elem.get_attribute('href')) 
                # next_page_elem.get_attribute('href')

                if next_page_url:
                    logger.info(f"Navigating to next page: {next_page_url}")
                    driver.get(next_page_url)
                else:
                    logger.info("Navigating to next page by clicking button.")
                    driver.execute_script("arguments[0].click();", next_page_elem)
                
                # Small pause to ensure the browser has time to trigger the navigation event
                time.sleep(2) 
                
            except Exception as e:            
                logger.info(f"Failed to navigate to next page or no more pages: {e}")
                break
                
        # Return exactly the requested amount
        return product_data[:max_products]

    def scrape_basic_product_details(self, driver, search_url: str, attempt:int = 0, max_products: int = 80) -> Dict[str, Optional[str]]:
        driver.wait_for_selector('[data-component-type="s-search-result"]', timeout=self.config.PAGE_LOAD_TIMEOUT)
        product_data = []
        # Check for CAPTCHA
        if "captcha" in driver.page_source.lower():
            logger.warning("CAPTCHA detected")
            if not self._handle_captcha(driver, search_url):
                logger.error("Failed to solve CAPTCHA")
                return product_data
        logger.info(f"Parsing products (attempt {attempt + 1})")
            # Scroll to load lazy content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(1)    
        product_data = self.scrape_basic_product_details_helper(driver, max_products)
        return product_data
    
    def scrape_product_details(self, product: Dict[str, Optional[str]], reviews: bool = True) -> Dict[str, Optional[str]]:
        try:
          # logger.info(f"Product: {product.title}, Price: ₹{product.price}, Rating: {product.rating}, Reviews: {product.review_count}, URL: {product.url}")
            with SeleniumDriver(proxy=None, headless=True) as driver:
                # with self.lock:
                #     logger.info(f"Scraping details for product URL: {product['url']}")
                driver.get(product['url'])
                try:
                    driver.wait_for_selector('#customer-reviews_feature_div', timeout=10)
                    review_summary = driver.query_selector('[data-testid="overall-summary"]')
                    product['review_summary'] = self._extract_text(review_summary)
                except Exception as e:
                    logger.error(f"Error loading product page or extracting review summary: {e}")
                    product['review_summary'] = None   
                try:
                    if reviews:
                        # with self.lock:
                        #     logger.info("Extracting reviews list")
                        reviews_list = driver.query_selector_all('[data-hook="review"]')
                        for review in reviews_list:
                            review_text = ' '.join(self._extract_text(review.query_selector('[data-hook="review-collapsed"]')).split())
                            if 'reviews' not in product:
                                product['reviews'] = []
                            product['reviews'].append(review_text)
                    else:
                        product['reviews'] = []
                except Exception as e:
                    logger.error(f"Error extracting reviews list: {e}")
                try:   
                    # with self.lock:
                    #     logger.info("Extracting product details from table")
                    details = self.extract_product_details_robust(driver)
                    product['brand'] = details['brand']  # Use table brand if available
                    product['weight'] = details['weight']
                    product['net_quantity'] = details['net_quantity']
                    product['form'] = details['form']
                    product['manufacturer'] = details['manufacturer']
                    product['ingredient_type'] = details['ingredient_type']
                    product['dimension'] = details['dimension']
                    product['country_of_origin'] = details['country_of_origin']
                    product['review_count'] = details['review_count']
                    product['mrp'] = details['mrp']              
                except Exception as e:
                    with self.lock:
                        logger.debug(f"Error extracting product details: {e}")

                with self.lock:
                    logger.debug(f"Extracted details for product: {product['title'][:30]}")

        except Exception as e:
            with self.lock:
                logger.debug(f"Error logging product details: {e}")
        return product

    
    def extract_product_details_robust(self, driver) -> Dict[str, Optional[str]]:
        """Extract product details from Amazon's new UI using Detail Bullets list"""
        details = {
            'brand': None,
            'weight': None,
            'net_quantity': None,
            'form': None,
            'manufacturer': None,
            'ingredient_type': None,
            'dimension': None,
            'country_of_origin': None,
            'price_per_unit': None,
            'review_count': None,
            'mrp': None,
        }
        
        # Field mapping - UPDATED with more precise patterns
        field_mapping = {
            'brand': ['brand', 'brand name'],
            'manufacturer': ['manufacturer', 'mfr', 'made by', 'importer'],
            'weight': ['item weight', 'net weight'],  # More specific
            'net_quantity': ['net quantity', 'net content quantity', 'unit count'],  # More specific
            'dimension': ['product dimensions', 'item dimensions', 'package dimensions'],
            'form': ['form', 'item form', 'product form'],
            'ingredient_type': ['ingredient type', 'diet type', 'vegetarian'],
            'country_of_origin': ['country of origin', 'country/region of origin'],  # Added variant
        }

        try:

            # === EXTRACT FROM DETAIL BULLETS UL LIST ===
            brand_from_snapshot = self.extract_brand_name(driver)
            if brand_from_snapshot:
                details['brand'] = brand_from_snapshot

            self.extract_from_detail_bullets_list(driver, field_mapping, details)
            if details['weight']:
                details['weight'] = self._normalize_weight_to_grams(details['weight'])
        

            # === REVIEW COUNT ===
            try:
                review_elem = driver.query_selector('#averageCustomerReviews_feature_div #acrCustomerReviewText')
                if review_elem:
                    details['review_count'] = str(self._parse_review_count(review_elem.text))
            except Exception as e:
                logger.debug(f"Review count not found: {e}")
            
            # === MRP ===
            try:
                id_elem = driver.query_selector("#apex_desktop")
                mrp_elem = id_elem.query_selector(".a-spacing-small.aok-align-center .aok-relative .a-text-price span[aria-hidden='true']")
                if mrp_elem:
                    details['mrp'] = str(self._parse_price(mrp_elem.get_attribute("textContent").strip()))
                    # logger.info(f"Found mrp: {details['mrp']}")
            except Exception as e:
                logger.debug(f"MRP not found: {e}")

            # === CLEAN UP VALUES ===
            for key in details:
                if details[key]:
                    details[key] = details[key].replace('\u200e', '').replace('\u200f', '').strip()
            
            found_count = sum(1 for v in details.values() if v)
            # logger.info(f"✓ Extracted product details: {found_count}/{len(details)} fields found")
            
            return details
            
        except Exception as e:
            logger.warning(f"Could not extract product details: {e}")
            return details


    def extract_from_detail_bullets_list(self, driver, field_mapping, details):
        """Extract product details from the Detail Bullets UL list under 'Product details' heading"""
        
        # logger.info("Extracting from Detail Bullets list...")
        
        # Try multiple selectors for the UL element
        ul_selectors = [
            '#detailBullets_feature_div ul.detail-bullet-list',
            '#detailBullets_feature_div ul.a-unordered-list.a-nostyle.a-vertical.a-spacing-none.detail-bullet-list',
            '#detailBullets_feature_div ul.a-unordered-list',
            '#detailBulletsWrapper_feature_div ul',
        ]
        
        ul_element = None
        
        for selector in ul_selectors:
            try:
                ul_element = driver.query_selector(selector)
                if ul_element:
                    # logger.info(f"✓ Found Detail Bullets UL with selector: {selector}")
                    break
            except:
                continue
        
        if not ul_element:
            logger.warning("Detail bullets UL not found with any selector")
            return
        
        # Get all <li> items
        li_items = ul_element.query_selector_all('li')
        
        for idx, li in enumerate(li_items, 1):
            try:
                # Get the main span with class "a-list-item"
                list_item_span = li.query_selector('span.a-list-item')
                
                # Get all child spans
                spans = list_item_span.query_selector_all('span')
                
                if len(spans) < 1:
                    logger.debug(f"Item {idx}: Skipping - no spans found")
                    continue
                
                # Extract full text first
                full_text = self._extract_text(list_item_span).strip()
                
                # Try to find the bold span (label)
                label = None
                value = None
                
                try:
                    # Look for bold span specifically
                    bold_span = list_item_span.query_selector('span.a-text-bold')
                    label = self._extract_text(bold_span).strip()
                    
                    # Get value by removing label from full text
                    label_text = self._extract_text(bold_span).strip()
                    value = full_text.replace(label_text, '', 1).strip()
                    
                except:
                    # Fallback: try to split by common separators
                    if ':' in full_text:
                        parts = full_text.split(':', 1)
                        if len(parts) == 2:
                            label = parts[0].strip()
                            value = parts[1].strip()
                    elif '\u200f' in full_text:  # RTL mark
                        parts = full_text.split('\u200f', 1)
                        if len(parts) == 2:
                            label = parts[0].strip()
                            value = parts[1].strip()
                
                if not label or not value:
                    logger.debug(f"Item {idx}: Could not extract label/value from: {full_text[:80]}")
                    continue
                
                # Clean up separators and hidden characters
                label = label.rstrip(':').rstrip('-').rstrip('\u200e').rstrip('\u200f').strip()
                value = value.lstrip(':').lstrip('-').lstrip('\u200e').lstrip('\u200f').strip()
                
                if not value or len(value) < 1:
                    logger.debug(f"Item {idx}: Skipping '{label}' - no value")
                    continue
                
                # Match against field mapping and store
                self.match_and_store_field(label, value, field_mapping, details)
                
            except Exception as e:
                logger.debug(f"Item {idx}: Error processing - {e}")
                continue
        
        # logger.info("✓ Finished extracting from Detail Bullets list")

    def _normalize_weight_to_grams(self, weight_str: str) -> Optional[str]:
        """
        Convert weight string to grams (numeric value only, no unit)
        
        Examples:
            "95 g" -> "95"
            "1.5 kg" -> "1500"
            "500 Grams" -> "500"
            "2.5 Kilograms" -> "2500"
            "750 mg" -> "0.75"
        """
        import re
    
        if not weight_str:
            return None
        
        try:
            # Remove commas and extra whitespace
            weight_str = weight_str.replace(',', '').strip()
            
            # Extract number and unit using regex
            # Pattern matches: "95 g", "1.5kg", "500 Grams", etc.
            pattern = r'([\d.]+)\s*(g|gram|grams|kg|kilogram|kilograms|mg|milligram|milligrams|oz|ounce|ounces|lb|pound|pounds)'
            match = re.search(pattern, weight_str, re.IGNORECASE)
            
            if not match:
                logger.warning(f"Could not parse weight: {weight_str}")
                return None
            
            value = float(match.group(1))
            unit = match.group(2).lower()
            print(f"Parsed weight: {value} {unit}")
            # Convert to grams
            if unit in ['g', 'gram', 'grams']:
                grams = value
            elif unit in ['kg', 'kilogram', 'kilograms']:
                grams = value * 1000.0
            elif unit in ['mg', 'milligram', 'milligrams']:
                grams = value / 1000.0
            elif unit in ['oz', 'ounce', 'ounces']:
                grams = value * 28.3495
            elif unit in ['lb', 'pound', 'pounds']:
                grams = value * 453.592
            else:
                logger.warning(f"Unknown weight unit: {unit}")
                return None
            
            # Return as string without unit, rounded to 2 decimal places if needed
            if grams == int(grams):
                result = str(int(grams))
            else:
                result = f"{grams:.2f}"
            
            # logger.info(f"Normalized weight: '{weight_str}' -> '{result}' grams")
            return result
            
        except Exception as e:
            logger.warning(f"Error normalizing weight '{weight_str}': {e}")
            return None


    def match_and_store_field(self, label, value, field_mapping, details):
        """Match a label-value pair against field mapping and store if matched"""
        
        label_lower = label.lower().strip()
        
        # Priority matching: exact match first, then partial match
        # This prevents "Item Weight" from matching both 'weight' and 'net_quantity'
        
        matched = False
        
        for field, possible_headers in field_mapping.items():
            for header in possible_headers:
                # Exact match (after lowercasing)
                if label_lower == header.lower():
                    if not details[field]:
                        details[field] = value
                        # logger.info(f"  ✓ EXACT match field '{field}': {value}")
                        return True
        
        # If no exact match, try partial match
        for field, possible_headers in field_mapping.items():
            for header in possible_headers:
                # Partial match
                if header.lower() in label_lower:
                    if not details[field]:
                        details[field] = value
                        # logger.info(f"  ✓ PARTIAL match field '{field}': {value}")
                        return True
        
        # Log unmatched fields for debugging
        logger.debug(f"  ✗ No match for label: '{label}'")
        return False
    
    def extract_brand_from_snapshot(self, driver) -> Optional[str]:
        """Extract brand name from the brand snapshot section"""
        
        logger.info("Extracting brand from brand snapshot...")
        
        # Multiple selectors to find the brand name
        brand_selectors = [
            # Main brand snapshot selector (from your screenshot)
            'div#brandSnapshot_feature_div brand-snapshot-title-container p'
            'div.a-section.brand-snapshot-flex-row p span.a-size-medium.a-text-bold',
            
            # Alternative selectors
            'div.brand-snapshot-card-content span.a-size-medium.a-text-bold',
            '.a-cardui-body.brand-snapshot-card-container span.a-text-bold',
            
            # Generic brand snapshot container
            'div[class*="brand-snapshot"] span.a-size-medium.a-text-bold',
            
            # Fallback: any bold text in brand snapshot section
            'div.a-section.brand-snapshot-flex-row span.a-text-bold',
        ]
        
        for selector in brand_selectors:
            try:
                brand_element = driver.query_selector(selector)
                if brand_element:
                    brand_name = self._extract_text(brand_element).strip()
                    
                    # Filter out common non-brand text
                    if brand_name and brand_name.lower() not in ['visit', 'store', 'brand', 'flex']:
                        # logger.info(f"✓ Found brand from snapshot: {brand_name}")
                        return brand_name
                        
            except Exception as e:
                logger.debug(f"Brand selector '{selector}' failed: {e}")
                continue
        
        # Fallback: Try to find by role="heading" and aria-level="2"
        try:
            heading_element = driver.query_selector(
                'div[class*="brand-snapshot"] div[role="heading"][aria-level="2"] span.a-text-bold'
            )
            if heading_element:
                brand_name = self._extract_text(heading_element).strip()
                if brand_name:
                    # logger.info(f"✓ Found brand from heading: {brand_name}")
                    return brand_name
        except:
            pass
        
        # Another fallback: Look for the specific structure from your screenshot
        try:
            # Structure: div.brand-snapshot-flex-row > div.a-section > p > span
            container = driver.query_selector('div.brand-snapshot-flex-row')
            if container:
                # Find all bold spans within
                bold_spans = container.query_selector_all('span.a-text-bold')
                for span in bold_spans:
                    text = self._extract_text(span).strip()
                    # The brand name is usually the first substantial bold text
                    if text and len(text) > 1 and text.lower() not in ['visit', 'store', 'flex']:
                        # logger.info(f"✓ Found brand from container: {text}")
                        return text
        except:
            pass
        
        logger.info("Brand not found in snapshot section")
        return None
    
    def extract_brand_from_item_details(self, driver) -> Optional[str]:
        """
        Extract brand name specifically from the Item Details accordion table
        Structure: #voyagerAccordian_feature_div > table.a-keyvalue > tbody > tr > th + td
        """
        import time
        
        # logger.info("Extracting brand from Item Details accordion table...")
        
        # First, expand the accordion if it's collapsed
        try:
            accordion_button = driver.query_selector(
                '#item_details[data-expanded="false"]'
            )
            
            if accordion_button and accordion_button.is_displayed():
                # logger.info("Item Details accordion is collapsed, expanding...")
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    accordion_button
                )
                driver.execute_script("arguments[0].click();", accordion_button)
                time.sleep(0.5)
                # logger.info("✓ Expanded Item Details accordion")
                
        except Exception as e:
            logger.debug(f"Accordion already expanded or not found: {e}")
        
        # Extract brand from the table structure
        table_selectors = [
            '#voyagerAccordian_feature_div table.a-keyvalue.voyager-ns-desktop-table',
            '#voyagerAccordian_feature_div table.a-keyvalue',
            '#item_details',
        ]
        
        for table_selector in table_selectors:
            try:
                table = driver.query_selector(table_selector)
                if not table:
                    continue
                    
                # logger.info(f"✓ Found Item Details table with selector: {table_selector}")
                
                # Get all rows in the table
                rows = table.query_selector_all('tr')
                # logger.info(f"Processing {len(rows)} rows from Item Details table...")
                
                for idx, row in enumerate(rows, 1):
                    try:
                        # Get th (label) and td (value)
                        th = row.query_selector('th')
                        td = row.query_selector( 'td')
                        
                        # Extract text
                        label = self._extract_text(th).lower().strip()
                        value = self._extract_text(td).strip()
                        
                        # Check if this is the Brand Name field
                        if label.lower() in ['brand name', 'brand']:
                            # logger.info(f"✓ Found brand from Item Details table: {value}")
                            return value
                            
                    except Exception as e:
                        logger.debug(f"Row {idx}: Could not process - {e}")
                        continue
                
                # If we processed the table but didn't find brand, break
                break
                        
            except Exception as e:
                logger.debug(f"Could not process table with selector {table_selector}: {e}")
                continue
        
        # logger.info("Brand not found in Item Details accordion table")
        return None

    def extract_brand_name(self, driver) -> Optional[str]:
        """
        Extract brand name from Amazon product page
        Priority order: Item Details table -> brand byline -> brand snapshot -> product title
        """
        import time
        
        # logger.info("Extracting brand name...")
        
        # ========================================
        # PRIORITY 1: Item Details Accordion Table (Most Accurate)
        # ========================================
        brand_from_item_details = self.extract_brand_from_item_details(driver)
        if brand_from_item_details:
            return brand_from_item_details
        
        # ========================================
        # PRIORITY 2: Brand Byline
        # ========================================
        brand_byline_selectors = [
            '#bylineInfo',  # Main brand byline
            'a#bylineInfo',
            '#brand',
        ]
        
        for selector in brand_byline_selectors:
            try:
                brand_element = driver.query_selector(selector)
                if brand_element:
                    brand_text = self._extract_text(brand_element).strip()
                    
                    # Clean up common prefixes
                    brand_text = brand_text.replace('Visit the ', '').replace(' Store', '').replace('Brand: ', '').strip()
                    
                    if brand_text and len(brand_text) > 0:
                        # logger.info(f"✓ Found brand from byline: {brand_text}")
                        return brand_text
                        
            except Exception as e:
                logger.debug(f"Brand byline selector '{selector}' failed: {e}")
                continue
        
        # ========================================
        # PRIORITY 3: Brand Snapshot Section
        # ========================================  
        brand_snapshot_selectors = [
            'div.brand-snapshot-flex-row p span.a-size-medium.a-text-bold',
            'div.brand-snapshot-card-content span.a-size-medium.a-text-bold',
        ]
        
        for selector in brand_snapshot_selectors:
            try:
                # Playwright automatically handles the CSS selector string natively
                brand_element = driver.query_selector(selector)
                
                if brand_element:
                    brand_name = self._extract_text(brand_element).strip()

                    # Filter out non-brand text
                    if brand_name and brand_name.lower() not in ['visit', 'store', 'brand', 'flex', '']:
                        # logger.info(f"✓ Found brand from snapshot: {brand_name}")
                        return brand_name
                        
            except Exception as e:
                logger.debug(f"Brand snapshot selector '{selector}' failed: {e}")
                continue
        # ========================================
        # PRIORITY 4: Product Title (Extract First Word/Brand)
        # ========================================
        try:
            title_element = driver.query_selector( '#productTitle')
            if title_element:
                title_text = self._extract_text(title_element).strip()
                
                # Brand is usually the first word/phrase in the title
                # Extract first 1-3 words before comma or hyphen
                if ',' in title_text:
                    potential_brand = title_text.split(',')[0].strip()
                elif ' - ' in title_text:
                    potential_brand = title_text.split(' - ')[0].strip()
                else:
                    # Take first 1-2 words
                    words = title_text.split()
                    if len(words) >= 2:
                        potential_brand = ' '.join(words[:2])
                    else:
                        potential_brand = words[0] if words else None
                
                if potential_brand and len(potential_brand) > 1:
                    # logger.info(f"✓ Found potential brand from title: {potential_brand}")
                    return potential_brand
                    
        except Exception as e:
            logger.debug(f"Could not extract brand from title: {e}")
        
        logger.warning("Could not find brand name from any source")
        return None

    def scrape(self, product_name: str, category: Optional[str] = None, max_products: int = 80, deep_details: bool = False, reviews: bool = True) -> List[Product]: # type: ignore
        """Scrape Amazon products using Selenium"""
        products = []
        product_data = []
        detailed_prod = []
        logger.info("Starting scrapping")
        search_url = f"{self.base_url}/s?k={quote_plus(product_name)}"

        if category:
            search_url += f"&i={quote_plus(category)}"
        
        for attempt in range(self.config.MAX_RETRIES):
            proxy = self.proxy_manager.get_proxy() if self.proxy_manager else None
            proxy_str = proxy['http'].replace('http://', '') if proxy else None
            
            try:
                with SeleniumDriver(proxy=proxy_str, headless=True) as driver:
                    logger.info(f"Loading Amazon search page (attempt {attempt + 1})")
                    driver.get(search_url)

                    # Anti-detection: Simulate human behavior with scrolling
                    import random
                    time.sleep(random.uniform(1, 2))
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
                    time.sleep(random.uniform(0.5, 1))
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(random.uniform(0.5, 1))

                    # pick basic info of product
                    product_data = self.scrape_basic_product_details(driver, search_url, attempt, max_products)
                if deep_details and product_data:
                    # go to prod url and get more details
                    with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_detail_workers) as executor:
                    # Submit all detail page fetching tasks
                        future_to_data = {
                            executor.submit(self.scrape_product_details, data, reviews=reviews): data
                            for data in product_data
                        }
                        for future in concurrent.futures.as_completed(future_to_data):
                            data = future_to_data[future]
                            try:
                                detailed_data = future.result()
                                if detailed_data:
                                    detailed_prod.append(detailed_data)
                            except Exception as e:
                                logger.error(f"Error fetching product details: {e}")
                else :
                    detailed_prod = product_data 

                if detailed_prod:
                    logger.info(f"products len {len(detailed_prod)}")
                    for product in detailed_prod:
                        product_object = Product(
                            brand=product.get('brand', None),
                            name=product.get('title', 'Unknown Product'),
                            cur_price=product['cur_price'],
                            mrp=product.get('mrp', None),
                            weight=product.get('weight', None),
                            net_quantity=product.get('net_quantity', None),
                            form=product.get('form', None),
                            manufacturer=product.get('manufacturer', None),
                            ingredient_type=product.get('ingredient_type', None),
                            dimension=product.get('dimension', None),
                            country_of_origin=product.get('country_of_origin', None),
                            rating=product.get('rating', None),
                            review_count=product['review_count'],
                            url=product.get('url', ''),
                            review_summary=product.get('review_summary', None),
                            platform="Amazon",
                            reviews=product.get('reviews', [])
                        )
                        products.append(product_object)

                    logger.info(f"Successfully scraped {len(products)} products from Amazon")
                    return products
                    
            except TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if proxy_str and self.proxy_manager:
                    self.proxy_manager.mark_failed(proxy_str)
                
            except Exception as e:
                logger.error(f"Error scraping Amazon: {e}")
                if proxy_str and self.proxy_manager:
                    self.proxy_manager.mark_failed(proxy_str)
            
            if attempt < self.config.MAX_RETRIES - 1:
                delay = self.config.RETRY_DELAY * (2 ** attempt)
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
        
        logger.error("Failed to scrape Amazon after all attempts")
        return products
