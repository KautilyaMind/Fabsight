"""Compact portfolio UI backed exclusively by the FabSight API."""
import os,requests,streamlit as st
API=os.getenv("FABSIGHT_API_URL","http://localhost:8000")
st.set_page_config(page_title="FabSight",layout="wide")
st.title("FabSight")
st.subheader("Enterprise Adaptable Synthetic Semiconductor Process Intelligence")
page=st.sidebar.radio("Explore",["Overview","Case Explorer","Investigations","Human Review","Final Report","Audit Trail","System Information"])
def get(path):
 r=requests.get(API+path,timeout=30); r.raise_for_status(); return r.json()
def post(path,payload=None):
 r=requests.post(API+path,json=payload or {},timeout=120); r.raise_for_status(); return r.json()
try:
 if page=="Overview":st.markdown("Public process data + wafer-map vision + synthetic telemetry + RAG + LangGraph agent + human review")
 elif page=="Case Explorer":
  cases=get("/cases"); selected=st.selectbox("Case",[x["case_id"] for x in cases]); st.json(next(x for x in cases if x["case_id"]==selected))
  if st.button("Start Investigation"):st.session_state["investigation"]=post("/investigations",{"case_id":selected}); st.success(st.session_state["investigation"]["investigation_id"])
 elif page=="Investigations":
  items=get("/investigations"); st.dataframe(items,use_container_width=True)
  if items:
   iid=st.selectbox("Investigation",[x["investigation_id"] for x in items]); detail=get(f"/investigations/{iid}"); st.write("Actual graph trace",detail.get("state",{}).get("agent_state",{}).get("trace",[]));
   if detail["status"] in {"CREATED","RESUMED"} and st.button("Run / Resume"):st.json(post(f"/investigations/{iid}/run"))
 elif page=="Human Review":
  waiting=[x for x in get("/investigations") if x["status"]=="WAITING_FOR_HUMAN"]
  if not waiting:st.write("No investigation is waiting for review.")
  else:
   iid=st.selectbox("Waiting investigation",[x["investigation_id"] for x in waiting]); detail=get(f"/investigations/{iid}"); st.json(detail.get("state",{}).get("review_request",{})); comment=st.text_area("Engineer comment"); action=st.selectbox("Action",["APPROVE","REJECT","ADD_EVIDENCE","REQUEST_REANALYSIS","COMMENT"])
   if st.button("Submit review"):st.json(post(f"/investigations/{iid}/feedback",{"action":action,"comment":comment,"author_role":"PROCESS_ENGINEER"}))
 elif page=="Final Report":
  items=get("/investigations"); iid=st.selectbox("Investigation",[x["investigation_id"] for x in items]); report=get(f"/investigations/{iid}/report"); st.warning("AI-generated and engineer approval are separate states."); st.json(report)
 elif page=="Audit Trail":
  items=get("/investigations"); iid=st.selectbox("Investigation",[x["investigation_id"] for x in items]); st.dataframe(get(f"/investigations/{iid}/audit"),use_container_width=True)
 else:st.json(get("/health")); st.write("Subsystem readiness is available from application startup checks. Configuration values and secrets are never displayed.")
except requests.RequestException as exc:st.error("FabSight API is unavailable or returned a sanitized error.")
st.caption(r"\* Notice: Educational simulation. No proprietary semiconductor manufacturing data is used.")
