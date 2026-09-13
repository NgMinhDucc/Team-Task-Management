from fastapi import APIRouter, HTTPException, status

from auth import CurrentUser
from database import SessionDep
import models.comments as mc

router = APIRouter(prefix="/comments")

@router.post("/create-comments")
async def create_comments(session: SessionDep, current_user: CurrentUser, create_comment: mc.CreateComment):
    comment_data = create_comment.model_dump()
    new_comment = mc.Comments(**comment_data)
    
    session.add(new_comment)
    session.commit()
    session.refresh(new_comment)
    
    return "comment created successfully"