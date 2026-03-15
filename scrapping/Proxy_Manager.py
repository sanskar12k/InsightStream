from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProxyManager:
    """Manages proxy rotation"""
    
    def __init__(self, proxy_list: Optional[List[str]] = None):
        self.proxies = proxy_list or []
        self.current_index = 0
        self.failed_proxies = set()
    
    def get_proxy(self) -> Optional[Dict]:
        """Get next working proxy"""
        if not self.proxies:
            return None
        
        attempts = 0
        while attempts < len(self.proxies):
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            
            if proxy not in self.failed_proxies:
                return {
                    'http': f'http://{proxy}',
                    'https': f'http://{proxy}'
                }
            attempts += 1
        
        logger.warning("No working proxies available")
        return None
    
    def mark_failed(self, proxy: str):
        """Mark proxy as failed"""
        self.failed_proxies.add(proxy)
        logger.warning(f"Proxy marked as failed: {proxy}")
