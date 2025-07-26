import streamlit as st
import asyncio
import json
from datetime import datetime
import logging
from run_langgraph import MultiAgentWorkflow
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def main():
    st.title("🧬 Multi-Agent GenAI System")
    st.header("Pharmaceutical Data Analysis with AI Agents")
    
    # Initialize session state
    if 'workflow_results' not in st.session_state:
        st.session_state.workflow_results = None
    if 'email_approved' not in st.session_state:
        st.session_state.email_approved = False
    if 'processing' not in st.session_state:
        st.session_state.processing = True #False
    
    # Sidebar for configuration
    # with st.sidebar:
    #     st.header("⚙️ Configuration")
        
    #     # API Status Check
    #     st.subheader("🔑 API Status")
    #     import os 
    #     gemini_key = os.getenv("GEMINI_API_KEY")
    #     neo4j_uri = os.getenv("NEO4J_URI", "")
    #     astra_token = os.getenv("ASTRA_DB_TOKEN", "")
        
    #     st.write("Gemini API:", "✅ Configured" if gemini_key else "❌ Missing")
    #     st.write("Neo4j:", "✅ Configured" if neo4j_uri else "❌ Missing")
    #     st.write("Astra DB:", "✅ Configured" if astra_token else "✅ Mock Mode")
        
    #     st.divider()
        
    #     # Sample queries
        # st.subheader("📝 Sample Queries")
        # if st.button("Load Sample Query"):
        #     st.session_state.sample_query = True
    
    # Main interface
    st.header("💬 Enter Your Query")
    
    # # Query input
    # default_query = ""
    # if hasattr(st.session_state, 'sample_query') and st.session_state.sample_query:
    #     default_query = "Please provide how many open CAPA present in last one year. Also, provide how many investigation were created for brand Avino and provide brand Avino's Clinical Trial summary."
    #     st.session_state.sample_query = False
    
    # user_query = st.text_area(
    #     "Please provide how many open CAPA present in last one year. Also, provide how many investigation were created for brand Avino and provide brand Avino's Clinical Trial summary.",
    #     # value=default_query,
    #     height=100,
    #     # placeholder="e.g., Please provide how many open CAPA present in last one year..."
    # )
    
    # user_query = st.text_input(
    #     "Please provide how many open CAPA present in last one year. Also, provide how many investigation were created for brand Avino and provide brand Avino's Clinical Trial summary."
    #     )   

    # user_query = st.text_area(
    #     label="Enter your pharmaceutical query below:",
    #     height=100,
    #     placeholder="e.g., Please provide how many open CAPA are present in the last one year. Also, provide how many investigations were created for brand Avino and its Clinical Trial summary."
    # )

    st.markdown("""
    **Sample Query:**
    Please provide how many open CAPA are present in the last one year. Also, provide how many investigations were created for brand Avino and its Clinical Trial summary.
    """)

    user_query = st.text_area(
        label="Your Query",
        height=100,
        placeholder="Paste or type your query here..."
    )


    # Process button
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("🚀 Process Query", disabled=st.session_state.processing or not user_query.strip()):
            st.session_state.processing = True
            st.session_state.workflow_results = None
            st.session_state.email_approved = False
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Results"):
            st.session_state.workflow_results = None
            st.session_state.email_approved = False
            st.session_state.processing = False
            st.rerun()
    
    # print("==> st.session_state.processing:", st.session_state.processing)
    # print("user_query:", user_query.strip())
    # Processing
    if st.session_state.processing and user_query.strip():
        with st.spinner("🤖 Processing query through AI agents..."):
            try:
                print(f"Processing user query: {user_query}")
                # Run the workflow
                workflow = MultiAgentWorkflow() #run_langgraph.py
                results = asyncio.run(workflow.run(user_query))
                st.session_state.workflow_results = results
                st.session_state.processing = False
                st.success("✅ Query processed successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error processing query: {str(e)}")
                st.session_state.processing = False
                logger.error(f"Error in workflow: {str(e)}", exc_info=True)

    else:
        st.session_state.processing = False
        if not user_query.strip():
            st.warning("Please enter a query to process.")
    
    # Display results
    if st.session_state.workflow_results:
        st.header("📊 Results")
        
        results = st.session_state.workflow_results
        
        # Show breakdown
        if 'breakdown' in results:
            with st.expander("🧠 Chain-of-Thought Breakdown", expanded=True):
                breakdown = results['breakdown']
                for i, question in enumerate(breakdown.get('sub_questions', []), 1):
                    st.write(f"**Q{i}:** {question}")
        
        # Show agent results
        if 'agent_results' in results:
            st.subheader("🤖 Agent Results")
            
            agent_results = results['agent_results']
            
            # CAPA Results
            if 'capa_result' in agent_results:
                with st.expander("📋 CAPA Analysis Results"):
                    capa_data = agent_results['capa_result']
                    if capa_data.get('success'):
                        st.metric("Open CAPAs (Last Year)", capa_data.get('count', 0))
                        if capa_data.get('details'):
                            st.json(capa_data['details'])
                    else:
                        st.error(f"CAPA Agent Error: {capa_data.get('error', 'Unknown error')}")
            
            # Neo4j Results
            if 'neo4j_result' in agent_results:
                with st.expander("🔍 Investigation Details"):
                    neo4j_data = agent_results['neo4j_result']
                    if neo4j_data.get('success'):
                        investigations = neo4j_data.get('investigations', [])
                        if investigations:
                            for inv in investigations:
                                st.write(f"**CAPA ID:** {inv.get('capa_id', 'N/A')}")
                                st.write(f"**Investigation:** {inv.get('name', 'N/A')}")
                                st.write(f"**Brand:** {inv.get('brand', 'N/A')}")
                                st.write(f"**Batch:** {inv.get('batch_number', 'N/A')}")
                                if inv.get('pdf_link'):
                                    st.write(f"**PDF Link:** {inv['pdf_link']}")
                                st.divider()
                        else:
                            st.info("No investigations found for the specified criteria.")
                    else:
                        st.error(f"Neo4j Agent Error: {neo4j_data.get('error', 'Unknown error')}")
            
            # Vector Search Results
            if 'vector_result' in agent_results:
                with st.expander("📚 Clinical Trial Summary"):
                    vector_data = agent_results['vector_result']
                    if vector_data.get('success'):
                        summary = vector_data.get('summary', '')
                        if summary:
                            st.write(summary)
                        else:
                            st.info("No clinical trial data found for the specified brand.")
                    else:
                        st.error(f"Vector Search Agent Error: {vector_data.get('error', 'Unknown error')}")
        
        # Consolidated Summary
        if 'final_summary' in results:
            st.subheader("📈 Consolidated Summary")
            st.write(results['final_summary'])
        
        # Email confirmation
        st.subheader("📧 Email Summary")
        
        if not st.session_state.email_approved:
            st.info("Would you like to send this summary via email?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Send Email"):
                    st.session_state.email_approved = True
                    st.rerun()
            
            with col2:
                if st.button("❌ No, Don't Send"):
                    st.info("Email not sent.")
        
        else:
            with st.spinner("📤 Sending email..."):
                try:
                    workflow = MultiAgentWorkflow()
                    email_result = asyncio.run(workflow.send_email(results))
                    
                    if email_result.get('success'):
                        st.success("✅ Email sent successfully!")
                        st.write(f"**To:** {email_result.get('recipient', 'N/A')}")
                        st.write(f"**Subject:** {email_result.get('subject', 'N/A')}")
                    else:
                        st.error(f"❌ Failed to send email: {email_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error sending email: {str(e)}")
                    logger.error(f"Error sending email: {str(e)}", exc_info=True)
                
                st.session_state.email_approved = False

    # Footer
    st.divider()
    st.caption(f"Multi-Agent GenAI System | Powered by Google Gemini | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
