#!/usr/bin/env python3
"""
Script to check if the current SUPABASE_KEY is a service_role key or anon key.
"""

import os
import json
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_supabase_key():
    """Check the type of the current Supabase key"""
    key = os.getenv('SUPABASE_KEY')
    
    if not key:
        print("❌ No SUPABASE_KEY found in environment")
        return False
    
    try:
        # Split JWT token into parts
        parts = key.split('.')
        
        if len(parts) < 2:
            print("❌ Invalid JWT format")
            return False
        
        # Decode the payload (second part)
        payload = parts[1]
        # Add padding if needed for base64 decoding
        payload += '=' * (4 - len(payload) % 4)
        
        # Decode and parse JSON
        decoded = base64.b64decode(payload)
        data = json.loads(decoded)
        
        # Extract role
        role = data.get('role', 'unknown')
        iss = data.get('iss', 'unknown')
        
        print(f"🔍 JWT Analysis:")
        print(f"   Issuer: {iss}")
        print(f"   Role: {role}")
        print(f"   Key prefix: {key[:50]}...")
        
        if role == 'service_role':
            print("\n✅ SUCCESS: This IS a service_role key!")
            print("   This key should bypass RLS and give full database access")
            return True
        elif role == 'anon':
            print("\n❌ PROBLEM: This is an 'anon' key!")
            print("   You need to use the 'service_role' key instead")
            print("\n💡 Solution:")
            print("   1. Go to Supabase Dashboard → Settings → API")
            print("   2. Look for the key labeled 'service_role secret' 🔐")
            print("   3. Copy that key (NOT the 'anon public' key)")
            print("   4. Replace SUPABASE_KEY in your .env file")
            return False
        else:
            print(f"\n⚠️ UNKNOWN: Unexpected role '{role}'")
            return False
            
    except Exception as e:
        print(f"❌ Error decoding JWT: {e}")
        return False

if __name__ == "__main__":
    check_supabase_key() 