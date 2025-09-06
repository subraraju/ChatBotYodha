"""Activity service for managing conversation activities in the database."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from app.models.database_models import Activity, Sales, Product
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ActivityService:
    """Service for managing Activity table operations."""
    
    @staticmethod
    def get_latest_sales_id(db: Session, customer_id: int, product_id: Optional[int] = None) -> Optional[int]:
        """
        Get the latest sales_id for a customer and product combination.
        
        Args:
            db: Database session
            customer_id: Customer ID
            product_id: Product ID (optional)
            
        Returns:
            Latest sales_id or None if not found
        """
        try:
            # Use raw SQL query to avoid SQLAlchemy relationship issues
            if product_id:
                result = db.execute(
                    text("SELECT sales_id FROM sales WHERE customer_id = :customer_id AND product_id = :product_id ORDER BY sale_date DESC LIMIT 1"),
                    {"customer_id": customer_id, "product_id": product_id}
                ).fetchone()
            else:
                result = db.execute(
                    text("SELECT sales_id FROM sales WHERE customer_id = :customer_id ORDER BY sale_date DESC LIMIT 1"),
                    {"customer_id": customer_id}
                ).fetchone()
            
            return result[0] if result else None
            
        except Exception as e:
            print(f"Error getting latest sales_id: {e}")
            return None
    
    @staticmethod
    def get_customer_product_ids(db: Session, customer_id: int, limit: int = 5) -> List[int]:
        """
        Get product IDs from customer's recent purchases.
        
        Args:
            db: Database session
            customer_id: Customer ID
            limit: Maximum number of recent products to retrieve
            
        Returns:
            List of product IDs from recent purchases
        """
        try:
            # Use raw SQL query to avoid SQLAlchemy relationship issues
            result = db.execute(
                text("SELECT DISTINCT product_id FROM sales WHERE customer_id = :customer_id ORDER BY sale_date DESC LIMIT :limit"),
                {"customer_id": customer_id, "limit": limit}
            ).fetchall()
            
            product_ids = [row[0] for row in result]
            
            print(f"Found {len(product_ids)} product IDs for customer {customer_id}: {product_ids}")
            return product_ids
            
        except Exception as e:
            print(f"Error getting customer product IDs: {e}")
            return []
    
    @staticmethod
    def get_most_recent_product_id(db: Session, customer_id: int) -> Optional[int]:
        """
        Get the most recent product ID purchased by the customer.
        
        Args:
            db: Database session
            customer_id: Customer ID
            
        Returns:
            Most recent product ID or None if not found
        """
        try:
            # Use raw SQL query to avoid SQLAlchemy relationship issues
            result = db.execute(
                text("SELECT product_id FROM sales WHERE customer_id = :customer_id ORDER BY sale_date DESC LIMIT 1"),
                {"customer_id": customer_id}
            ).fetchone()
            
            if result:
                product_id = result[0]
                print(f"Most recent product ID for customer {customer_id}: {product_id}")
                return product_id
            else:
                print(f"No sales found for customer {customer_id}")
                return None
            
        except Exception as e:
            print(f"Error getting most recent product ID: {e}")
            return None
    
    @staticmethod
    def create_chatbot_activity(
        db: Session,
        customer_id: int,
        session_id: str,
        url_data: str,
        product_id: Optional[int] = None,
        description: Optional[str] = None,
        comments: Optional[str] = None
    ) -> Optional[int]:
        """
        Create a new chatbot activity record with product_id from user's query context.
        
        Args:
            db: Database session
            customer_id: Customer ID
            session_id: Session ID
            url_data: Complete URL to the stored conversation file
            product_id: Product ID (should be from user's actual query, not latest purchase)
            description: Activity description
            comments: Additional comments
            
        Returns:
            Activity ID if successful, None if failed
        """
        try:
            # If product_id is provided, use it (it should be from the product user asked about)
            # If not provided, fallback to most recent product from purchases as backup
            if product_id is None:
                product_id = ActivityService.get_most_recent_product_id(db, customer_id)
                if product_id:
                    print(f"No product_id from session, using most recent product ID {product_id} for customer {customer_id}")
                else:
                    print(f"No product purchases found for customer {customer_id}, creating activity without product_id")
            else:
                print(f"Using product_id {product_id} from user's query context for customer {customer_id}")
            
            # Get the latest sales_id for this customer and product
            sales_id = None
            try:
                sales_id = ActivityService.get_latest_sales_id(db, customer_id, product_id)
                if sales_id:
                    print(f"Found sales_id {sales_id} for customer {customer_id}, product {product_id}")
            except Exception as e:
                print(f"Warning: Could not get sales_id: {e}")
                sales_id = None
            
            # Create activity record with product data from user's query
            try:
                activity = Activity(
                    customer_id=customer_id,
                    product_id=product_id,  # Now uses product from user's actual query
                    activity_type="CHATBOT",
                    description=description or f"Customer service chat session completed",
                    comments=comments or f"Conversation stored in Azure Blob Storage",
                    activity_date=datetime.now()
                )
                
                # Try to set additional fields if they exist in the model
                if hasattr(activity, 'sales_id'):
                    activity.sales_id = sales_id
                if hasattr(activity, 'session_id'):
                    activity.session_id = session_id
                if hasattr(activity, 'url_data'):
                    activity.url_data = url_data  # Complete downloadable URL
                
                db.add(activity)
                db.commit()
                db.refresh(activity)
                
                print(f"Created activity record with ID: {activity.activity_id}")
                print(f"  Customer ID: {customer_id}")
                print(f"  Product ID: {product_id} ({'from user query' if product_id else 'none available'})")
                print(f"  Sales ID: {sales_id}")
                print(f"  Session ID: {session_id}")
                print(f"  Complete URL: {url_data}")
                return activity.activity_id
                
            except Exception as model_error:
                db.rollback()
                print(f"Model error: {model_error}")
                
                # Fallback: Create minimal activity record with just core fields
                print("Attempting fallback creation with minimal fields...")
                activity = Activity(
                    customer_id=customer_id,
                    product_id=product_id,  # Still use actual product ID in fallback
                    activity_type="CHATBOT",
                    description=f"{description or 'Chat session'} | Session: {session_id} | URL: {url_data}",
                    comments=comments or f"Conversation stored in Azure Blob Storage"
                )
                
                db.add(activity)
                db.commit()
                db.refresh(activity)
                
                print(f"Created fallback activity record with ID: {activity.activity_id}")
                return activity.activity_id
            
        except Exception as e:
            print(f"Error creating activity record: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def update_activity_with_conversation_summary(
        db: Session,
        activity_id: int,
        conversation_summary: Dict[str, Any]
    ) -> bool:
        """
        Update an activity record with conversation summary information.
        
        Args:
            db: Database session
            activity_id: Activity ID to update
            conversation_summary: Summary data from the conversation
            
        Returns:
            True if successful, False if failed
        """
        try:
            activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()
            
            if not activity:
                print(f"Activity with ID {activity_id} not found")
                return False
            
            # Update description with conversation details
            total_messages = conversation_summary.get("export_metadata", {}).get("total_messages", 0)
            customer_state = conversation_summary.get("session_info", {}).get("customer_state", "unknown")
            
            updated_description = f"Chat session completed - {total_messages} messages, final state: {customer_state}"
            activity.description = updated_description
            
            # Update comments with additional info
            session_info = conversation_summary.get("session_info", {})
            if session_info.get("recent_purchases"):
                purchase_count = len(session_info["recent_purchases"])
                activity.comments = f"Session involved {purchase_count} recent purchases. Conversation stored in Azure Blob Storage."
            
            db.commit()
            print(f"Updated activity {activity_id} with conversation summary")
            return True
            
        except Exception as e:
            print(f"Error updating activity record: {e}")
            db.rollback()
            return False


def test_activity_service():
    """Test the activity service."""
    from app.database import get_database
    
    try:
        db = next(get_database())
        
        # Test getting latest sales_id
        sales_id = ActivityService.get_latest_sales_id(db, customer_id=1)
        print(f"Latest sales_id for customer 1: {sales_id}")
        
        print("✅ Activity service test successful")
        return True
        
    except Exception as e:
        print(f"❌ Activity service test failed: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    # Test the activity service
    test_activity_service()
