#!/usr/bin/env python3
"""
Marketing Persons API - With fallback for offline testing
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class MarketingPerson:
    """Data class for marketing person information"""
    id: int
    name: str
    email: str
    phone: str
    timezone: str
    specialization: str
    availability_note: str

class MarketingPersonsAPI:
    """API for marketing persons with fallback when database unavailable"""
    
    def __init__(self):
        """Initialize API"""
        self.fallback_mode = False
        try:
            self._ensure_marketing_persons_exist()
        except Exception as e:
            print(f"⚠️ Database unavailable, using fallback data: {e}")
            self.fallback_mode = True
    
    def _get_db_session(self) -> Session:
        """Get database session"""
        from app.database import SessionLocal
        return SessionLocal()
    
    def _ensure_marketing_persons_exist(self):
        """Ensure we have marketing persons in the Customer table"""
        from app.models.database_models import Customer
        
        db = self._get_db_session()
        try:
            # Test database connection
            db.execute("SELECT 1")
            db.close()
        except Exception:
            db.close()
            raise Exception("Database connection failed")
    
    def _get_fallback_persons(self) -> List[MarketingPerson]:
        """Get fallback marketing persons when database is unavailable"""
        return [
            MarketingPerson(
                id=1,
                name="Kartheek DS",
                email="nagakartheek.ds@gmail.com",
                phone="+91-9876543210",
                timezone="Asia/Kolkata",
                specialization="Product Demos & Technical Consultations",
                availability_note="Available Monday-Friday, 9 AM - 6 PM IST"
            ),
            MarketingPerson(
                id=2,
                name="Raju T",
                email="raju.t@uslocumservices.com",
                phone="+91-9876543211",
                timezone="Asia/Kolkata",
                specialization="Business Development & Enterprise Sales",
                availability_note="Available Monday-Saturday, 10 AM - 7 PM IST"
            ),
            MarketingPerson(
                id=3,
                name="Malee",
                email="malee@uslocumservices.com",
                phone="+1-555-123-4567",
                timezone="America/New_York",
                specialization="International Sales & Partnerships",
                availability_note="Available Monday-Friday, 9 AM - 5 PM EST"
            )
        ]
    
    def get_active_marketing_persons(self) -> List[MarketingPerson]:
        """Get all active marketing persons"""
        if self.fallback_mode:
            return self._get_fallback_persons()
        
        # Database logic would go here
        try:
            from app.models.database_models import Customer
            db = self._get_db_session()
            
            marketing_emails = [
                "nagakartheek.ds@gmail.com",
                "raju.t@uslocumservices.com", 
                "malee@uslocumservices.com"
            ]
            
            customers = db.query(Customer).filter(Customer.email.in_(marketing_emails)).all()
            
            specializations = {
                "nagakartheek.ds@gmail.com": "Product Demos & Technical Consultations",
                "raju.t@uslocumservices.com": "Business Development & Enterprise Sales", 
                "malee@uslocumservices.com": "International Sales & Partnerships"
            }
            
            availability_notes = {
                "nagakartheek.ds@gmail.com": "Available Monday-Friday, 9 AM - 6 PM IST",
                "raju.t@uslocumservices.com": "Available Monday-Saturday, 10 AM - 7 PM IST",
                "malee@uslocumservices.com": "Available Monday-Friday, 9 AM - 5 PM EST"
            }
            
            timezones = {
                "nagakartheek.ds@gmail.com": "Asia/Kolkata",
                "raju.t@uslocumservices.com": "Asia/Kolkata",
                "malee@uslocumservices.com": "America/New_York"
            }
            
            marketing_persons = []
            for customer in customers:
                person = MarketingPerson(
                    id=customer.customer_id,
                    name=f"{customer.first_name} {customer.last_name}",
                    email=customer.email,
                    phone=customer.phone or "N/A",
                    timezone=timezones.get(customer.email, "Asia/Kolkata"),
                    specialization=specializations.get(customer.email, "General Sales & Support"),
                    availability_note=availability_notes.get(customer.email, "Available during business hours")
                )
                marketing_persons.append(person)
            
            marketing_persons.sort(key=lambda x: x.name)
            db.close()
            return marketing_persons
            
        except Exception:
            return self._get_fallback_persons()
    
    def get_marketing_person_by_email(self, email: str) -> Optional[MarketingPerson]:
        """Get marketing person by email address"""
        persons = self.get_active_marketing_persons()
        for person in persons:
            if person.email == email:
                return person
        return None
    
    def format_selection_list(self) -> str:
        """Format marketing persons as a selection list for the bot"""
        persons = self.get_active_marketing_persons()
        
        if not persons:
            return "❌ No marketing team members available at the moment."
        
        selection_text = "🏢 **Our Marketing Team:**\n\n"
        
        for i, person in enumerate(persons, 1):
            selection_text += f"**{i}. {person.name}** 👤\n"
            if person.specialization:
                selection_text += f"   🎯 {person.specialization}\n"
            selection_text += "\n"
        
        selection_text += f"Please reply with the number of the person you'd like to meet (**1-{len(persons)}**)."
        
        return selection_text
    
    def get_person_by_selection(self, selection: int) -> Optional[MarketingPerson]:
        """Get marketing person by selection number (1-based)"""
        persons = self.get_active_marketing_persons()
        
        if 1 <= selection <= len(persons):
            return persons[selection - 1]
        return None

# Convenience functions for easy import
def get_marketing_persons_list() -> str:
    """Get formatted list of marketing persons for bot display"""
    api = MarketingPersonsAPI()
    return api.format_selection_list()

def get_marketing_person_info_by_selection(selection: int) -> Optional[Dict]:
    """Get full marketing person info by selection number"""
    api = MarketingPersonsAPI()
    person = api.get_person_by_selection(selection)
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
