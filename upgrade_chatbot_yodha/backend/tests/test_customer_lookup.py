"""
Tests for customer_lookup service.
"""

from app.models import Customer, Product, Sales
from app.services.customer_lookup import find_customer, get_purchases, get_marketing_persons


def _seed(db):
    """Insert minimal test data."""
    c = Customer(
        customer_id=1,
        party_type="Individual",
        first_name="Alice",
        last_name="Test",
        email="alice@test.com",
        phone="555-1234",
    )
    p = Product(product_id=1, product_name="Widget Pro", version="1.0", price=99.99)
    db.add_all([c, p])
    db.flush()

    s = Sales(sale_id=1, customer_id=1, product_id=1, quantity=2, total_amount=199.98)
    db.add(s)
    db.flush()

    mktg = Customer(
        customer_id=10,
        party_type="MKTG",
        first_name="Mark",
        last_name="Eter",
        email="mark@mktg.com",
    )
    db.add(mktg)
    db.flush()


def test_find_customer_by_email(db):
    _seed(db)
    result = find_customer(db, email="alice@test.com")
    assert result is not None
    assert result["first_name"] == "Alice"


def test_find_customer_not_found(db):
    _seed(db)
    result = find_customer(db, email="nobody@test.com")
    assert result is None


def test_get_purchases(db):
    _seed(db)
    purchases, has_more = get_purchases(db, customer_id=1)
    assert len(purchases) == 1
    assert purchases[0]["product_name"] == "Widget Pro"
    assert not has_more


def test_get_marketing_persons(db):
    _seed(db)
    persons = get_marketing_persons(db)
    assert len(persons) == 1
    assert persons[0]["first_name"] == "Mark"
