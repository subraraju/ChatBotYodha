"""
Test script for the Agentic Chatbot API
"""

import requests
import json
import time

API_BASE_URL = "http://127.0.0.1:8000"


def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False


def test_customers_api():
    """Test the customers API"""
    print("\nTesting customers API...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/customers/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            customers = response.json()
            print(f"Found {len(customers)} customers")
            if customers:
                print(f"First customer: {customers[0]}")
        return response.status_code == 200
    except Exception as e:
        print(f"Customers API test failed: {e}")
        return False


def test_products_api():
    """Test the products API"""
    print("\nTesting products API...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/products/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            products = response.json()
            print(f"Found {len(products)} products")
            if products:
                print(f"First product: {products[0]}")
        return response.status_code == 200
    except Exception as e:
        print(f"Products API test failed: {e}")
        return False


def test_chat_functionality():
    """Test the chat functionality"""
    print("\nTesting chat functionality...")

    customer_email = "test@example.com"
    test_messages = [
        "Hello, can you help me?",
        "Show me information about customers",
        "What products do you have?",
        "Tell me about recent sales",
    ]

    try:
        # Start a new chat session
        print(f"Starting chat session for {customer_email}...")
        response = requests.post(
            f"{API_BASE_URL}/api/chat/start", params={"customer_email": customer_email}
        )

        if response.status_code != 200:
            print(f"Failed to start chat session: {response.text}")
            return False

        session_data = response.json()
        session_id = session_data["session_id"]
        print(f"Session started: {session_id}")

        # Send test messages
        for message in test_messages:
            print(f"\nSending: {message}")
            response = requests.post(
                f"{API_BASE_URL}/api/chat/{session_id}/message",
                params={"message": message, "use_external_search": False},
            )

            if response.status_code == 200:
                response_data = response.json()
                print(f"Response: {response_data['response'][:100]}...")
            else:
                print(f"Failed to send message: {response.text}")
                return False

            time.sleep(1)  # Small delay between messages

        # Get session data
        print(f"\nRetrieving session data...")
        response = requests.get(f"{API_BASE_URL}/api/chat/{session_id}")
        if response.status_code == 200:
            session = response.json()
            print(f"Session has {len(session['messages'])} messages")

        # Test export
        print(f"\nTesting export functionality...")
        response = requests.get(f"{API_BASE_URL}/api/chat/{session_id}/export/json")
        if response.status_code == 200:
            print("Export successful")

        return True

    except Exception as e:
        print(f"Chat functionality test failed: {e}")
        return False


def test_tavily_search():
    """Test Tavily search functionality"""
    print("\nTesting Tavily search...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/tavily/search",
            params={
                "query": "customer relationship management best practices",
                "max_results": 3,
            },
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Tavily search successful")
            print(f"Found {len(result.get('results', []))} results")
        else:
            print(f"Tavily search failed: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Tavily search test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("AGENTIC CHATBOT API TESTS")
    print("=" * 50)

    tests = [
        ("Health Check", test_health_check),
        ("Customers API", test_customers_api),
        ("Products API", test_products_api),
        ("Chat Functionality", test_chat_functionality),
        ("Tavily Search", test_tavily_search),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'=' * 20}")
        print(f"Running: {test_name}")
        print(f"{'=' * 20}")

        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"Test {test_name} crashed: {e}")
            results[test_name] = False

        time.sleep(1)

    # Print summary
    print(f"\n{'=' * 50}")
    print("TEST SUMMARY")
    print(f"{'=' * 50}")

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the logs above.")


if __name__ == "__main__":
    run_all_tests()
