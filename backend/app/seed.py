from passlib.context import CryptContext
from sqlalchemy import select
from .database import Base, SessionLocal, engine
from .models import Dataset, Project, TestCase, User

CASES = [
    ("Patient started metformin 500 mg twice daily.", {"medications": ["metformin"]}, ["diabetes"]),
    ("Continue lisinopril; discontinue aspirin.", {"medications": ["lisinopril", "aspirin"]}, ["cardiology"]),
    ("No current medications reported.", {"medications": []}, ["negative"]),
    ("Atorvastatin and insulin are listed in the medication history.", {"medications": ["atorvastatin", "insulin"]}, ["multiple"]),
    ("Begin amoxicillin for seven days.", {"medications": ["amoxicillin"]}, ["antibiotic"]),
]


def seed():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == "demo@evalforge.dev")): return
        user = User(email="demo@evalforge.dev", name="Demo Engineer", password_hash=CryptContext(schemes=["pbkdf2_sha256"]).hash("demo1234"))
        db.add(user); db.flush()
        project = Project(name="Clinical NLP Quality", description="Synthetic medication extraction evaluation", owner_id=user.id)
        db.add(project); db.flush()
        dataset = Dataset(name="Medication Extraction", description="Public-safe synthetic clinical notes", project_id=project.id)
        db.add(dataset); db.flush()
        db.add_all([TestCase(dataset_id=dataset.id, input=text, expected_output=expected, tags=tags) for text, expected, tags in CASES])
        db.commit()
        print("Seeded demo@evalforge.dev / demo1234")


if __name__ == "__main__": seed()
