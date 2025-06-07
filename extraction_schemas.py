# extraction_schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional

# class CoursePrerequisite(BaseModel):
#     code: str = Field(..., description="Prerequisite course code, e.g., 'BIOL 0030'")

# class CourseExtraInfo(BaseModel):
#     enrollment_limit: Optional[int] = Field(
#         None, description="Maximum number of students, e.g., 20"
#     )
#     instructor_permission_required: Optional[bool] = Field(
#         None, description="True if course text says 'Instructor permission required'"
#     )

class CourseSchema(BaseModel):
    course_code: str = Field(..., description="Catalog number, e.g., 'BIOL 0040'")
    course_title: str = Field(..., description="Title, e.g., 'Nutrition for Fitness and Physical Activity'")
    course_description: str = Field(..., description="Complete text description of the specific course")
    # prerequisites: List[CoursePrerequisite] = Field(
    #     default_factory=list,
    #     description="List of prerequisite course codes mentioned in this block"
    # )
    # extra_info: Optional[CourseExtraInfo] = Field(
    #     None, description="Any extra structured details (enrollment, permissions, etc.)"
    # )
