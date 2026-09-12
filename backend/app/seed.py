"""
Load 3 demo services if the database is empty:

  Payment Service  -->  Auth Service  -->  Database Service
"""

from sqlalchemy.orm import Session

from . import crud, models


DEMO_SERVICES = [
    {
        "name": "Database Service",
        "service_type": "database",
        "description": "Stores user and application data.",
        "connects_to": [],
    },
    {
        "name": "Auth Service",
        "service_type": "auth",
        "description": "Handles login, sessions, and identity.",
        "connects_to": ["Database Service"],
    },
    {
        "name": "Payment Service",
        "service_type": "payment",
        "description": "Processes customer payments.",
        "connects_to": ["Auth Service"],
    },
]


def seed_if_empty(db: Session) -> None:
    count = db.query(models.Service).count()
    if count > 0:
        return

    # Create Database first so Auth can connect to it, then Payment.
    for item in DEMO_SERVICES:
        crud.create_service(
            db=db,
            name=item["name"],
            service_type=item["service_type"],
            description=item["description"],
            connects_to=item["connects_to"],
        )
