#!/usr/bin/env python3

# Test just the basic imports first
try:
    print("Testing basic imports...")
    import os
    import json
    import uuid
    print("✓ Standard library imports OK")
    
    from typing import List, Dict, Any, Optional, Tuple
    print("✓ Typing imports OK")
    
    from enum import Enum
    print("✓ Enum import OK")
    
    from dotenv import load_dotenv
    print("✓ Dotenv import OK")
    
    # Test the models that might have typing issues
    from app.models.pydantic_models import CustomerSession
    print("✓ CustomerSession import OK")
    
    print("✅ All basic imports successful!")
    
except Exception as e:
    print(f"❌ Error in imports: {e}")
    import traceback
    traceback.print_exc()
