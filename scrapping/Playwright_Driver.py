from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import random
import logging
from typing import Optional
from scrapping.config import ScraperConfig

logger = logging.getLogger(__name__)

class PlaywrightDriver:
    """Playwright wrapper with Selenium-compatible API"""

    def __init__(self, proxy: Optional[str] = None, headless: bool = True):
        self.proxy = proxy
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def __enter__(self):
        """Initialize Playwright and create page"""
        self.playwright = sync_playwright().start()

        # Launch browser with anti-detection flags
        launch_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-gpu',
            '--disable-notifications',
            '--disable-popup-blocking',
            '--disable-extensions',
            '--disable-infobars',
        ]

        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=launch_args
        )

        # Create context with proxy and user agent
        context_options = {
            'user_agent': random.choice(ScraperConfig.USER_AGENTS),
            'viewport': {'width': 1920, 'height': 1080},
        }

        if self.proxy:
            context_options['proxy'] = {'server': f'http://{self.proxy}'}

        self.context = self.browser.new_context(**context_options)

        # Anti-detection: Hide webdriver property
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Create page
        self.page = self.context.new_page()

        # Set timeouts
        self.page.set_default_timeout(ScraperConfig.PAGE_LOAD_TIMEOUT * 1000)

        logger.info("✓ Playwright driver created successfully")

        return self  # Return self, not page - acts as driver wrapper

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.warning(f"Error closing driver: {e}")

    # Selenium-compatible API methods

    def get(self, url: str):
        """Navigate to URL (Selenium compatibility)"""
        self.page.goto(url, wait_until='domcontentloaded')

    def goto(self, url: str):
        """Navigate to URL (Playwright native)"""
        self.page.goto(url, wait_until='domcontentloaded')

    def find_element(self, by, selector: str):
        """Selenium-compatible element finder"""
        # Convert By.CSS_SELECTOR to plain selector
        element = self.page.query_selector(selector)
        if element:
            return PlaywrightElement(element)
        return None

    def find_elements(self, by, selector: str):
        """Selenium-compatible elements finder"""
        elements = self.page.query_selector_all(selector)
        return [PlaywrightElement(e) for e in elements]

    def query_selector(self, selector: str):
        """Playwright native selector"""
        element = self.page.query_selector(selector)
        return PlaywrightElement(element) if element else None

    def query_selector_all(self, selector: str):
        """Playwright native selector all"""
        elements = self.page.query_selector_all(selector)
        return [PlaywrightElement(e) for e in elements]

    def wait_for_selector(self, selector: str, timeout: int = None):
        """Wait for element to appear"""
        timeout_ms = (timeout * 1000) if timeout else None
        element = self.page.wait_for_selector(selector, timeout=timeout_ms)
        return PlaywrightElement(element) if element else None

    def execute_script(self, script: str, *args):
        """Selenium-compatible script execution"""
        # Selenium allows "return statement", Playwright needs just the expression
        # Convert "return document.title" to "document.title"
        script = script.strip()
        if script.startswith('return '):
            script = script[7:]  # Remove "return "

        if args:
            # For element-based scripts, use evaluate on element
            if args[0]._element:
                return args[0]._element.evaluate(script)
            return None

        return self.page.evaluate(script)

    def evaluate(self, script: str):
        """Playwright native evaluate"""
        return self.page.evaluate(script)

    @property
    def page_source(self):
        """Get page HTML (Selenium compatibility)"""
        return self.page.content()

    def content(self):
        """Get page HTML (Playwright native)"""
        return self.page.content()

    def set_page_load_timeout(self, timeout: float):
        """Set page load timeout in seconds"""
        self.page.set_default_navigation_timeout(timeout * 1000)

    def implicitly_wait(self, timeout: float):
        """Set implicit wait (Playwright uses default timeout)"""
        self.page.set_default_timeout(timeout * 1000)

    def quit(self):
        """Close browser (Selenium compatibility)"""
        self.__exit__(None, None, None)


class PlaywrightElement:
    """Wrapper for Playwright elements to match Selenium API"""

    def __init__(self, element):
        self._element = element

    @property
    def text(self):
        """Get element text (Selenium compatibility)"""
        return self._element.inner_text() if self._element else ""

    def text_content(self):
        """Get element text content"""
        return self._element.text_content() if self._element else ""

    def get_attribute(self, attr: str):
        """Get element attribute"""
        return self._element.get_attribute(attr) if self._element else None

    def find_element(self, by, selector: str):
        """Find child element"""
        child = self._element.query_selector(selector) if self._element else None
        return PlaywrightElement(child) if child else None

    def find_elements(self, by, selector: str):
        """Find child elements"""
        if not self._element:
            return []
        children = self._element.query_selector_all(selector)
        return [PlaywrightElement(e) for e in children]

    def query_selector(self, selector: str):
        """Playwright native child selector"""
        child = self._element.query_selector(selector) if self._element else None
        return PlaywrightElement(child) if child else None

    def query_selector_all(self, selector: str):
        """Playwright native child selector all"""
        if not self._element:
            return []
        children = self._element.query_selector_all(selector)
        return [PlaywrightElement(e) for e in children]

    def click(self):
        """Click element"""
        if self._element:
            self._element.click()

    def evaluate(self, script: str):
        """Execute JS on element"""
        if self._element:
            # Strip "return" prefix for Selenium compatibility
            script = script.strip()
            if script.startswith('return '):
                script = script[7:]
            return self._element.evaluate(script)
        return None
