"""Simple test for cross-range switching without complex imports."""

import re
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# Mock purchase data for testing
MOCK_PURCHASES = [
    {"product_name": "Gaming Laptop Pro", "sale_date": "2024-01-15", "product_id": 1},
    {"product_name": "Wireless Headphones", "sale_date": "2024-01-10", "product_id": 2},
    {"product_name": "Smart Phone Case", "sale_date": "2024-01-05", "product_id": 3},
    {"product_name": "Bluetooth Speaker", "sale_date": "2024-01-01", "product_id": 4},
    {"product_name": "Tablet Stand", "sale_date": "2023-12-28", "product_id": 5},
    {"product_name": "USB-C Cable", "sale_date": "2023-12-25", "product_id": 6},
    {"product_name": "Portable Charger", "sale_date": "2023-12-20", "product_id": 7},
    {"product_name": "Screen Protector", "sale_date": "2023-12-15", "product_id": 8},
    {"product_name": "Keyboard Cover", "sale_date": "2023-12-10", "product_id": 9},
    {"product_name": "Mouse Pad", "sale_date": "2023-12-05", "product_id": 10},
]

@dataclass
class MockSession:
    session_id: str
    state: str = "PRODUCT_SELECTION"
    displayed_purchases: List[Dict] = None
    all_purchases: List[Dict] = None
    has_more_purchases: bool = False
    selected_product: Optional[Dict] = None
    
    def __post_init__(self):
        if self.displayed_purchases is None:
            self.displayed_purchases = []
        if self.all_purchases is None:
            self.all_purchases = []

def extract_product_from_input(message: str, session: MockSession) -> Optional[Dict]:
    """Mock implementation of product extraction with cross-range switching."""
    
    message_lower = message.lower()
    
    # Check for explicit range switching commands
    if any(phrase in message_lower for phrase in ['show 1-5', 'show first 5', 'show earlier', 'show previous']):
        # Switch to 1-5 range
        session.displayed_purchases = session.all_purchases[:5]
        session.has_more_purchases = len(session.all_purchases) > 5
        return {"switch_to_range": "1-5"}
    
    if any(phrase in message_lower for phrase in ['show 6-10', 'show next 5', 'show more', 'show later']):
        # Switch to 6-10 range  
        session.displayed_purchases = session.all_purchases[5:10]
        session.has_more_purchases = False
        return {"switch_to_range": "6-10"}
    
    # Auto-pagination phrases
    auto_pagination_phrases = [
        "it's not in this list", "not in this list", "i don't see it here", 
        "not what i'm looking for", "can't see it", "not there", 
        "none of these", "not listed", "missing", "different product", 
        "other product", "not among these"
    ]
    
    if any(phrase in message_lower for phrase in auto_pagination_phrases):
        if len(session.displayed_purchases) == 5 and session.displayed_purchases == session.all_purchases[:5]:
            # Currently showing 1-5, switch to 6-10
            session.displayed_purchases = session.all_purchases[5:10]
            session.has_more_purchases = False
            return {"auto_pagination": "6-10"}
    
    # Check for product number references
    product_numbers = re.findall(r'\b(\d+)\b', message)
    
    for num_str in product_numbers:
        num = int(num_str)
        
        # Handle beyond-range requests
        if num > 10:
            return {"beyond_range": num}
        
        # Handle cross-range product selection
        if 1 <= num <= 10:
            # Check if product is in current displayed range
            current_range_start = 1 if len(session.displayed_purchases) == 5 and session.displayed_purchases == session.all_purchases[:5] else 6
            current_range_end = 5 if current_range_start == 1 else 10
            
            if current_range_start <= num <= current_range_end:
                # Product is in current range
                product_index = num - current_range_start
                return session.displayed_purchases[product_index]
            else:
                # Product is in different range - need to switch
                if 1 <= num <= 5:
                    # Switch to 1-5 range
                    session.displayed_purchases = session.all_purchases[:5]
                    session.has_more_purchases = len(session.all_purchases) > 5
                    return {"cross_range_switch": "1-5", "selected_product": session.all_purchases[num-1]}
                elif 6 <= num <= 10:
                    # Switch to 6-10 range
                    session.displayed_purchases = session.all_purchases[5:10]
                    session.has_more_purchases = False
                    return {"cross_range_switch": "6-10", "selected_product": session.all_purchases[num-1]}
    
    return None

def test_cross_range_scenarios():
    """Test various cross-range switching scenarios."""
    
    print("=== Testing Cross-Range Product Switching Logic ===\n")
    
    # Initialize session with mock data
    session = MockSession(
        session_id="test_cross_range",
        displayed_purchases=MOCK_PURCHASES[:5],  # Start with 1-5
        all_purchases=MOCK_PURCHASES,
        has_more_purchases=True
    )
    
    test_scenarios = [
        # Scenario 1: Auto-pagination
        ("It's not in this list", "Should trigger auto-pagination to 6-10"),
        
        # Scenario 2: Select from new range
        ("Tell me about product 7", "Should select product 7 from 6-10 range"),
        
        # Scenario 3: Cross-range selection back to 1-5
        ("I want product 2", "Should switch back to 1-5 and select product 2"),
        
        # Scenario 4: Explicit range switching
        ("show 6-10", "Should explicitly switch to 6-10 range"),
        
        # Scenario 5: Beyond range request
        ("Tell me about product 15", "Should handle beyond-range gracefully"),
        
        # Scenario 6: Return to 1-5 explicitly
        ("show 1-5", "Should switch back to 1-5 range"),
    ]
    
    for i, (message, expected) in enumerate(test_scenarios, 1):
        print(f"Test {i}: {message}")
        print(f"Expected: {expected}")
        
        # Show current state
        current_range = "1-5" if session.displayed_purchases == session.all_purchases[:5] else "6-10"
        print(f"Current range: {current_range}")
        
        result = extract_product_from_input(message, session)
        
        if result:
            if "auto_pagination" in result:
                print(f"✅ Auto-pagination triggered: {result['auto_pagination']}")
            elif "switch_to_range" in result:
                print(f"✅ Explicit range switch: {result['switch_to_range']}")
            elif "cross_range_switch" in result:
                print(f"✅ Cross-range switch: {result['cross_range_switch']}")
                print(f"   Selected product: {result['selected_product']['product_name']}")
            elif "beyond_range" in result:
                print(f"⚠️ Beyond-range request: Product {result['beyond_range']}")
            elif "product_name" in result:
                print(f"✅ Product selected: {result['product_name']}")
            else:
                print(f"✅ Result: {result}")
        else:
            print("❌ No result returned")
        
        # Show new state
        new_range = "1-5" if session.displayed_purchases == session.all_purchases[:5] else "6-10"
        print(f"New range: {new_range}")
        print(f"Displayed products: {[p['product_name'] for p in session.displayed_purchases]}")
        print("-" * 60)

if __name__ == "__main__":
    test_cross_range_scenarios()
