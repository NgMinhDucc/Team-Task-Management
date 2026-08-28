from fastapi import Depends
from typing import Annotated
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "postgresql://postgres:minhhducc7206@localhost/Team Task Management"
engine = create_engine(DATABASE_URL, echo=True)

def create_database_and_tables():
    SQLModel.metadata.create_all(engine)
    
def get_session():
    with Session(engine) as session:
        yield session
        
SessionDep = Annotated[Session, Depends(get_session)]