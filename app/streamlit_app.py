"""Single-service FabSight UI for Streamlit Community Cloud."""
from __future__ import annotations
import os,sys
from pathlib import Path
import streamlit as st

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"src")]
from fabsight.services import InvestigationService  # noqa:E402
from fabsight.services.cloud import create_cloud_service  # noqa:E402
from fabsight.services.health import startup_status  # noqa:E402

st.set_page_config(page_title="FabSight",layout="wide")

@st.cache_resource(show_spinner="Loading FabSight models and retrieval index...")
def service(database_url:str):
 if database_url:return create_cloud_service(database_url)
 return InvestigationService()

def records():return service(database_url).list()
def selected_id(items,label="Investigation"):
 return st.selectbox(label,[x["investigation_id"] for x in items]) if items else None

database_url=os.getenv("DATABASE_URL","").strip()
cloud_mode=bool(database_url)
app=service(database_url)
st.title("FabSight")
st.subheader("Enterprise Adaptable Synthetic Semiconductor Process Intelligence")
page=st.sidebar.radio("Explore",["Overview","Case Explorer","Investigations","Human Review","Final Report","Audit Trail","System Information"])
try:
 if page=="Overview":
  st.markdown("Public process data + wafer-map vision + synthetic telemetry + RAG + LangGraph agent + human review")
  st.info("This cloud profile runs the investigation service directly inside Streamlit; PostgreSQL stores investigations and graph checkpoints.")
 elif page=="Case Explorer":
  cases=[x.to_dict() for x in app.cases()];selected=st.selectbox("Case",[x["case_id"] for x in cases]);st.json(next(x for x in cases if x["case_id"]==selected))
  if st.button("Start Investigation"):
   created=app.create(selected);st.session_state["investigation"]=created;st.success(created["investigation_id"])
 elif page=="Investigations":
  items=records();st.dataframe(items,use_container_width=True);iid=selected_id(items)
  if iid:
   detail=app.detail(iid);st.write("Actual graph trace",detail.get("state",{}).get("agent_state",{}).get("trace",[]))
   if detail["status"] in {"CREATED","RESUMED"} and st.button("Run / Resume"):
    with st.spinner("Running the evidence investigation..."):st.json(app.run(iid))
 elif page=="Human Review":
  waiting=[x for x in records() if x["status"]=="WAITING_FOR_HUMAN"]
  if not waiting:st.write("No investigation is waiting for review.")
  else:
   iid=selected_id(waiting,"Waiting investigation");detail=app.detail(iid);st.json(detail.get("state",{}).get("review_request",{}));comment=st.text_area("Engineer comment");action=st.selectbox("Action",["APPROVE","REJECT","ADD_EVIDENCE","REQUEST_REANALYSIS","COMMENT"])
   if st.button("Submit review"):st.json(app.feedback(iid,{"action":action,"comment":comment,"author_role":"PROCESS_ENGINEER"}))
 elif page=="Final Report":
  items=records();iid=selected_id(items)
  if iid:
   st.warning("AI-generated and engineer approval are separate states.")
   try:st.json(app.report(iid))
   except KeyError:st.info("The report is available after the investigation and human-review workflow completes.")
  else:st.info("Start an investigation first.")
 elif page=="Audit Trail":
  items=records();iid=selected_id(items)
  if iid:st.dataframe(app.audit(iid),use_container_width=True)
  else:st.info("Start an investigation first.")
 else:
  health=startup_status();health["deployment"]="streamlit-postgres" if cloud_mode else "local-sqlite";health["subsystems"]["application_database"]="READY";health["subsystems"]["checkpoint_database"]="READY";st.json(health);st.write("Configuration values and secrets are never displayed.")
except (KeyError,ValueError) as exc:st.error(str(exc).strip("'"))
except Exception as exc:
 detail=str(exc) if isinstance(exc,TypeError) else type(exc).__name__
 st.error(f"FabSight could not complete this operation. Diagnostic: {detail}")
st.caption(r"\* Notice: Educational simulation. No proprietary semiconductor manufacturing data is used.")
