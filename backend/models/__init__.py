from .ourusers import OurUsers
from .course import Course
from .section import Section
from .assignment import Assignment
from .progress import AssignmentProgress, CourseProgress
from .enrollment import Enrollment

# Import all models here
# This way when we import Base to alembic env.py all models are also will be imported
# and changes applied to migration script

from backend.database import Base

# example
# from app.models.users import Users
