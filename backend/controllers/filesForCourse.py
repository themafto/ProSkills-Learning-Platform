from fastapi import APIRouter, UploadFile, File

from backend.main import BUCKET_NAME, s3

router = APIRouter(
    prefix="/Files",
    tags=["filesForCourse"],
)

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
