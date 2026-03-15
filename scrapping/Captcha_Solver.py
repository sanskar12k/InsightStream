from typing import List, Dict, Optional
from scrapping.config import CAPTCHA_AVAILABLE 
import logging
if CAPTCHA_AVAILABLE:
    from twocaptcha import TwoCaptcha

logger = logging.getLogger(__name__)

class CaptchaSolver:
    """Handles CAPTCHA solving using 2Captcha service"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        if api_key and CAPTCHA_AVAILABLE:
            self.solver = TwoCaptcha(api_key)
        else:
            self.solver = None
            if api_key and not CAPTCHA_AVAILABLE:
                logger.warning("2captcha-python not installed. Install with: pip install 2captcha-python")
    
    def solve_recaptcha(self, site_key: str, url: str) -> Optional[str]:
        """Solve reCAPTCHA v2"""
        if not self.solver:
            logger.warning("No CAPTCHA solver configured")
            return None
        
        try:
            logger.info("Solving reCAPTCHA...")
            result = self.solver.recaptcha(
                sitekey=site_key,
                url=url
            )
            logger.info("CAPTCHA solved successfully")
            return result['code']
        except Exception as e:
            logger.error(f"CAPTCHA solving failed: {e}")
            return None
    
    def solve_hcaptcha(self, site_key: str, url: str) -> Optional[str]:
        """Solve hCaptcha"""
        if not self.solver:
            logger.warning("No CAPTCHA solver configured")
            return None
        
        try:
            logger.info("Solving hCaptcha...")
            result = self.solver.hcaptcha(
                sitekey=site_key,
                url=url
            )
            logger.info("hCaptcha solved successfully")
            return result['code']
        except Exception as e:
            logger.error(f"hCaptcha solving failed: {e}")
            return None
