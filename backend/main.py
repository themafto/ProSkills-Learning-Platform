import os

import boto3
from fastapi import FastAPI
from backend.controllers import auth, courses, students, assignments
from backend.database import Base, engine
from backend.middlewares.cors import setup_cors

app = FastAPI()



from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

s3 = boto3.client('s3',
                  aws_access_key_id=os.environ.get('ACCESS_KEY_ID'),
                  aws_secret_access_key=os.environ.get('SECRET_ACCESS_KEY'),
                  )
BUCKET_NAME='team-project-backet'
setup_cors(app)
Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(students.router)
app.include_router(assignments.router)

