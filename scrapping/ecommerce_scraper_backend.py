"""
Advanced E-commerce Product Scraper Backend
Supports Selenium, Proxies, and CAPTCHA solving
"""
"""
Scrapping product name, price, rating, review count
Scrapping product review summary
write down to csv file
Detail of a product
Add pagination
Multi threading
Also add image link
Scrap all review
"""
from typing import List, Dict, Optional
import time
import random
from dataclasses import dataclass
from enum import Enum
import logging
from urllib.parse import urljoin, quote_plus
import json
import pandas as pd
from datetime import datetime
import os
from scrapping.config import PANDAS_AVAILABLE, ScraperConfig, ScraperMethod 
from scrapping.Amazon_Scrapper import AmazonScraper
import scrapping.Captcha_Solver
import scrapping.Proxy_Manager

if PANDAS_AVAILABLE:
    import pandas as pd

logger = logging.getLogger(__name__)

class ScraperMethod(Enum):
    API = "API"
    SELENIUM = "Selenium"
    REQUESTS = "Requests"

class ScraperOrchestrator:
    """Orchestrates multiple scrapers with proxy and CAPTCHA support"""
    
    def __init__(self, 
                 proxy_list: Optional[List[str]] = None,
                 captcha_api_key: Optional[str] = None,
                 amazon_api_key: Optional[str] = None):
        
        proxy_manager = Proxy_Manager(proxy_list) if proxy_list else None
        captcha_solver = Captcha_Solver(captcha_api_key) if captcha_api_key else None
        
        self.scrapers = {
            'amazon': AmazonScraper(proxy_manager, captcha_solver, amazon_api_key)
            # 'flipkart': FlipkartScraper(proxy_manager, captcha_solver),
        }
    
    def scrape_all(self, product_name: str, category: Optional[str] = None, platforms: List[str] = ['amazon', 'flipkart'], max_product: int = 80, deep_details: bool = True,  reviews: bool = True) -> Dict:
        """Scrape all platforms"""
        if not product_name or not product_name.strip():
            raise ValueError("Product name cannot be empty")
        
        results = {}
        
        for platform, scraper in self.scrapers.items():
            logger.info(f"Scraping {platform}...")
            try:
                start_time = datetime.now()
                products = scraper.scrape(product_name, category, max_product, deep_details, reviews)
                results[platform] = {
                    'success': len(products) > 0,
                    'method': ScraperMethod.SELENIUM.value,
                    'products': [p.to_dict() for p in products],
                    'count': len(products)
                }
                logger.info(f"Scraping {platform} completed")
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                print(f"\n✓ Scraping completed in {duration:.2f} seconds")
            except Exception as e:
                logger.error(f"Error scraping {platform}: {e}")
                results[platform] = {
                    'success': False,
                    'error': str(e),
                    'products': []
                }
            
            # Rate limiting between platforms
            # time.sleep(random.uniform(*ScraperConfig.RATE_LIMIT_DELAY))
        return results
    


    def export_to_csv_pandas(self, results: Dict, product: Optional[str] = None,
                            search_id: Optional[str] = None, output_dir: str = 'scrape_results') -> dict:
        """
        Export scraping results to R2 cloud storage

        Args:
            results: Scraping results dict
            product: Product name
            search_id: Search UUID (required for R2 upload)
            output_dir: Legacy parameter, ignored when search_id provided

        Returns:
            Dict with R2 paths: {'products': 'path', 'reviews': 'path', 'filename_structure': 'name'}
            or None if failed
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if not product:
            product = "product"
        product = product.replace(" ", "_").lower()
        filename_structure = product + "_" + timestamp

        # Collect all products
        all_products = []
        for platform, data in results.items():
            if data.get('success') and data.get('products'):
                all_products.extend(data['products'])

        if not all_products:
            logger.warning("No products to export")
            return None

        try:
            # Create DataFrame
            df = pd.DataFrame(all_products)

            # Reorder and rename columns
            column_order = ['platform', 'brand', 'name', 'cur_price', 'mrp', 'rating',
                          'review_count', 'review_summary', 'url', 'weight', 'net_quantity',
                          'form', 'manufacturer', 'ingredient_type', 'dimension', 'country_of_origin']
            product_df = df[column_order].drop_duplicates()

            product_df.columns = ['Platform', 'Brand', 'Product Name', 'Current Price', 'MRP',
                                 'Rating', 'Review Count', 'Review Summary', 'URL', 'Weight',
                                 'Net Quantity', 'Form', 'Manufacturer', 'Ingredient Type',
                                 'Dimension', 'Country of Origin']

            # Truncate long review summaries
            product_df['Review Summary'] = product_df['Review Summary'].apply(
                lambda x: x[:2000] if pd.notna(x) else ''
            )

            # Sort by rating and price
            product_df = product_df.sort_values(['Rating', 'Current Price'], ascending=[False, True])

            # Create review DataFrame
            review_df = df[['platform', 'brand', 'name', 'reviews']].explode('reviews').dropna(subset=['reviews'])

            # Upload to R2 if search_id provided, otherwise fallback to local
            if search_id:
                from backend.storage.r2_storage import get_storage
                storage = get_storage()

                paths = storage.upload_scraping_results(
                    product_df=product_df,
                    review_df=review_df,
                    search_id=search_id,
                    product_name=product,
                    timestamp=timestamp,
                    df_type='pandas'
                )

                paths['filename_structure'] = filename_structure
                logger.info(f"✓ Exported {len(all_products)} products to R2: {paths}")
                return paths
            else:
                # Fallback to local file system (legacy behavior)
                os.makedirs(output_dir, exist_ok=True)
                filename = product + "_" + timestamp + '.csv'
                reviews_filename = product + "_reviews_" + timestamp + '.csv'
                filepath = os.path.join(output_dir, filename)
                review_filepath = os.path.join(output_dir, reviews_filename)

                product_df.to_csv(filepath, index=False, encoding='utf-8')
                review_df.to_csv(review_filepath, index=False, encoding='utf-8')

                logger.info(f"✓ Exported {len(all_products)} products to {filepath}")
                return {
                    'products': filepath,
                    'reviews': review_filepath,
                    'filename_structure': filename_structure
                }

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return None
        
    def get_best_deals(self, results: Dict) -> List[Dict]:
        """Extract best deals across platforms"""
        all_products = []
        
        for platform_data in results.values():
            if platform_data.get('success'):
                all_products.extend(platform_data.get('products', []))
        
        sorted_products = sorted(
            all_products,
            key=lambda x: (-(x.get('rating') or 0), x.get('cur_price') or float('inf'))
        )
        
        return sorted_products[:5]


# Usage example
if __name__ == "__main__":
    # Configuration
    PROXY_LIST = [
        # Add your proxies here: "ip:port" or "user:pass@ip:port"
        # "123.45.67.89:8080",
        # "user:pass@98.76.54.32:3128"
    ]
    
    CAPTCHA_API_KEY = None  # Get from 2captcha.com
    AMAZON_API_KEY = None   # Amazon Product Advertising API
    
    orchestrator = ScraperOrchestrator(
        proxy_list=PROXY_LIST if PROXY_LIST else None,
        captcha_api_key=CAPTCHA_API_KEY,
        amazon_api_key=AMAZON_API_KEY
    )
    
    try:
        product = "Honey"
        category = "Grocery"
        results = orchestrator.scrape_all(
            product_name= product,
            category= category,
            platforms=['amazon'],  # Add 'flipkart' if FlipkartScraper is implemented
            deep_details=True,
            max_product=2,
            reviews=False
        )
        print(json.dumps(results, indent=2))
        csv_file = orchestrator.export_to_csv_pandas(results, product=product.capitalize())
        
        if csv_file:
            print(f"\n✓ Products exported to: {csv_file}")
            
    except Exception as e:
        logger.error(f"Application error: {e}")