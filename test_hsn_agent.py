# Basic test script for HSN Code Validation Agent

# import necessary libraries
import requests
from hsn_agent import validate_hsn

# Local Validation Logic Test
def test_local_validation():
    print("Running local validation tests...")
    codes = ["01012100", "99999999", "abc", "0101"]
    for code in codes:
        result = validate_hsn(code)
        print(f"[Local] {code}: {result}")

# API Endpoint Test (/validate)
def test_api_validation():
    print("\nTesting /validate API endpoint...")
    try:
        res = requests.post(
            "http://127.0.0.1:5000/validate",
            json={"hsn_code": "01012100"}
        )
        print(f"[API] Status: {res.status_code}")
        print(f"[API] Response: {res.json()}")
    except requests.exceptions.ConnectionError:
        print("[API] Error: Cannot connect to server. Is it running on http://127.0.0.1:5000?")
    except Exception as e:
        print(f"[API] Unexpected error: {e}")

# Run All Tests
if __name__ == "__main__":
    test_local_validation()
    test_api_validation()
