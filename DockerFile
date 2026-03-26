# 1. Use the official Playwright image (This contains ALL the missing libglib, libnss3, etc.)
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Install the Playwright Chromium browser 
# (We don't need --with-deps anymore because the base image already has them!)
RUN playwright install chromium

# 5. Copy your actual code into the container
COPY . .

# 6. Start your FastAPI server
# Railway automatically assigns a PORT environment variable, so we use it here.
# NOTE: Change "main:app" if your FastAPI instance is named differently or in a different file!
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}