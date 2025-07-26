import os
import logging
import smtplib
import asyncio
from typing import Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

class MCPEmailModule:
    """
    FastMCP module for email operations
    Supports SMTP and mock implementations for development
    """
    
    def __init__(self):
        self.module_name = "mcp_email"
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.mock_mode = os.getenv("EMAIL_MOCK_MODE", "true").lower() == "true"
        
        logger.info(f"Initialized {self.module_name} module (Mock Mode: {self.mock_mode})")
    
    async def send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email with the provided data
        """
        logger.info(f"Sending email to: {email_data.get('to', 'Unknown')}")
        
        try:
            if self.mock_mode:
                return await self._send_mock_email(email_data)
            else:
                return await self._send_smtp_email(email_data)
                
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _send_mock_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock email sending for development and testing
        """
        logger.info("Sending mock email")
        
        try:
            # Simulate email sending delay
            await asyncio.sleep(1.0)
            
            # Log email details for debugging
            logger.info(f"Mock Email Details:")
            logger.info(f"  To: {email_data.get('to', 'N/A')}")
            logger.info(f"  From: {email_data.get('from', 'N/A')}")
            logger.info(f"  Subject: {email_data.get('subject', 'N/A')}")
            logger.info(f"  Body Length: {len(email_data.get('body', ''))}")
            
            # Generate mock message ID
            message_id = f"mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}@company.com"
            
            # Save email to mock log file for reference
            await self._save_mock_email_log(email_data, message_id)
            
            return {
                "success": True,
                "message_id": message_id,
                "recipient": email_data.get('to'),
                "subject": email_data.get('subject'),
                "sent_at": datetime.now().isoformat(),
                "method": "mock"
            }
            
        except Exception as e:
            logger.error(f"Error in mock email sending: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "method": "mock"
            }
    
    async def _save_mock_email_log(self, email_data: Dict[str, Any], message_id: str):
        """
        Save mock email to a log file for reference
        """
        try:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, "mock_emails.log")
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "message_id": message_id,
                "to": email_data.get('to'),
                "from": email_data.get('from'),
                "subject": email_data.get('subject'),
                "body_preview": email_data.get('body', '')[:200] + "..." if len(email_data.get('body', '')) > 200 else email_data.get('body', ''),
                "html_body_present": bool(email_data.get('html_body'))
            }
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{log_entry}\n")
            
            logger.info(f"Mock email logged to: {log_file}")
            
        except Exception as e:
            logger.error(f"Error saving mock email log: {str(e)}")
    
    async def _send_smtp_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email using SMTP
        """
        logger.info("Sending email via SMTP")
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = email_data.get('from', self.smtp_username)
            msg['To'] = email_data.get('to')
            msg['Subject'] = email_data.get('subject', 'No Subject')
            
            # Add text part
            text_body = email_data.get('body', '')
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                msg.attach(text_part)
            
            # Add HTML part if available
            html_body = email_data.get('html_body', '')
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            await asyncio.get_event_loop().run_in_executor(
                None, self._send_smtp_message, msg, email_data.get('to')
            )
            
            message_id = msg.get('Message-ID', f"smtp_{datetime.now().strftime('%Y%m%d_%H%M%S')}@company.com")
            
            return {
                "success": True,
                "message_id": message_id,
                "recipient": email_data.get('to'),
                "subject": email_data.get('subject'),
                "sent_at": datetime.now().isoformat(),
                "method": "smtp"
            }
            
        except Exception as e:
            logger.error(f"Error in SMTP email sending: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "method": "smtp"
            }
    
    def _send_smtp_message(self, msg: MIMEMultipart, recipient: str):
        """
        Send SMTP message (synchronous operation run in executor)
        """
        server = None
        try:
            # Create SMTP connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            # Send message
            server.send_message(msg, to_addrs=[recipient])
            
            logger.info(f"Email sent successfully via SMTP to {recipient}")
            
        finally:
            if server:
                server.quit()
    
    async def send_notification(self, recipient: str, subject: str, message: str) -> Dict[str, Any]:
        """
        Send a simple notification email
        """
        logger.info(f"Sending notification to: {recipient}")
        
        try:
            email_data = {
                "to": recipient,
                "from": self.smtp_username or "system@company.com",
                "subject": subject,
                "body": message,
                "html_body": f"<p>{message.replace(chr(10), '<br>')}</p>",
                "timestamp": datetime.now().isoformat()
            }
            
            return await self.send_email(email_data)
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_bulk_email(self, recipients: list, subject: str, body: str, html_body: str = None) -> Dict[str, Any]:
        """
        Send email to multiple recipients
        """
        logger.info(f"Sending bulk email to {len(recipients)} recipients")
        
        try:
            results = []
            
            for recipient in recipients:
                email_data = {
                    "to": recipient,
                    "from": self.smtp_username or "system@company.com",
                    "subject": subject,
                    "body": body,
                    "html_body": html_body or f"<p>{body.replace(chr(10), '<br>')}</p>",
                    "timestamp": datetime.now().isoformat()
                }
                
                result = await self.send_email(email_data)
                result["recipient"] = recipient
                results.append(result)
                
                # Small delay between emails to avoid rate limiting
                await asyncio.sleep(0.1)
            
            successful_sends = len([r for r in results if r.get("success")])
            
            return {
                "success": True,
                "total_recipients": len(recipients),
                "successful_sends": successful_sends,
                "failed_sends": len(recipients) - successful_sends,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in bulk email sending: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "total_recipients": len(recipients) if recipients else 0
            }
    
    async def validate_email_config(self) -> Dict[str, Any]:
        """
        Validate email configuration
        """
        logger.info("Validating email configuration")
        
        try:
            if self.mock_mode:
                return {
                    "valid": True,
                    "mode": "mock",
                    "message": "Mock mode configuration is valid"
                }
            
            # Check SMTP configuration
            if not self.smtp_server:
                return {
                    "valid": False,
                    "mode": "smtp",
                    "error": "SMTP server not configured"
                }
            
            if not self.smtp_username or not self.smtp_password:
                return {
                    "valid": False,
                    "mode": "smtp",
                    "error": "SMTP credentials not configured"
                }
            
            # Test SMTP connection
            try:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.quit()
                
                return {
                    "valid": True,
                    "mode": "smtp",
                    "server": self.smtp_server,
                    "port": self.smtp_port,
                    "username": self.smtp_username,
                    "message": "SMTP configuration is valid"
                }
                
            except Exception as smtp_error:
                return {
                    "valid": False,
                    "mode": "smtp",
                    "error": f"SMTP connection failed: {str(smtp_error)}"
                }
            
        except Exception as e:
            logger.error(f"Error validating email configuration: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "error": str(e)
            }
