"""Factory for the direct Streamlit + PostgreSQL deployment profile."""
from fabsight.agents.graph import InvestigationAgent
from fabsight.agents.persistence import PostgresCheckpointStore
from fabsight.database import PostgresInvestigationStore
from fabsight.services.investigation_service import InvestigationService

def create_cloud_service(database_url:str)->InvestigationService:
 if not database_url.strip():raise ValueError("DATABASE_URL is required for the cloud profile.")
 agent=InvestigationAgent()
 return InvestigationService(
  store=PostgresInvestigationStore(database_url),
  checkpoint_store=PostgresCheckpointStore(database_url),
  agent_factory=lambda:agent,
 )
