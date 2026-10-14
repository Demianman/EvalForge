from passlib.context import CryptContext
from sqlalchemy import select
from .database import Base, SessionLocal, engine
import hashlib
from .models import Dataset, Project, RagChunk, RagDocument, TestCase, User
from .rag import chunk_text, embed, tokenize

CASES = [
    ("Patient started metformin 500 mg twice daily.", {"medications": ["metformin"]}, ["diabetes"]),
    ("Continue lisinopril; discontinue aspirin.", {"medications": ["lisinopril", "aspirin"]}, ["cardiology"]),
    ("No current medications reported.", {"medications": []}, ["negative"]),
    ("Atorvastatin and insulin are listed in the medication history.", {"medications": ["atorvastatin", "insulin"]}, ["multiple"]),
    ("Begin amoxicillin for seven days.", {"medications": ["amoxicillin"]}, ["antibiotic"]),
]

RAG_GUIDE = """Metformin is commonly used to manage type 2 diabetes. Renal function should be reviewed when evaluating medication safety. Lisinopril may be used for blood pressure management, with potassium and kidney function monitoring. This entirely synthetic educational guide is not medical advice and must not be used for clinical decisions."""


def seed():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "demo@evalforge.dev"))
        if not user:
            user = User(email="demo@evalforge.dev", name="Demo Engineer", password_hash=CryptContext(schemes=["pbkdf2_sha256"]).hash("demo1234"))
            db.add(user); db.flush()
        project = db.scalar(select(Project).where(Project.owner_id == user.id, Project.name == "Clinical NLP Quality"))
        if not project:
            project = Project(name="Clinical NLP Quality", description="Synthetic medication extraction and RAG evaluation", owner_id=user.id)
            db.add(project); db.flush()
        dataset = db.scalar(select(Dataset).where(Dataset.project_id == project.id, Dataset.name == "Medication Extraction"))
        if not dataset:
            dataset = Dataset(name="Medication Extraction", description="Public-safe synthetic clinical notes", project_id=project.id)
            db.add(dataset); db.flush()
            db.add_all([TestCase(dataset_id=dataset.id, input=text, expected_output=expected, tags=tags) for text, expected, tags in CASES])
        digest = hashlib.sha256(RAG_GUIDE.encode()).hexdigest()
        document = db.scalar(select(RagDocument).where(RagDocument.project_id == project.id, RagDocument.content_sha256 == digest))
        if not document:
            document = RagDocument(project_id=project.id, title="Synthetic medication safety guide", source_uri="fixture://synthetic-medication-guide", content_sha256=digest)
            db.add(document); db.flush()
            chunks = chunk_text(RAG_GUIDE, 24, 6)
            db.add_all([RagChunk(document_id=document.id, position=index, content=content, token_set=sorted(set(tokenize(content))), embedding=embed(content), chunk_metadata={"chunk_size": 24, "chunk_overlap": 6}) for index, content in enumerate(chunks)])
        db.commit()
        print("Seeded demo@evalforge.dev / demo1234")


if __name__ == "__main__": seed()
