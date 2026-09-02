from typing import Any
from pydantic import BaseModel,Field
class InvestigationCreate(BaseModel):case_id:str=Field(min_length=1,max_length=64)
class FeedbackRequest(BaseModel):
 action:str; comment:str=Field(default="",max_length=4000); author_role:str="PROCESS_ENGINEER"; evidence:dict[str,Any]|None=None; requested_analysis:str|None=None
