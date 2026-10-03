"""Thin FastAPI layer; intelligence remains in InvestigationService."""
from __future__ import annotations
from fastapi import FastAPI,HTTPException,Request
from api.schemas import FeedbackRequest,InvestigationCreate
from fabsight.services import InvestigationService
from fabsight.services.health import startup_status

app=FastAPI(title="FabSight API",version="1.1.0",description="Synthetic educational process-intelligence application")
def service(request:Request)->InvestigationService:
 if not hasattr(request.app.state,"service"):request.app.state.service=InvestigationService()
 return request.app.state.service
def safe(call):
 try:return call()
 except KeyError as exc:raise HTTPException(404,detail=str(exc).strip("'")) from None
 except ValueError as exc:raise HTTPException(400,detail=str(exc)) from None
@app.get("/health")
def health():return startup_status()
@app.get("/cases")
def cases(request:Request):return [x.to_dict() for x in service(request).cases()]
@app.get("/cases/{case_id}")
def case(case_id:str,request:Request):return safe(lambda:service(request).case(case_id).to_dict())
@app.post("/investigations",status_code=201)
def create(body:InvestigationCreate,request:Request):return safe(lambda:service(request).create(body.case_id))
@app.get("/investigations")
def investigations(request:Request):return service(request).list()
@app.post("/investigations/{iid}/run")
def run(iid:str,request:Request):return safe(lambda:service(request).run(iid))
@app.get("/investigations/{iid}")
def detail(iid:str,request:Request):return safe(lambda:service(request).detail(iid))
@app.post("/investigations/{iid}/feedback")
def feedback(iid:str,body:FeedbackRequest,request:Request):return safe(lambda:service(request).feedback(iid,body.model_dump()))
@app.get("/investigations/{iid}/report")
def report(iid:str,request:Request):return safe(lambda:service(request).report(iid))
@app.get("/investigations/{iid}/audit")
def audit(iid:str,request:Request):return safe(lambda:service(request).audit(iid))
