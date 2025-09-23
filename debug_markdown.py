#!/usr/bin/env python3
"""
Debug the specific formatting issue seen in Streamlit
"""
import streamlit as st

def test_markdown_formatting():
    """Test different markdown formatting approaches"""
    
    # The problematic format that might be generated
    problematic_format = """**I found the following available 1-hour slots (all times local):

1**. Tuesday 2025-09-16 09:00 - 10:00
2. Wednesday 2025-09-17 09:00 - 10:00
3. Thursday 2025-09-18 09:00 - 10:00

Please pick a slot number (1-3) or say 'no' to see next week's options."""

    # A better format
    better_format = """I found the following available 1-hour slots (all times local):

1. Tuesday 2025-09-16 09:00 - 10:00
2. Wednesday 2025-09-17 09:00 - 10:00  
3. Thursday 2025-09-18 09:00 - 10:00

Please pick a slot number (1-3) or say 'no' to see next week's options."""

    # Another approach with proper markdown separation
    separated_format = """**Available 1-hour slots (all times local):**

1. Tuesday 2025-09-16 09:00 - 10:00
2. Wednesday 2025-09-17 09:00 - 10:00
3. Thursday 2025-09-18 09:00 - 10:00

Please pick a slot number (1-3) or say 'no' to see next week's options."""

    print("=== TESTING MARKDOWN FORMATS ===")
    
    print("\n1. PROBLEMATIC FORMAT:")
    print(repr(problematic_format))
    print("\nRendered:")
    print(problematic_format)
    
    print("\n2. BETTER FORMAT:")
    print(repr(better_format))
    print("\nRendered:")
    print(better_format)
    
    print("\n3. SEPARATED FORMAT:")
    print(repr(separated_format))
    print("\nRendered:")
    print(separated_format)

if __name__ == "__main__":
    test_markdown_formatting()
