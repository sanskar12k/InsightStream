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
            current_idx = self.current_index  # Store before incrementing for logging
            self.current_index = (self.current_index + 1) % len(self.proxies)

            if proxy not in self.failed_proxies:
                # Log proxy usage with masked credentials for security
                proxy_display = proxy[:20] + "..." if len(proxy) > 20 else proxy
                logger.info(f"Using proxy: {proxy_display} (index {current_idx})")
                return {
                    'http': f'http://{proxy}',
                    'https': f'http://{proxy}'
                }
            else:
                proxy_display = proxy[:20] + "..." if len(proxy) > 20 else proxy
                logger.debug(f"Skipping failed proxy: {proxy_display}")

            attempts += 1

        logger.error(f"All {len(self.proxies)} proxies failed! ({len(self.failed_proxies)}/{len(self.proxies)} marked as failed)")
        return None
    
    def mark_failed(self, proxy: str):
        """Mark proxy as failed"""
        self.failed_proxies.add(proxy)
        proxy_display = proxy[:20] + "..." if len(proxy) > 20 else proxy
        logger.warning(f"✗ Marked proxy as failed: {proxy_display} ({len(self.failed_proxies)}/{len(self.proxies)} total failed)")
