import os
from dotenv import load_dotenv
from backend.auth.jwt_auth import create_access_token, verify_token

load_dotenv()

print("="*60)
print("JWT TOKEN DEBUGGING")
print("="*60)

# Check SECRET_KEY
secret = "-|0pJo:aiZA.Y|[[7E#f<z(DqF4u*OGI"
print(f"\n1. SECRET_KEY loaded: {secret[:20]}..." if secret else "❌ SECRET_KEY NOT FOUND")

# Create test token
print("\n2. Creating test token...")
test_token = create_access_token({"sub": 1})
print(f"   Token: {test_token[:50]}...")
print(f"   Length: {len(test_token)}")

# Verify token
print("\n3. Verifying token...")
try:
    payload = verify_token(test_token)
    print(f"   ✅ SUCCESS! Payload: {payload}")
except Exception as e:
    print(f"   ❌ FAILED! Error: {e}")

# Test with your actual token from Postman
print("\n4. Paste your token from Postman:")
print("   (or press Enter to skip)")
user_token = input("   Token: ").strip()

if user_token:
    if user_token.startswith("Bearer "):
        user_token = user_token[7:]  # Remove "Bearer "
    
    try:
        payload = verify_token(user_token)
        print(f"   ✅ Token valid! User ID: {payload.get('sub')}")
    except Exception as e:
        print(f"   ❌ Token invalid! Error: {e}")

print("\n" + "="*60)