import os
from typing import List, Optional
import uuid
import re
from datetime import datetime

import boto3
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from starlette import status

from backend.dependencies.getdb import get_db
from backend.oauth2 import get_current_user_jwt
from backend.models import Course, Assignment, Enrollment
from backend.schemas.file import FileResponse as FileResponseSchema, FileUploadResponse, FileDeleteResponse

router = APIRouter(
    prefix="/files",
    tags=["files"],
)

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

s3 = boto3.client('s3',
                  aws_access_key_id=os.environ.get('ACCESS_KEY_ID'),
                  aws_secret_access_key=os.environ.get('SECRET_ACCESS_KEY'),
                  region_name=os.environ.get('AWS_REGION', 'us-east-1')
                  )
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'files-for-team-project')
TEMP_DOWNLOAD_DIR = "temp_downloads"

# Ensure temp directory exists
os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)

# File size limits (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_CONTENT_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/zip',
    'text/plain',
    'text/csv',
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/x-python-code',
    'text/x-python',
    'application/json',
    'application/xml',
    'text/markdown'
]

# Helper function to check file type and size
async def validate_file(file: UploadFile):
    # Check if file exists
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Check content type
    content_type = file.content_type
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {content_type} not allowed"
        )
    
    # Check file size
    try:
        # Read first chunk to check size without loading entire file
        first_chunk = await file.read(MAX_FILE_SIZE + 1)
        if len(first_chunk) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024)} MB"
            )
        
        # Reset file position for later reading
        await file.seek(0)
        return first_chunk
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating file: {str(e)}"
        )

# Helper function to check course enrollment
def check_enrollment(db: Session, user_id: int, course_id: int) -> bool:
    return db.query(Enrollment).filter(
        Enrollment.student_id == user_id,
        Enrollment.course_id == course_id
    ).first() is not None

# Helper function to check course ownership
def check_course_ownership(db: Session, user_id: int, course_id: int) -> bool:
    return db.query(Course).filter(
        Course.id == course_id,
        Course.teacher_id == user_id
    ).first() is not None

@router.get('', response_model=List[FileResponseSchema])
async def get_all_files(
    course_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user_jwt),
    db: Session = Depends(get_db)
):
    """
    Get all files or files for a specific course
    """
    try:
        user_id = current_user.get("user_id")
        user_role = current_user.get("role")
        
        # If course_id provided, verify course exists and user has access
        if course_id:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="Course not found"
                )
            
            # Verify user has permission to view course files
            if user_role not in ['teacher', 'admin'] and \
               not check_course_ownership(db, user_id, course_id) and \
               not check_enrollment(db, user_id, course_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Not authorized to view files for this course"
                )
                
            # Filter by course prefix in S3
            prefix = f"course_{course_id}/"
            response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        else:
            # For non-admin/teacher users, only show files from their courses
            if user_role not in ['teacher', 'admin']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view all files"
                )
                
            # Get all files
            response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        
        if 'Contents' not in response:
            return []
            
        files = []
        for item in response.get('Contents', []):
            files.append(FileResponseSchema(
                key=item['Key'],
                size=item['Size'],
                last_modified=item['LastModified'],
                etag=item['ETag']
            ))
        return files
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving files: {str(e)}"
        )

@router.post('/upload', response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    course_id: Optional[int] = Form(None),
    current_user: dict = Depends(get_current_user_jwt),
    db: Session = Depends(get_db)
):
    """
    Upload a file to S3
    """
    try:
        # Validate file
        file_content = await validate_file(file)
        
        user_id = current_user.get("user_id")
        user_role = current_user.get("role")
        
        # If course_id provided, verify course exists and user has permissions
        if course_id:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="Course not found"
                )
            
            # Verify user has permission to upload to this course
            if user_role not in ['teacher', 'admin'] and \
               not check_course_ownership(db, user_id, course_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Not authorized to upload to this course"
                )
                
            # Create a prefix for this course
            key = f"course_{course_id}/{uuid.uuid4().hex}_{file.filename}"
        else:
            # Only admins and teachers can upload general files
            if user_role not in ['teacher', 'admin']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to upload general files"
                )
                
            # Generate a unique filename with a folder structure to avoid collisions
            timestamp = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
            key = f"general/{timestamp}/{unique_filename}"
            
        # Upload directly from memory to S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=file_content,
            ContentType=file.content_type
        )
        
        return FileUploadResponse(
            message="File uploaded successfully", 
            file_key=key
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

@router.post('/assignments/{assignment_id}/upload', response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_assignment_file(
    assignment_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_jwt),
    db: Session = Depends(get_db)
):
    """
    Upload a file for a specific assignment
    """
    try:
        # Validate file
        file_content = await validate_file(file)
        
        user_id = current_user.get("user_id")
        user_role = current_user.get("role")
        
        # Check if assignment exists
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        
        # Check course access permissions
        course = db.query(Course).filter(Course.id == assignment.course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        # For tasks, only teacher can upload
        if user_role not in ['teacher', 'admin'] and course.teacher_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload task files"
            )
            
        # Create a structured key for assignments with uniqueness
        key = f"assignments/{assignment_id}/task/{uuid.uuid4().hex}_{file.filename}"
        
        # Upload directly from memory to S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=file_content,
            ContentType=file.content_type
        )
        
        return FileUploadResponse(
            message="Assignment file uploaded successfully",
            file_key=key
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading assignment file: {str(e)}"
        )

@router.post('/assignments/{assignment_id}/submit', response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def submit_assignment(
    assignment_id: int,
    file: UploadFile = File(...),
    comment: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user_jwt),
    db: Session = Depends(get_db)
):
    """
    Submit a solution for an assignment
    """
    try:
        # Validate file
        file_content = await validate_file(file)
        
        user_id = current_user.get("user_id")
        user_role = current_user.get("role")
        
        # Check if assignment exists
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        
        # Get the associated course and verify enrollment
        course = db.query(Course).filter(Course.id == assignment.course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
            
        # For students, check if they're enrolled in the course
        if user_role == 'student' and not check_enrollment(db, user_id, course.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this course"
            )
        
        # Create a structured key for submissions with timestamp for versioning
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        key = f"assignments/{assignment_id}/submissions/{user_id}/{timestamp}_{file.filename}"
        
        # Upload directly from memory to S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=file_content,
            ContentType=file.content_type,
            Metadata={
                'comment': comment if comment else '',
                'timestamp': timestamp
            }
        )
        
        # Update or create submission record in database
        # This would require a Submission model that you should implement
        # Example:
        # submission = Submission(
        #     assignment_id=assignment_id,
        #     student_id=user_id,
        #     submitted_at=datetime.now(),
        #     file_key=key,
        #     comment=comment
        # )
        # db.add(submission)
        # db.commit()
        
        return FileUploadResponse(
            message="Assignment submission successful",
            file_key=key
        )
    
    except HTTPException:
        raise  
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting assignment: {str(e)}"
        )

@router.get('/assignments/{assignment_id}/task', response_model=List[FileResponseSchema])
async def get_assignment_files(
    assignment_id: int,
    current_user: dict = Depends(get_current_user_jwt),
    db: Session = Depends(get_db)
):
    """
    Get files for a specific assignment task
    """
    try:
        user_id = current_user.get("user_id")
        user_role = current_user.get("role")
        
        # Check if assignment exists
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
            
        # Get the associated course
        course = db.query(Course).filter(Course.id == assignment.course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
            
        # Verify access permissions
        if user_role not in ['teacher', 'admin'] and \
           course.teacher_id != user_id and \
           not check_enrollment(db, user_id, course.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view assignment files"
            )
        
        # Filter by assignment prefix in S3
        prefix = f"assignments/{assignment_id}/task/"
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        
        if 'Contents' not in response:
            return []
            
        files = []
        for item in response.get('Contents', []):
            files.append(FileResponseSchema(
                key=item['Key'],
                size=item['Size'],
                last_modified=item['LastModified'],
                etag=item['ETag']
            ))
        return files
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assignment files: {str(e)}"
        )

@router.get('/assignments/{assignment_id}/submissions', response_model=List[FileResponseSchema])
async def get_assignment_submissions(
    assignment_id: int,
    student_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user_jwt),
    db: Session = Depends(get_db)
):
    """
    Get submissions for a specific assignment
    """
    try:
        user_id = current_user.get("user_id")
        user_role = current_user.get("role")
        
        # Check if assignment exists
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
            
        # Get the associated course
        course = db.query(Course).filter(Course.id == assignment.course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
            
        # Teachers and admins can see all submissions, students can only see their own
        if user_role in ['teacher', 'admin'] or course.teacher_id == user_id:
            # Teacher can see all submissions or filter by student
            prefix = f"assignments/{assignment_id}/submissions/"
            if student_id:
                prefix = f"{prefix}{student_id}/"
        elif user_role == 'student':
            # Students can only see their own submissions
            if student_id and student_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other student submissions"
                )
                
            # Check if student is enrolled in the course
            if not check_enrollment(db, user_id, course.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not enrolled in this course"
                )
                
            prefix = f"assignments/{assignment_id}/submissions/{user_id}/"
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view submissions"
            )
            
        # Get submissions from S3
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        
        if 'Contents' not in response:
            return []
            
        files = []
        for item in response.get('Contents', []):
            files.append(FileResponseSchema(
                key=item['Key'],
                size=item['Size'],
                last_modified=item['LastModified'],
                etag=item['ETag']
            ))
        return files
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assignment submissions: {str(e)}"
        )

@router.get('/download/{file_key:path}')
async def download_file(
    file_key: str,
    current_user: dict = Depends(get_current_user_jwt),
    db: Session = Depends(get_db)
):
    """
    Download a file from S3 with proper authorization
    """
    try:
        # Check if file exists
        try:
            s3.head_object(Bucket=BUCKET_NAME, Key=file_key)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Implement authorization based on file path pattern
        user_id = current_user.get("user_id")
        user_role = current_user.get("role")
        
        # Case 1: Assignment task files
        if file_key.startswith("assignments/") and "/task/" in file_key:
            # Extract assignment ID from the path
            match = re.match(r"assignments/(\d+)/task/", file_key)
            if not match:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid assignment file path"
                )
                
            assignment_id = int(match.group(1))
            
            # Check if assignment exists
            assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignment not found"
                )
            
            # Check course access
            course = db.query(Course).filter(Course.id == assignment.course_id).first()
            if not course:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course not found"
                )
            
            # Teachers and admins have access to all assignment tasks
            if user_role in ['teacher', 'admin'] or course.teacher_id == user_id:
                pass  # Allow access
            # For students, check if they're enrolled in the course
            elif user_role == 'student':
                if not check_enrollment(db, user_id, course.id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are not enrolled in this course"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this file"
                )
                
        # Case 2: Assignment submission files
        elif file_key.startswith("assignments/") and "/submissions/" in file_key:
            # Extract IDs from path
            match = re.match(r"assignments/(\d+)/submissions/(\d+)/", file_key)
            if not match:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid submission file path"
                )
                
            assignment_id = int(match.group(1))
            submission_student_id = int(match.group(2))
            
            # Check if assignment exists
            assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignment not found"
                )
            
            # Get the associated course
            course = db.query(Course).filter(Course.id == assignment.course_id).first()
            if not course:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course not found"
                )
            
            # Teachers and admins can access all submissions
            if user_role in ['teacher', 'admin'] or course.teacher_id == user_id:
                pass  # Allow access
            # Students can only access their own submissions
            elif user_role == 'student' and user_id == submission_student_id:
                # Verify enrollment
                if not check_enrollment(db, user_id, course.id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are not enrolled in this course"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this submission"
                )
                
        # Case 3: Course files
        elif file_key.startswith("course_"):
            # Extract course ID using regex
            match = re.match(r"course_(\d+)/", file_key)
            if not match:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid course file path"
                )
                
            course_id = int(match.group(1))
            
            # Check if course exists
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course not found"
                )
            
            # Verify access permissions
            if user_role in ['teacher', 'admin'] or course.teacher_id == user_id:
                pass  # Allow access
            elif user_role == 'student':
                # Check enrollment
                if not check_enrollment(db, user_id, course_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are not enrolled in this course"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this file"
                )
        
        # Case 4: General files (admin/teachers only)
        elif user_role not in ['admin', 'teacher']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this file"
            )
        
        # Create a download response
        try:
            response = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
            
            # Extract the filename from the key
            filename = file_key.split('/')[-1]
            # Remove UUID if present (format: uuid_filename.ext)
            if '_' in filename and len(filename.split('_')[0]) == 32:
                filename = '_'.join(filename.split('_')[1:])
            
            # Get content type, defaulting to octet-stream if not specified
            content_type = response.get('ContentType', 'application/octet-stream')
            
            # Return a streaming response
            return StreamingResponse(
                content=response['Body'].iter_chunks(chunk_size=8192),
                media_type=content_type,
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
            )
        except boto3.exceptions.Boto3Error as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"S3 service error: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading file: {str(e)}"
        )

@router.delete('/{file_key:path}', response_model=FileDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_file(
    file_key: str,
    current_user: dict = Depends(get_current_user_jwt),
    db: Session = Depends(get_db)
):
    """
    Delete a file from S3
    """
    try:
        # Check if file exists
        try:
            s3.head_object(Bucket=BUCKET_NAME, Key=file_key)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        user_id = current_user.get("user_id")
        user_role = current_user.get("role")
        
        # Only teachers and admins can delete files
        if user_role not in ['teacher', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete files"
            )
            
        # Additional checks for assignment/course-specific files
        if file_key.startswith("assignments/"):
            match = re.match(r"assignments/(\d+)/", file_key)
            if match:
                assignment_id = int(match.group(1))
                
                # Verify assignment exists and user has rights to it
                assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
                if assignment:
                    course = db.query(Course).filter(Course.id == assignment.course_id).first()
                    
                    # If not admin, verify teacher owns the course
                    if user_role != 'admin' and course and course.teacher_id != user_id:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to delete files for this assignment"
                        )
        
        elif file_key.startswith("course_"):
            match = re.match(r"course_(\d+)/", file_key)
            if match:
                course_id = int(match.group(1))
                
                # If not admin, verify teacher owns the course
                if user_role != 'admin' and not check_course_ownership(db, user_id, course_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to delete files for this course"
                    )
        
        # Delete the file
        try:
            s3.delete_object(Bucket=BUCKET_NAME, Key=file_key)
        except boto3.exceptions.Boto3Error as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"S3 service error: {str(e)}"
            )
        
        return FileDeleteResponse(message="File deleted successfully")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting file: {str(e)}"
        )
