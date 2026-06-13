"""Tests for Category model and hierarchy functionality."""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.base import Base
from backend.db.models.category import Category


@pytest.fixture
def session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_category_creation(session):
    """Test creating a basic category."""
    cat = Category(
        id=uuid4(),
        name="Groceries",
        description="Grocery shopping",
        monarch_name="Groceries",
        color="#FF5733",
        icon="shopping-cart",
    )
    session.add(cat)
    session.commit()

    retrieved = session.query(Category).filter_by(name="Groceries").first()
    assert retrieved is not None
    assert retrieved.name == "Groceries"
    assert retrieved.monarch_name == "Groceries"
    assert retrieved.color == "#FF5733"


def test_category_hierarchy(session):
    """Test parent-child category relationships."""
    expenses = Category(
        id=uuid4(),
        name="Expenses",
        description="All expenses",
    )
    session.add(expenses)
    session.flush()

    groceries = Category(
        id=uuid4(),
        name="Groceries",
        parent_category_id=expenses.id,
        monarch_name="Groceries",
    )
    session.add(groceries)
    session.commit()

    # Retrieve and verify hierarchy
    retrieved_expenses = session.query(Category).filter_by(name="Expenses").first()
    assert len(retrieved_expenses.children) == 1
    assert retrieved_expenses.children[0].name == "Groceries"

    retrieved_groceries = session.query(Category).filter_by(name="Groceries").first()
    assert retrieved_groceries.parent is not None
    assert retrieved_groceries.parent.name == "Expenses"


def test_category_get_path(session):
    """Test getting full category path."""
    root = Category(id=uuid4(), name="Root")
    session.add(root)
    session.flush()

    middle = Category(id=uuid4(), name="Middle", parent_category_id=root.id)
    session.add(middle)
    session.flush()

    leaf = Category(id=uuid4(), name="Leaf", parent_category_id=middle.id)
    session.add(leaf)
    session.commit()

    retrieved_leaf = session.query(Category).filter_by(name="Leaf").first()
    path = retrieved_leaf.get_path()
    assert len(path) == 3
    assert [c.name for c in path] == ["Root", "Middle", "Leaf"]


def test_category_get_path_str(session):
    """Test formatted path string."""
    root = Category(id=uuid4(), name="Expenses")
    session.add(root)
    session.flush()

    child = Category(id=uuid4(), name="Dining Out", parent_category_id=root.id)
    session.add(child)
    session.commit()

    retrieved = session.query(Category).filter_by(name="Dining Out").first()
    path_str = retrieved.get_path_str()
    assert path_str == "Expenses > Dining Out"


def test_category_is_root(session):
    """Test root category detection."""
    root = Category(id=uuid4(), name="Root")
    session.add(root)
    session.flush()

    child = Category(id=uuid4(), name="Child", parent_category_id=root.id)
    session.add(child)
    session.commit()

    retrieved_root = session.query(Category).filter_by(name="Root").first()
    retrieved_child = session.query(Category).filter_by(name="Child").first()

    assert retrieved_root.is_root()
    assert not retrieved_child.is_root()


def test_category_is_leaf(session):
    """Test leaf category detection."""
    root = Category(id=uuid4(), name="Root")
    session.add(root)
    session.flush()

    child = Category(id=uuid4(), name="Child", parent_category_id=root.id)
    session.add(child)
    session.commit()

    retrieved_root = session.query(Category).filter_by(name="Root").first()
    retrieved_child = session.query(Category).filter_by(name="Child").first()

    assert not retrieved_root.is_leaf()
    assert retrieved_child.is_leaf()


def test_category_descendants(session):
    """Test getting all descendant categories."""
    root = Category(id=uuid4(), name="Expenses")
    session.add(root)
    session.flush()

    food = Category(id=uuid4(), name="Food", parent_category_id=root.id)
    session.add(food)
    session.flush()

    groceries = Category(id=uuid4(), name="Groceries", parent_category_id=food.id)
    session.add(groceries)
    session.flush()

    dining = Category(id=uuid4(), name="Dining Out", parent_category_id=food.id)
    session.add(dining)
    session.commit()

    retrieved_root = session.query(Category).filter_by(name="Expenses").first()
    descendants = retrieved_root.get_descendants()

    assert len(descendants) == 3
    names = {d.name for d in descendants}
    assert names == {"Food", "Groceries", "Dining Out"}
