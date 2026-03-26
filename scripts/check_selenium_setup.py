#!/usr/bin/env python3
"""
Pre-flight check for Selenium setup on Railway
Run this before starting the app to validate Chrome/driver installation
"""
import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_chrome():
    """Check if Chrome/Chromium is installed"""
    paths = [
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome',
    ]

    for path in paths:
        if os.path.exists(path):
            try:
                result = subprocess.run(
                    [path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"✓ Chrome found: {result.stdout.strip()} at {path}")
                    return True
            except Exception as e:
                logger.warning(f"Chrome at {path} failed: {e}")

    logger.error("✗ No working Chrome installation found")
    return False

def check_chromedriver():
    """Check if chromedriver is installed"""
    paths = [
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver',
    ]

    for path in paths:
        if os.path.exists(path):
            try:
                result = subprocess.run(
                    [path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"✓ ChromeDriver found: {result.stdout.strip()} at {path}")
                    return True
            except Exception as e:
                logger.warning(f"ChromeDriver at {path} failed: {e}")

    logger.warning("⚠ No system chromedriver - Selenium will auto-download")
    return True  # Not critical - can use auto-download

def check_shared_libraries():
    """Check for required shared libraries"""
    try:
        result = subprocess.run(
            ['ldd', '/usr/bin/chromium'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if 'not found' in result.stdout:
            logger.error(f"✗ Missing libraries:\n{result.stdout}")
            return False
        logger.info("✓ All shared libraries found")
        return True
    except Exception as e:
        logger.warning(f"Could not check libraries: {e}")
        return True

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Selenium Setup Pre-flight Check")
    logger.info("=" * 60)

    checks = [
        ("Chrome/Chromium", check_chrome),
        ("ChromeDriver", check_chromedriver),
        ("Shared Libraries", check_shared_libraries),
    ]

    all_passed = True
    for name, check_func in checks:
        logger.info(f"\nChecking {name}...")
        if not check_func():
            all_passed = False

    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("✓ All checks passed - Selenium should work")
        sys.exit(0)
    else:
        logger.error("✗ Some checks failed - Selenium may not work")
        sys.exit(1)
