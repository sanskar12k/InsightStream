import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def load_proxies_from_file(file_path: str = "config/proxies.txt") -> List[str]:
    """
    Load proxy list from configuration file.

    Format: username:password@ip:port
    Returns: List of proxy strings
    """
    if not os.path.exists(file_path):
        logger.warning(f"Proxy file not found: {file_path}")
        return []

    proxies = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    proxies.append(line)

        logger.info(f"✓ Loaded {len(proxies)} proxies from {file_path}")
        return proxies

    except Exception as e:
        logger.error(f"Error loading proxies from {file_path}: {e}")
        return []

def get_proxy_list() -> Optional[List[str]]:
    """
    Get proxy list based on environment.

    Priority:
    1. Load from config/proxies.txt (local or Railway)
    2. Return None if no proxies configured
    """
    # Try loading from file
    proxies = load_proxies_from_file("config/proxies.txt")

    if proxies:
        return proxies

    logger.warning("No proxies configured. Scraping without proxy rotation.")
    return None
