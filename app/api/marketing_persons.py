#!/usr/bin/env python3
"""
Professional Persons API - Database-driven with fallback for offline testing

This module fetches professionals from the database based on party_type column.
Supports: MKTG (Marketing), Business, Individual, etc.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class MarketingPerson:
    """Data class for professional person information"""
    id: int
    name: str
    email: str
    phone: str
    timezone: str
    specialization: str
    availability_note: str

# Mapping of party_type to display labels
PARTY_TYPE_LABELS = {
    'MKTG': 'Marketing Team',
    'Business': 'Business Professionals',
    'Individual': 'Individual Contacts'
}

class MarketingPersonsAPI:
    """
    API for fetching professionals by party_type from database.
    
    Supports dynamic party_type: MKTG, Business, Individual, etc.
    """
    
    # Default timezone mapping (can be extended to store in DB)
    DEFAULT_TIMEZONE = "Asia/Kolkata"
    
    # Store current party_type for context
    current_party_type = 'MKTG'
    
    def __init__(self, party_type: str = 'MKTG'):
        """Initialize API and test database connection"""
        self.fallback_mode = False
        self.current_party_type = party_type
        try:
            self._test_database_connection()
            print("✅ MarketingPersonsAPI: Database connection successful")
        except Exception as e:
            print(f"⚠️ Database unavailable, using fallback data: {e}")
            self.fallback_mode = True
    
    def _get_db_session(self) -> Session:
        """Get database session"""
        from app.database import SessionLocal
        return SessionLocal()
    
    def _test_database_connection(self):
        """Test database connection"""
        from app.models.database_models import Customer
        
        db = self._get_db_session()
        try:
            # Test database connection with proper SQLAlchemy syntax
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            
            # Show count for current party_type
            count = db.query(Customer).filter(Customer.party_type == self.current_party_type).count()
            print(f"✅ Found {count} person(s) with party_type='{self.current_party_type}' in database")
            
            db.close()
        except Exception as e:
            db.close()
            raise Exception(f"Database connection failed: {e}")
    
    def _get_fallback_persons(self) -> List[MarketingPerson]:
        """
        Get fallback marketing persons when database is unavailable.
        
        These should match the actual marketing persons in the database
        (party_type='MKTG') for consistency.
        """
        return [
            MarketingPerson(
                id=1005,
                name="Vishal Matere",
                email="vishmatere1999@gmail.com",
                phone="+918766776988",
                timezone="Asia/Kolkata",
                specialization="Product Demos & Technical Consultations",
                availability_note="Available Monday-Friday, 9 AM - 6 PM IST"
            ),
            MarketingPerson(
                id=1008,
                name="Yodha PCES",
                email="yodhaguy@gmail.com",
                phone="+14086246663",
                timezone="Asia/Kolkata",
                specialization="Business Development & Enterprise Sales",
                availability_note="Available Monday-Friday, 9 AM - 6 PM IST"
            ),
            MarketingPerson(
                id=1020,
                name="Tony Stark",
                email="tony.s@starkindustries.com",
                phone="555-012-3456",
                timezone="America/New_York",
                specialization="International Sales & Partnerships",
                availability_note="Available Monday-Friday, 9 AM - 5 PM EST"
            )
        ]
    
    def get_persons_by_party_type(self, party_type: str = None) -> List[MarketingPerson]:
        """
        Get all persons from database by party_type.
        
        Args:
            party_type: The party_type to filter by (e.g., 'MKTG', 'Business', 'Individual')
                       If None, uses self.current_party_type
        
        Returns:
            List of MarketingPerson objects
        """
        party_type = party_type or self.current_party_type
        
        if self.fallback_mode:
            print(f"📋 Using fallback data (database unavailable)")
            return self._get_fallback_persons()
        
        try:
            from app.models.database_models import Customer
            db = self._get_db_session()
            
            # Query persons by party_type
            customers = db.query(Customer).filter(Customer.party_type == party_type).all()
            
            if not customers:
                print(f"⚠️ No persons found with party_type='{party_type}'")
                db.close()
                return []
            
            print(f"✅ Found {len(customers)} person(s) with party_type='{party_type}'")
            
            persons = []
            for customer in customers:
                # Build full name
                first_name = customer.first_name or ""
                last_name = customer.last_name or ""
                full_name = f"{first_name} {last_name}".strip() or "Team Member"
                
                # Determine timezone based on phone number or default
                timezone = self._determine_timezone(customer.phone, customer.email)
                
                # Generate specialization and availability based on customer data
                specialization = self._get_specialization(customer)
                availability_note = self._get_availability_note(timezone)
                
                person = MarketingPerson(
                    id=customer.customer_id,
                    name=full_name,
                    email=customer.email or "contact@company.com",
                    phone=customer.phone or "N/A",
                    timezone=timezone,
                    specialization=specialization,
                    availability_note=availability_note
                )
                persons.append(person)
            
            persons.sort(key=lambda x: x.name)
            db.close()
            
            return persons
            
        except Exception as e:
            print(f"❌ Error fetching persons from database: {e}")
            return []
    
    def get_active_marketing_persons(self) -> List[MarketingPerson]:
        """Get all active marketing persons (party_type='MKTG') - for backward compatibility"""
        return self.get_persons_by_party_type('MKTG')
    
    def _determine_timezone(self, phone: str, email: str) -> str:
        """Determine timezone based on phone number prefix or email domain"""
        if phone:
            # US phone numbers
            if phone.startswith('+1') or phone.startswith('1-'):
                return "America/New_York"
            # India phone numbers
            if phone.startswith('+91') or phone.startswith('91-'):
                return "Asia/Kolkata"
        return self.DEFAULT_TIMEZONE
    
    def _get_specialization(self, customer) -> str:
        """Get specialization for a marketing person - uses party_type from database"""
        return customer.party_type or "Marketing"
    
    def _get_availability_note(self, timezone: str) -> str:
        """Get availability note based on timezone"""
        if timezone == "America/New_York":
            return "Available Monday-Friday, 9 AM - 5 PM EST"
        elif timezone == "Asia/Kolkata":
            return "Available Monday-Friday, 9 AM - 6 PM IST"
        else:
            return "Available during business hours"
    
    def get_marketing_person_by_email(self, email: str) -> Optional[MarketingPerson]:
        """Get marketing person by email address"""
        persons = self.get_active_marketing_persons()
        for person in persons:
            if person.email == email:
                return person
        return None
    
    def format_selection_list(self, party_type: str = None) -> str:
        """Format persons as a selection list for the bot"""
        party_type = party_type or self.current_party_type
        persons = self.get_persons_by_party_type(party_type)
        
        # Get display label for party_type
        label = PARTY_TYPE_LABELS.get(party_type, f"{party_type} Professionals")
        
        if not persons:
            return f"❌ No {label.lower()} available at the moment."
        
        selection_text = f"🏢 **Our {label}:**\n\n"
        
        for i, person in enumerate(persons, 1):
            selection_text += f"**{i}. {person.name}** 👤\n"
            if person.specialization:
                selection_text += f"   🎯 {person.specialization}\n"
            selection_text += "\n"
        
        selection_text += f"Please reply with the number of the person you'd like to meet (**1-{len(persons)}**)."
        
        return selection_text
    
    def get_person_by_selection(self, selection: int, party_type: str = None) -> Optional[MarketingPerson]:
        """Get person by selection number (1-based)"""
        party_type = party_type or self.current_party_type
        persons = self.get_persons_by_party_type(party_type)
        
        if 1 <= selection <= len(persons):
            return persons[selection - 1]
        return None

# Convenience functions for easy import
def get_marketing_persons_list(party_type: str = 'MKTG') -> str:
    """Get formatted list of persons by party_type for bot display"""
    api = MarketingPersonsAPI(party_type=party_type)
    return api.format_selection_list(party_type)

def get_marketing_person_info_by_selection(selection: int, party_type: str = 'MKTG') -> Optional[Dict]:
    """Get full person info by selection number and party_type"""
    api = MarketingPersonsAPI(party_type=party_type)
    person = api.get_person_by_selection(selection, party_type)
    if person:
        return {
            'id': person.id,
            'name': person.name,
            'email': person.email,
            'phone': person.phone,
            'timezone': person.timezone,
            'specialization': person.specialization,
            'availability_note': person.availability_note
        }
    return None

def get_persons_list_by_type(party_type: str) -> str:
    """Get formatted list of persons by any party_type"""
    return get_marketing_persons_list(party_type)

def detect_party_type_from_message(message: str) -> Optional[str]:
    """
    Detect which party_type the user wants based on their message.
    
    Returns:
        'MKTG' for marketing requests
        'Business' for business requests
        'Individual' for individual requests
        None if no match
    """
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['marketing', 'mktg']):
        return 'MKTG'
    elif any(word in message_lower for word in ['business', 'enterprise', 'corporate']):
        return 'Business'
    elif any(word in message_lower for word in ['individual', 'personal']):
        return 'Individual'
    
    return None


def get_customer_name_by_email(email: str) -> Optional[str]:
    """
    Look up customer name from database by email address.
    
    Args:
        email: Customer's email address
        
    Returns:
        Customer's full name or None if not found
    """
    if not email:
        return None
        
    try:
        from app.database import SessionLocal
        from app.models.database_models import Customer
        
        db = SessionLocal()
        customer = db.query(Customer).filter(Customer.email == email).first()
        
        if customer:
            first_name = customer.first_name or ""
            last_name = customer.last_name or ""
            full_name = f"{first_name} {last_name}".strip()
            db.close()
            
            if full_name:
                print(f"✅ Found customer name for {email}: {full_name}")
                return full_name
        
        db.close()
        print(f"⚠️ No customer found in database for email: {email}")
        return None
        
    except Exception as e:
        print(f"❌ Error looking up customer by email: {e}")
        return None


def get_customer_phone_by_email(email: str) -> Optional[str]:
    """
    Look up customer phone number from database by email address.
    
    Args:
        email: Customer's email address
        
    Returns:
        Customer's phone number or None if not found
    """
    if not email:
        return None
        
    try:
        from app.database import SessionLocal
        from app.models.database_models import Customer
        
        db = SessionLocal()
        customer = db.query(Customer).filter(Customer.email == email).first()
        
        if customer and customer.phone:
            phone = customer.phone
            db.close()
            print(f"✅ Found customer phone for {email}: {phone}")
            return phone
        
        db.close()
        print(f"⚠️ No phone number found in database for email: {email}")
        return None
        
    except Exception as e:
        print(f"❌ Error looking up customer phone by email: {e}")
        return None


def get_customer_telegram_chat_id(email: str) -> Optional[int]:
    """
    Look up customer Telegram chat ID from database by email address.
    
    Args:
        email: Customer's email address
        
    Returns:
        Customer's Telegram chat ID (int) or None if not found/not registered
    """
    if not email:
        return None
        
    try:
        from app.database import SessionLocal
        from app.models.database_models import Customer
        
        db = SessionLocal()
        customer = db.query(Customer).filter(Customer.email == email).first()
        
        if customer and customer.telegram_chat_id:
            chat_id = customer.telegram_chat_id
            db.close()
            print(f"✅ Found Telegram chat_id for {email}: {chat_id}")
            return chat_id
        
        db.close()
        print(f"⚠️ No Telegram chat_id found for {email}")
        return None
        
    except Exception as e:
        print(f"❌ Error looking up Telegram chat_id by email: {e}")
        return None
