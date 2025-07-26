import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from datetime import datetime
from mcp_modules.mcp_email import MCPEmailModule

logger = logging.getLogger(__name__)

class EmailAgent:
    """
    Agent responsible for sending email summaries after human approval
    using FastMCP architecture
    """
    
    def __init__(self):
        self.mcp_module = MCPEmailModule()
        self.default_recipient = os.getenv("DEFAULT_EMAIL_RECIPIENT", "analyst@company.com")
        self.sender_email = os.getenv("SENDER_EMAIL", "system@company.com")
    
    async def send_summary_email(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email with consolidated analysis results
        """
        logger.info("Preparing to send summary email")
        
        try:
            # Generate email content
            email_content = self._generate_email_content(results)
            
            # Prepare email data
            email_data = {
                "to": self.default_recipient,
                "from": self.sender_email,
                "subject": f"Pharmaceutical Analysis Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "body": email_content["body"],
                "html_body": email_content["html_body"],
                "timestamp": datetime.now().isoformat()
            }
            
            # Send email using MCP module
            send_result = await self.mcp_module.send_email(email_data)
            
            if send_result.get("success"):
                logger.info("Email sent successfully")
                return {
                    "success": True,
                    "recipient": self.default_recipient,
                    "subject": email_data["subject"],
                    "sent_at": email_data["timestamp"],
                    "message_id": send_result.get("message_id")
                }
            else:
                raise Exception(send_result.get("error", "Unknown email sending error"))
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "recipient": self.default_recipient
            }
    
    def _generate_email_content(self, results: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate email content from analysis results
        """
        try:
            # Extract data from results
            query = results.get("query", "N/A")
            agent_results = results.get("agent_results", {})
            final_summary = results.get("final_summary", "")
            
            # Generate plain text body
            text_body = self._generate_text_body(query, agent_results, final_summary)
            
            # Generate HTML body
            html_body = self._generate_html_body(query, agent_results, final_summary)
            
            return {
                "body": text_body,
                "html_body": html_body
            }
            
        except Exception as e:
            logger.error(f"Error generating email content: {str(e)}")
            return {
                "body": f"Error generating email content: {str(e)}",
                "html_body": f"<p>Error generating email content: {str(e)}</p>"
            }
    
    def _generate_text_body(self, query: str, agent_results: Dict[str, Any], final_summary: str) -> str:
        """
        Generate plain text email body
        """
        text_parts = [
            "PHARMACEUTICAL DATA ANALYSIS SUMMARY",
            "=" * 50,
            "",
            f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Original Query: {query}",
            "",
            "EXECUTIVE SUMMARY:",
            "-" * 20,
            final_summary,
            "",
            "DETAILED RESULTS:",
            "-" * 20
        ]
        
        # CAPA Results
        capa_result = agent_results.get("capa_result", {})
        if capa_result.get("success"):
            text_parts.extend([
                "",
                "1. CAPA ANALYSIS:",
                f"   - Open CAPAs found: {capa_result.get('count', 0)}",
                f"   - Analysis period: Last 12 months"
            ])
            
            details = capa_result.get("details", [])
            if details:
                text_parts.append("   - CAPA Details:")
                for capa in details[:5]:  # Show first 5
                    text_parts.append(f"     * {capa.get('capa_id', 'N/A')}: {capa.get('title', 'N/A')}")
        else:
            text_parts.extend([
                "",
                "1. CAPA ANALYSIS:",
                f"   - Error: {capa_result.get('error', 'Unknown error')}"
            ])
        
        # Neo4j Results
        neo4j_result = agent_results.get("neo4j_result", {})
        if neo4j_result.get("success"):
            investigations = neo4j_result.get("investigations", [])
            text_parts.extend([
                "",
                "2. INVESTIGATION ANALYSIS:",
                f"   - Investigations found: {len(investigations)}",
                f"   - Brand: {neo4j_result.get('brand', 'N/A')}"
            ])
            
            if investigations:
                text_parts.append("   - Investigation Details:")
                for inv in investigations[:3]:  # Show first 3
                    text_parts.extend([
                        f"     * CAPA ID: {inv.get('capa_id', 'N/A')}",
                        f"       Investigation: {inv.get('name', 'N/A')}",
                        f"       Batch: {inv.get('batch_number', 'N/A')}"
                    ])
        else:
            text_parts.extend([
                "",
                "2. INVESTIGATION ANALYSIS:",
                f"   - Error: {neo4j_result.get('error', 'Unknown error')}"
            ])
        
        # Vector Results
        vector_result = agent_results.get("vector_result", {})
        if vector_result.get("success"):
            text_parts.extend([
                "",
                "3. CLINICAL TRIAL SUMMARY:",
                f"   - Documents analyzed: {vector_result.get('documents_found', 0)}",
                f"   - Brand: {vector_result.get('brand', 'N/A')}"
            ])
            
            summary = vector_result.get("summary", "")
            if summary:
                text_parts.extend([
                    "   - Summary:",
                    f"     {summary[:200]}{'...' if len(summary) > 200 else ''}"
                ])
        else:
            text_parts.extend([
                "",
                "3. CLINICAL TRIAL SUMMARY:",
                f"   - Error: {vector_result.get('error', 'Unknown error')}"
            ])
        
        text_parts.extend([
            "",
            "=" * 50,
            "This report was generated automatically by the Multi-Agent GenAI System.",
            "For questions or clarifications, please contact the Data Analysis Team."
        ])
        
        return "\n".join(text_parts)
    
    def _generate_html_body(self, query: str, agent_results: Dict[str, Any], final_summary: str) -> str:
        """
        Generate HTML email body
        """
        html_parts = [
            "<html><body>",
            "<h2>🧬 Pharmaceutical Data Analysis Summary</h2>",
            f"<p><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
            f"<p><strong>Original Query:</strong> <em>{query}</em></p>",
            "<hr>",
            "<h3>📊 Executive Summary</h3>",
            f"<p>{final_summary.replace(chr(10), '<br>')}</p>",
            "<hr>",
            "<h3>🔍 Detailed Results</h3>"
        ]
        
        # CAPA Results
        capa_result = agent_results.get("capa_result", {})
        html_parts.append("<h4>1. 📋 CAPA Analysis</h4>")
        
        if capa_result.get("success"):
            html_parts.extend([
                f"<p><strong>Open CAPAs found:</strong> {capa_result.get('count', 0)}</p>",
                "<p><strong>Analysis period:</strong> Last 12 months</p>"
            ])
            
            details = capa_result.get("details", [])
            if details:
                html_parts.append("<h5>CAPA Details:</h5><ul>")
                for capa in details[:5]:
                    html_parts.append(f"<li><strong>{capa.get('capa_id', 'N/A')}:</strong> {capa.get('title', 'N/A')}</li>")
                html_parts.append("</ul>")
        else:
            html_parts.append(f"<p style='color: red;'><strong>Error:</strong> {capa_result.get('error', 'Unknown error')}</p>")
        
        # Neo4j Results
        neo4j_result = agent_results.get("neo4j_result", {})
        html_parts.append("<h4>2. 🔍 Investigation Analysis</h4>")
        
        if neo4j_result.get("success"):
            investigations = neo4j_result.get("investigations", [])
            html_parts.extend([
                f"<p><strong>Investigations found:</strong> {len(investigations)}</p>",
                f"<p><strong>Brand:</strong> {neo4j_result.get('brand', 'N/A')}</p>"
            ])
            
            if investigations:
                html_parts.append("<h5>Investigation Details:</h5><ul>")
                for inv in investigations[:3]:
                    html_parts.append(
                        f"<li><strong>CAPA ID:</strong> {inv.get('capa_id', 'N/A')}<br>"
                        f"<strong>Investigation:</strong> {inv.get('name', 'N/A')}<br>"
                        f"<strong>Batch:</strong> {inv.get('batch_number', 'N/A')}</li>"
                    )
                html_parts.append("</ul>")
        else:
            html_parts.append(f"<p style='color: red;'><strong>Error:</strong> {neo4j_result.get('error', 'Unknown error')}</p>")
        
        # Vector Results
        vector_result = agent_results.get("vector_result", {})
        html_parts.append("<h4>3. 📚 Clinical Trial Summary</h4>")
        
        if vector_result.get("success"):
            html_parts.extend([
                f"<p><strong>Documents analyzed:</strong> {vector_result.get('documents_found', 0)}</p>",
                f"<p><strong>Brand:</strong> {vector_result.get('brand', 'N/A')}</p>"
            ])
            
            summary = vector_result.get("summary", "")
            if summary:
                html_parts.append(f"<p><strong>Summary:</strong><br>{summary.replace(chr(10), '<br>')}</p>")
        else:
            html_parts.append(f"<p style='color: red;'><strong>Error:</strong> {vector_result.get('error', 'Unknown error')}</p>")
        
        html_parts.extend([
            "<hr>",
            "<p><small>This report was generated automatically by the Multi-Agent GenAI System.<br>",
            "For questions or clarifications, please contact the Data Analysis Team.</small></p>",
            "</body></html>"
        ])
        
        return "".join(html_parts)
    
    async def send_notification_email(self, subject: str, message: str, recipient: str = None) -> Dict[str, Any]:
        """
        Send a simple notification email
        """
        logger.info("Sending notification email")
        
        try:
            email_data = {
                "to": recipient or self.default_recipient,
                "from": self.sender_email,
                "subject": subject,
                "body": message,
                "html_body": f"<p>{message.replace(chr(10), '<br>')}</p>",
                "timestamp": datetime.now().isoformat()
            }
            
            result = await self.mcp_module.send_email(email_data)
            
            return {
                "success": result.get("success", False),
                "recipient": email_data["to"],
                "subject": subject,
                "error": result.get("error") if not result.get("success") else None
            }
            
        except Exception as e:
            logger.error(f"Error sending notification email: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "recipient": recipient or self.default_recipient,
                "subject": subject
            }
