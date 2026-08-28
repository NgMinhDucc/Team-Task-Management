from fastapi import FastAPI

from database import create_database_and_tables
import routers.users as users
import routers.projects as projects
import routers.tasks as tasks
import routers.comments as comments

create_database_and_tables()

app = FastAPI()
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(comments.router)