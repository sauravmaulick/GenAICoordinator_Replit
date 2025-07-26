import os
import json
import logging
from typing import Dict, Any, List
# from google import genai
# from google.genai import types
from utils.config import Config
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    Gemini-powered orchestrator agent that breaks down complex queries 
    using Chain-of-Thought reasoning and coordinates other agents
    """
    
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        # self.model = "gemini-2.5-flash"
        self.model = "gemini-1.5-flash"
        
        # print("\n +1"*5)
        # import google.generativeai as genai
        # # genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        # # Load variables from .env
        # load_dotenv()
        # # Get the API key
        # api_key = os.getenv("GEMINI_API_KEY")
        # # Configure the API
        # genai.configure(api_key=api_key)
        # # Use the model
        # model = genai.GenerativeModel("gemini-1.5-flash")
        # response = model.generate_content("What is quantum computing?")
        # print(response.text)
        # print("\n +1"*5)
        
    async def break_down_query(self, user_query: str) -> Dict[str, Any]:
        """
        Break down the user query into sub-questions using Chain-of-Thought reasoning
        """
        logger.info("Breaking down user query using Chain-of-Thought")
        print(f"*************** User Query: {user_query}")

        # print("==> Gimini Key", genai.configure(api_key=os.getenv("GEMINI_API_KEY")))
        
        try:
            model = genai.GenerativeModel(self.model)

            system_prompt = """
            You are an expert pharmaceutical data analyst. Your task is to break down complex user queries 
            into specific sub-questions that can be handled by specialized agents.
            
            Available agents and their capabilities:
            1. CAPA Agent: Reads and analyzes CAPA (Corrective and Preventive Action) data from text files
            2. Neo4j Agent: Queries graph database for investigation details, brands, batches, and PDF links
            3. Vector Agent: Searches vector database for clinical trial summaries and embedded document content
            4. Email Agent: Sends consolidated summaries via email
            
            For the given query, break it down into 3 specific sub-questions:
            - Q1: Should focus on CAPA data analysis (count, status, timeframe)
            - Q2: Should focus on Neo4j investigation queries (brand-specific, with CAPA relationships)
            - Q3: Should focus on vector search for clinical trial summaries
            
            Respond with JSON in this format:
            {
                "reasoning": "Your chain-of-thought reasoning for the breakdown",
                "sub_questions": [
                    "Q1: Specific CAPA-related question",
                    "Q2: Specific Neo4j investigation question", 
                    "Q3: Specific vector search question"
                ],
                "agent_mapping": {
                    "capa_agent": "Q1 description",
                    "neo4j_agent": "Q2 description", 
                    "vector_agent": "Q3 description"
                }
            }
            """
            # print("\n=" * 5)
            # print("line no 66: system_prompt:")
            # response = genai.GenerativeModel(self.model).generate_content(
            #     contents=[
            #         types.Content(role="user", parts=[types.Part(text=f"User Query: {user_query}")])
            #     ],
            #     generation_config=types.GenerationConfig(
            #         system_instruction=system_prompt,
            #         response_mime_type="application/json",
            #         temperature=0.1
            #     )
            # )

            # print("line no 78: response.text:", response.text)
            # print("\n=" * 5)
            
            # print("\n+2" * 5)
            # print("line no 66: system_prompt:")

            # response = genai.GenerativeModel(self.model).generate_content(
            #     contents=[
            #         types.Content(role="system", parts=[types.Part(text=system_prompt)]),
            #         types.Content(role="user", parts=[types.Part(text=f"User Query: {user_query}")])
            #     ],
            #     generation_config=types.GenerationConfig(
            #         response_mime_type="application/json",
            #         temperature=0.1
            #     )
            # )

            combined_prompt = f"""{system_prompt}
                User Query: {user_query}
                """
            
            response = model.generate_content(
                # contents=[
                #     {"role": "system", "parts": [system_prompt]},
                #     {"role": "user", "parts": [f"User Query: {user_query}"]}
                # ],
                contents=[{"role": "user", "parts": [combined_prompt]}],
                generation_config=GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            
            # print("line no 78: response.text:", response.text)
            # print("\n+2" * 5)

            if response.text:
                breakdown = json.loads(response.text)
                logger.info("Successfully broke down query into sub-questions")
                return breakdown
            else:
                raise ValueError("Empty response from Gemini")
                
        except Exception as e:
            logger.error(f"Error breaking down query: {str(e)}", exc_info=True)
            print(f"\n\n\nError breaking down query: {str(e)}")
            # Fallback breakdown
            return {
                "reasoning": "Fallback breakdown due to API error",
                "sub_questions": [
                    "Q1: How many open CAPA are present in the last 1 year?",
                    "Q2: Fetch Investigation details for brand 'Avino' including CAPA ID, Investigation Name, Brand, Batch Number, PDF Link",
                    "Q3: Retrieve clinical trial summary for brand 'Avino' from vector database"
                ],
                "agent_mapping": {
                    "capa_agent": "Analyze CAPA data file for open CAPAs in specified timeframe",
                    "neo4j_agent": "Query graph database for Avino brand investigations",
                    "vector_agent": "Search embedded clinical trial documents for Avino summaries"
                }
            }
    
    async def generate_final_summary(self, consolidated_data: str) -> str:
        """
        Generate a final consolidated summary from all agent results
        """
        logger.info("Generating final consolidated summary")
        
        try:
            model = genai.GenerativeModel(self.model)
            
            system_prompt = """
            You are a pharmaceutical data analyst creating a comprehensive summary report.
            
            Based on the consolidated data from multiple specialized agents, create a clear, 
            professional summary that answers the original user query.
            
            Format the summary with:
            1. Executive Summary (2-3 sentences)
            2. Key Findings (bullet points)
            3. Detailed Results (organized by data source)
            4. Recommendations or Next Steps (if applicable)
            
            Keep the tone professional and data-driven.
            """
            
            # response = self.client.models.generate_content(
            # response = genai.GenerativeModel(self.model).generate_content(
            #     contents=[
            #         types.Content(role="user", parts=[types.Part(text=f"Consolidated Data:\n{consolidated_data}")])
            #     ],
            #     generation_config=types.GenerationConfig(
            #         system_instruction=system_prompt,
            #         temperature=0.3
            #     )
            # )

            combined_prompt = f"""{system_prompt}
                consolidated_data: {consolidated_data}
                """
            
            response = model.generate_content(
                # contents=[
                #     {"role": "system", "parts": [system_prompt]},
                #     {"role": "user", "parts": [f"User Query: {user_query}"]}
                # ],
                contents=[{"role": "user", "parts": [combined_prompt]}],
                generation_config=GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )

            if response.text:
                logger.info("Successfully generated final summary")
                return response.text
            else:
                raise ValueError("Empty response from Gemini")
                
        except Exception as e:
            logger.error(f"Error generating final summary: {str(e)}", exc_info=True)
            return f"Summary generation failed: {str(e)}\n\nRaw Data:\n{consolidated_data}"
    
    async def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Analyze the intent and requirements of the user query
        """
        logger.info("Analyzing query intent")
        
        try:
            system_prompt = """
            Analyze the user query to identify:
            1. Primary intent (data retrieval, analysis, reporting, etc.)
            2. Required data sources (CAPA files, Neo4j, vector DB, etc.)
            3. Expected output format
            4. Urgency level
            5. Stakeholders involved
            
            Respond with JSON format.
            """
            
            # response = self.client.models.generate_content(
            #     model=self.model,
            response = genai.GenerativeModel(self.model).generate_content(
                contents=[
                    types.Content(role="user", parts=[types.Part(text=query)])
                ],
                generation_config=types.GenerationConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            return json.loads(response.text)
            # else:
            #     raise ValueError("Empty response from Gemini")
                
        except Exception as e:
            logger.error(f"Error analyzing query intent: {str(e)}", exc_info=True)
            return {
                "primary_intent": "data_analysis",
                "data_sources": ["capa", "neo4j", "vector"],
                "output_format": "summary_report",
                "urgency": "normal",
                "stakeholders": ["analyst"]
            }
