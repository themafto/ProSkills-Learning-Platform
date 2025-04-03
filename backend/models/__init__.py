from backend.database import Base

from .assignment import Assignment
from .course import Course
from .enrollment import Enrollment
from .ourusers import OurUsers
from .progress import AssignmentProgress, CourseProgress
from .section import Section

# Import all models here
# This way when we import Base to alembic env.py all models are also will be imported
# and changes applied to migration script


# example
# from app.models.users import Users
