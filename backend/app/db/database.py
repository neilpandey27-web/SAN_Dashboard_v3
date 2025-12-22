"""
Database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Create engine based on database URL
# SQLite needs check_same_thread=False for FastAPI
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,   # Check connections before use
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Ensures the session is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables.
    Should be called on application startup.
    """
    from app.db import models  # Import models to register them
    Base.metadata.create_all(bind=engine)
    
    # Seed initial data
    db = SessionLocal()
    try:
        _seed_initial_data(db)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding initial data: {e}")
    finally:
        db.close()


def _seed_initial_data(db):
    """Seed initial tenants and admin user if they don't exist."""
    from app.db.models import Tenant, User
    from app.core.security import hash_password
    
    # Seed tenants
    tenant_names = [
        ("BTC", "BTC"),
        ("HMC", "HMC"),
        ("ISST", "Infrastructure Services"),
        ("HST", "Hosted Services"),
        ("PERFORMANCE", "Performance"),
        ("UNKNOWN", "Unknown"),
    ]
    
    for name, description in tenant_names:
        existing = db.query(Tenant).filter(Tenant.name == name).first()
        if not existing:
            tenant = Tenant(name=name, description=description)
            db.add(tenant)
            print(f"Created tenant: {name}")
    
    db.flush()  # Ensure tenants have IDs
    
    # Seed admin user
    admin_email = "admin@company.com"
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    
    if not existing_admin:
        admin = User(
            username="admin",
            first_name="System",
            last_name="Administrator",
            email=admin_email,
            password_hash=hash_password("admin123"),
            role="admin",
            status="active"
        )
        db.add(admin)
        print(f"Created admin user: admin / {admin_email}")
