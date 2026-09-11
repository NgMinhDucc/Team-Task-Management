from fastapi import Depends, HTTPException, status
from typing import Annotated
from sqlmodel import Session, SQLModel, create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(DATABASE_URL)
if DATABASE_URL:
    engine = create_engine(DATABASE_URL, echo=True)

    def create_database_and_tables():
        SQLModel.metadata.create_all(engine)
        
    def get_session():
        with Session(engine) as session:
            yield session
            
    SessionDep = Annotated[Session, Depends(get_session)]
    
else:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=
        """
        Sorry for this inconvenience.
        Here's some coffee for you to enjoy while we're working on these errors.
        """
    )