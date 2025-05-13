"""
Test script for the /auth/profile endpoint
"""

import requests
import json
import sys

# API base URL
API_BASE_URL = "https://free-api-tvpr.onrender.com"

def register_user(username, password, email, full_name=None):
    """Register a new user"""
    url = f"{API_BASE_URL}/auth/register"
    payload = {
        "username": username,
        "password": password,
        "email": email
    }
    
    if full_name:
        payload["full_name"] = full_name
    
    response = requests.post(url, json=payload)
    return response.json()

def login_user(username, password):
    """Login a user"""
    url = f"{API_BASE_URL}/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    
    response = requests.post(url, json=payload)
    return response.json()

def get_profile(access_token):
    """Get user profile"""
    url = f"{API_BASE_URL}/auth/profile"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(url, headers=headers)
    return response.json()

def create_api_key(access_token, name="My API Key"):
    """Create a new API key"""
    url = f"{API_BASE_URL}/auth/keys"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "name": name
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def main():
    """Main function"""
    # Check if we should register a new user
    if len(sys.argv) > 1 and sys.argv[1] == "--register":
        print("Registering a new user...")
        username = input("Username: ")
        password = input("Password: ")
        email = input("Email: ")
        full_name = input("Full Name (optional): ")
        
        if not full_name:
            full_name = None
        
        result = register_user(username, password, email, full_name)
        print(json.dumps(result, indent=2))
        
        if "access_token" in result:
            access_token = result["access_token"]
            print(f"\nAccess Token: {access_token}")
            
            # Get profile
            print("\nGetting user profile...")
            profile = get_profile(access_token)
            print(json.dumps(profile, indent=2))
            
            # Create API key
            print("\nCreating API key...")
            api_key_result = create_api_key(access_token)
            print(json.dumps(api_key_result, indent=2))
            
            # Get profile again to see API key
            print("\nGetting user profile again...")
            profile = get_profile(access_token)
            print(json.dumps(profile, indent=2))
    else:
        # Login flow
        print("Logging in...")
        username = input("Username: ")
        password = input("Password: ")
        
        result = login_user(username, password)
        print(json.dumps(result, indent=2))
        
        if "access_token" in result:
            access_token = result["access_token"]
            print(f"\nAccess Token: {access_token}")
            
            # Get profile
            print("\nGetting user profile...")
            profile = get_profile(access_token)
            print(json.dumps(profile, indent=2))
            
            # Ask if user wants to create a new API key
            create_new_key = input("\nCreate a new API key? (y/n): ")
            if create_new_key.lower() == "y":
                key_name = input("API Key Name: ")
                api_key_result = create_api_key(access_token, key_name)
                print(json.dumps(api_key_result, indent=2))
                
                # Get profile again to see API key
                print("\nGetting user profile again...")
                profile = get_profile(access_token)
                print(json.dumps(profile, indent=2))

if __name__ == "__main__":
    main()
