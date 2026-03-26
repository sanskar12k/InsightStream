# Railway Environment Variables Configuration

## Required Environment Variables for Selenium Fix

Add these environment variables in your Railway project dashboard:

### Navigation
Railway Project → Variables → Add Variable

### Variables to Add

```bash
# Explicit paths (Railway Nixpacks installs to these locations)
CHROME_BIN=/usr/bin/chromium
CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Selenium standard env var
SE_CHROMEDRIVER=/usr/bin/chromedriver

# Optional: Control auto-download behavior
SE_MANAGER_CACHE_PATH=/tmp/selenium_cache
```

## Why These Variables Are Needed

1. **CHROME_BIN**: Tells Selenium exactly where to find the Chrome/Chromium binary
2. **CHROMEDRIVER_PATH**: Points to the system-installed chromedriver (from Aptfile)
3. **SE_CHROMEDRIVER**: Selenium's standard environment variable for chromedriver path
4. **SE_MANAGER_CACHE_PATH**: Optional - controls where Selenium Manager caches auto-downloaded drivers

## How to Add in Railway

1. Go to your Railway project dashboard
2. Click on your service
3. Navigate to the "Variables" tab
4. Click "New Variable"
5. Add each variable name and value
6. Save and redeploy

## Verification

After adding these variables and redeploying:

1. Check the build logs for the pre-flight check output:
   - Should see: "✓ Chrome found: ..."
   - Should see: "✓ ChromeDriver found: ..."
   - Should see: "✓ All checks passed - Selenium should work"

2. When scraping runs, check runtime logs for:
   - "✓ Found Chrome binary at: /usr/bin/chromium"
   - "✓ Using chromedriver from CHROMEDRIVER_PATH: /usr/bin/chromedriver"
   - "✓ Chrome validation passed: ..."
   - "✓ Selenium driver created successfully"

## Troubleshooting

If pre-flight checks fail:
- **Chrome not found**: Check if Aptfile has `chromium` installed
- **ChromeDriver not found**: Check if Aptfile has `chromium-driver` installed
- **Missing libraries**: Check if all required packages from Aptfile are installed

The pre-flight check will prevent the app from starting if critical components are missing, making issues immediately visible in deployment logs.
