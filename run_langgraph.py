import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import TypedDict

from agents.orchestrator import OrchestratorAgent
from agents.capa_agent import CapaAgent
from agents.neo4j_agent import Neo4jAgent
from agents.vector_agent import VectorAgent
from agents.email_agent import EmailAgent
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class WorkflowState(TypedDict):
    query: str
    breakdown: Dict[str, Any]
    agent_results: Dict[str, Any]
    final_summary: str
    email_result: Dict[str, Any]
    error: str

class MultiAgentWorkflow:
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.capa_agent = CapaAgent()
        self.neo4j_agent = Neo4jAgent()
        self.vector_agent = VectorAgent()
        self.email_agent = EmailAgent()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> CompiledStateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("orchestrator", self.orchestrate)
        workflow.add_node("capa_agent", self.process_capa)
        workflow.add_node("neo4j_agent", self.process_neo4j)
        workflow.add_node("vector_agent", self.process_vector)
        workflow.add_node("consolidate", self.consolidate_results)
        
        # Define the flow
        workflow.set_entry_point("orchestrator")
        workflow.add_edge("orchestrator", "capa_agent")
        workflow.add_edge("capa_agent", "neo4j_agent")
        workflow.add_edge("neo4j_agent", "vector_agent")
        workflow.add_edge("vector_agent", "consolidate")
        workflow.add_edge("consolidate", END)
        
        return workflow.compile()
    
    async def orchestrate(self, state: WorkflowState) -> WorkflowState:
        """Orchestrator node - breaks down the query using Chain-of-Thought"""
        logger.info("Starting orchestrator agent")
        print("===============================================")
        print("||     Starting orchestrator agent       ||")
        print("===============================================")
        
        try:
            breakdown = await self.orchestrator.break_down_query(state["query"]) ####
            state["breakdown"] = breakdown
            logger.info(f"Query breakdown completed: {len(breakdown.get('sub_questions', []))} sub-questions")

        except Exception as e:
            logger.error(f"Error in orchestrator: {str(e)}", exc_info=True)
            state["error"] = f"Orchestrator error: {str(e)}"
        
        return state
    
    async def process_capa(self, state: WorkflowState) -> WorkflowState:
        """CAPA Agent node - processes CAPA data"""
        logger.info("Starting CAPA agent")
        print("===============================================")
        print("||           Starting CAPA agent             ||")
        print("===============================================")
        
        try:
            if "agent_results" not in state:
                state["agent_results"] = {}
            
            # Extract CAPA-related query
            breakdown = state.get("breakdown", {})
            sub_questions = breakdown.get("sub_questions", [])
            
            capa_query = ""
            for question in sub_questions:
                if "CAPA" in question:
                    capa_query = question
                    break
            
            if not capa_query:
                capa_query = "How many open CAPA are present in the last one year?"
            
            result = await self.capa_agent.process_query(capa_query)
            state["agent_results"]["capa_result"] = result
            logger.info("CAPA agent processing completed")
            
        except Exception as e:
            logger.error(f"Error in CAPA agent: {str(e)}", exc_info=True)
            if "agent_results" not in state:
                state["agent_results"] = {}
            state["agent_results"]["capa_result"] = {"success": False, "error": str(e)}
        
        return state
    
    async def process_neo4j(self, state: WorkflowState) -> WorkflowState:
        """Neo4j Agent node - queries investigation data"""
        logger.info("Starting Neo4j agent")
        print("===============================================")
        print("||           Starting Neo4j agent            ||")
        print("===============================================")
        
        try:
            if "agent_results" not in state:
                state["agent_results"] = {}
            
            # Get CAPA IDs from previous step if available
            capa_result = state.get("agent_results", {}).get("capa_result", {})
            capa_ids = []
            
            if capa_result.get("success") and capa_result.get("details"):
                for capa in capa_result["details"]:
                    if capa.get("capa_id"):
                        capa_ids.append(capa["capa_id"])
            
            # Query for brand Avino investigations
            result = await self.neo4j_agent.get_investigations("Avino", capa_ids)
            state["agent_results"]["neo4j_result"] = result
            logger.info("Neo4j agent processing completed")
            
        except Exception as e:
            logger.error(f"Error in Neo4j agent: {str(e)}", exc_info=True)
            if "agent_results" not in state:
                state["agent_results"] = {}
            state["agent_results"]["neo4j_result"] = {"success": False, "error": str(e)}
        
        return state
    
    async def process_vector(self, state: WorkflowState) -> WorkflowState:
        """Vector Agent node - searches clinical trial data"""
        logger.info("Starting Vector agent")
        print("===============================================")
        print("||           Starting Vector agent           ||")
        print("===============================================")
        
        try:
            if "agent_results" not in state:
                state["agent_results"] = {}
            
            # Get PDF links from Neo4j results
            neo4j_result = state.get("agent_results", {}).get("neo4j_result", {})
            pdf_links = []
            
            if neo4j_result.get("success") and neo4j_result.get("investigations"):
                # print(f"Fetching PDF link for \n\t neo4j_result['investigations']:", neo4j_result["investigations"])
                for inv in neo4j_result["investigations"]:
                    if inv.get("pdf_link"):
                        pdf_links.append(inv["pdf_link"])
            

            # Search for Avino clinical trial summaries
            result = await self.vector_agent.search_clinical_trials("Avino", pdf_links)
            state["agent_results"]["vector_result"] = result
            logger.info("Vector agent processing completed")
            
        except Exception as e:
            logger.error(f"Error in Vector agent: {str(e)}", exc_info=True)
            if "agent_results" not in state:
                state["agent_results"] = {}
            state["agent_results"]["vector_result"] = {"success": False, "error": str(e)}
        
        return state
    
    async def consolidate_results(self, state: WorkflowState) -> WorkflowState:
        """Consolidate all agent results into a final summary"""
        logger.info("Consolidating results")
        print("=======================================================")
        print("|| Consolidate all agent results into a final summary ||")
        print("=======================================================")
        
        try:
            agent_results = state.get("agent_results", {})
            summary_parts = []
            
            # CAPA summary
            capa_result = agent_results.get("capa_result", {})
            if capa_result.get("success"):
                count = capa_result.get("count", 0)
                summary_parts.append(f"**CAPA Analysis:** Found {count} open CAPAs in the last year.")
            else:
                summary_parts.append(f"**CAPA Analysis:** Error - {capa_result.get('error', 'Unknown error')}")
            
            # Investigation summary
            neo4j_result = agent_results.get("neo4j_result", {})
            if neo4j_result.get("success"):
                investigations = neo4j_result.get("investigations", [])
                inv_count = len(investigations)
                summary_parts.append(f"**Investigations:** Found {inv_count} investigations for brand Avino.")
            else:
                summary_parts.append(f"**Investigations:** Error - {neo4j_result.get('error', 'Unknown error')}")
            
            # Clinical trial summary
            vector_result = agent_results.get("vector_result", {})
            if vector_result.get("success"):
                if vector_result.get("summary"):
                    summary_parts.append(f"**Clinical Trials:** {vector_result['summary']}")
                else:
                    summary_parts.append("**Clinical Trials:** No clinical trial data found for brand Avino.")
            else:
                summary_parts.append(f"**Clinical Trials:** Error - {vector_result.get('error', 'Unknown error')}")
            
            # Generate final summary using orchestrator
            consolidated_data = "\n".join(summary_parts)
            final_summary = await self.orchestrator.generate_final_summary(consolidated_data)
            state["final_summary"] = final_summary
            
            logger.info("Results consolidation completed")
            
        except Exception as e:
            logger.error(f"Error consolidating results: {str(e)}", exc_info=True)
            state["final_summary"] = f"Error consolidating results: {str(e)}"
        
        return state
    
    async def run(self, query: str) -> Dict[str, Any]:
        """Run the complete workflow"""
        logger.info(f"Starting workflow for query: {query[:100]}...")
        
        initial_state: WorkflowState = {
            "query": query,
            "breakdown": {},
            "agent_results": {},
            "final_summary": "",
            "email_result": {},
            "error": ""
        }
        
        try:
            final_state = await self.workflow.ainvoke(initial_state)
            logger.info("Workflow completed successfully")
            return final_state
        
        except Exception as e:
            logger.error(f"Workflow error: {str(e)}", exc_info=True)
            return {
                "query": query,
                "breakdown": {},
                "agent_results": {},
                "final_summary": f"Workflow error: {str(e)}",
                "email_result": {},
                "error": str(e)
            }
    
    async def send_email(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Send email with consolidated results"""
        logger.info("Sending email with results")
        print("===============================================")
        print("||           Starting Email agent            ||")
        print("===============================================")
        
        try:
            return await self.email_agent.send_summary_email(results)
        
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

# Test function
async def test_workflow():
    """Test the workflow with a sample query"""
    workflow = MultiAgentWorkflow()
    
    test_query = ("Please provide how many open CAPA present in last one year. "
                 "Also, provide how many investigation were created for brand Avino "
                 "and provide brand Avino's Clinical Trial summary.")
    
    results = await workflow.run(test_query)
    print(json.dumps(results, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(test_workflow())
