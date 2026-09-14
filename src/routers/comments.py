from fastapi import APIRouter, HTTPException, status

from auth import CurrentUser
from database import SessionDep
from models import Comments, CreateComment

router = APIRouter(prefix="/comments")

@router.post("/create-comments")
async def create_comments(session: SessionDep, current_user: CurrentUser, create_comment: CreateComment):
    comment_data = create_comment.model_dump()
    new_comment = Comments(**comment_data)
    
    session.add(new_comment)
    session.commit()
    session.refresh(new_comment)
    
    return "comment created successfully"