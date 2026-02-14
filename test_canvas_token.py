#!/usr/bin/env python3
"""
Canvas Token Tester
Quick script to test Canvas API token directly
"""

import requests
import sys

def test_canvas_token():
    """Test Canvas API token"""

    print("\n" + "="*60)
    print("CANVAS API TOKEN TESTER")
    print("="*60)

    # Get inputs
    canvas_url = input("\nEnter Canvas URL (e.g., https://vuu.instructure.com): ").strip()
    access_token = input("Enter Canvas API Token: ").strip()

    # Clean inputs
    canvas_url = canvas_url.rstrip('/')
    access_token = ''.join(access_token.split())  # Remove all whitespace

    print(f"\n{'='*60}")
    print("TEST DETAILS")
    print(f"{'='*60}")
    print(f"Canvas URL: {canvas_url}")
    print(f"Token Length: {len(access_token)} characters")
    print(f"Token Preview: {access_token[:20]}...")
    print(f"Token Ending: ...{access_token[-10:]}")

    # Test the connection
    print(f"\n{'='*60}")
    print("TESTING CONNECTION")
    print(f"{'='*60}")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        print(f"\nSending request to: {canvas_url}/api/v1/users/self")
        response = requests.get(
            f"{canvas_url}/api/v1/users/self",
            headers=headers,
            timeout=10
        )

        print(f"\nHTTP Status Code: {response.status_code}")
        print(f"\nResponse Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")

        print(f"\nResponse Body:")
        print(response.text)

        if response.status_code == 200:
            user_data = response.json()
            print(f"\n{'='*60}")
            print("✅ SUCCESS!")
            print(f"{'='*60}")
            print(f"Authenticated as: {user_data.get('name')}")
            print(f"User ID: {user_data.get('id')}")
            print(f"Email: {user_data.get('primary_email')}")
            print("\nYour Canvas token is valid! ✅")
            return True
        else:
            print(f"\n{'='*60}")
            print("❌ FAILED!")
            print(f"{'='*60}")

            if response.status_code == 401:
                print("\n⚠️  DIAGNOSIS: Invalid or Expired Token")
                print("\nPossible causes:")
                print("1. Token was copied incorrectly (missing characters)")
                print("2. Token has been revoked in Canvas")
                print("3. Token has expired")
                print("4. You're using a token from a different Canvas instance")
                print("\nHow to fix:")
                print("1. Go to Canvas → Account → Settings")
                print("2. Scroll to 'Approved Integrations'")
                print("3. Delete the old token (if exists)")
                print("4. Click '+ New Access Token'")
                print("5. Set purpose: 'ReadySetClass'")
                print("6. Click 'Generate Token'")
                print("7. COPY THE ENTIRE TOKEN (do not add quotes or spaces)")
                print("8. Try again with the new token")

            elif response.status_code == 403:
                print("\n⚠️  DIAGNOSIS: Insufficient Permissions")
                print("\nThe token doesn't have required permissions.")
                print("Create a new token with full access.")

            elif response.status_code == 404:
                print("\n⚠️  DIAGNOSIS: Wrong Canvas URL")
                print(f"\nThe URL '{canvas_url}' may be incorrect.")
                print("Verify your Canvas instance URL.")

            return False

    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ CONNECTION ERROR")
        print(f"Cannot connect to {canvas_url}")
        print(f"Error: {e}")
        print("\nVerify:")
        print("1. Canvas URL is correct")
        print("2. You have internet connection")
        print("3. Canvas is not blocking your IP")
        return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    test_canvas_token()
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60 + "\n")
