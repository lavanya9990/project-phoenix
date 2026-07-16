import os
os.environ["DATABASE_URL"]="sqlite:///./test.db"
import pytest
from fastapi.testclient import TestClient
from app.database import Base,engine
from app.main import app
@pytest.fixture(autouse=True)
def database():
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine); yield; Base.metadata.drop_all(engine)
@pytest.fixture
def client(): return TestClient(app)
@pytest.fixture
def payload(): return {"full_name":"Rahul Sharma","email":"rahul@example.com","phone":"9876543210","company_name":"Bright Smile","business_type":"Dental clinic","enquiry":"We need an AI chatbot and appointment reminder system.","estimated_budget":"INR 40,000","preferred_timeline":"Within one month"}
