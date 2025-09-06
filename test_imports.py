import sys
import os

sys.path.append(".")

try:
    from app.models.database_models import Customer, Product, Sales, Activity

    print("✅ Database models imported successfully")
    print(f"Customer table: {Customer.__tablename__}")
    print(f"Product table: {Product.__tablename__}")
    print(f"Sales table: {Sales.__tablename__}")
    print(f"Activity table: {Activity.__tablename__}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback

    traceback.print_exc()
