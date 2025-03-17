import os

import boto3
from fastapi import APIRouter, UploadFile, File

router = APIRouter(
    prefix="/Files",
    tags=["filesForCourse"],
)

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

s3 = boto3.client('s3',
                  aws_access_key_id=os.environ.get('ACCESS_KEY_ID'),
                  aws_secret_access_key=os.environ.get('SECRET_ACCESS_KEY'),
                  )
BUCKET_NAME='files-for-team-project'

@router.get('/all')
async def get_all_files():
    res = s3.list_objects_v2(Bucket=BUCKET_NAME)
    print(res)
    return res

@router.post('/upload')
async def upload_file(file: UploadFile = File(...)):
    if file:
        print(file.filename)
        s3.upload_file(file.filename, BUCKET_NAME, file.filename)
        return "File Uploaded"
    else:
        return "Error in uploading"
