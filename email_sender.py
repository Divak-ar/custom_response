import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
import os
import logging
import mimetypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, sender, password, server="Gmail", to_emails=None, cc_emails=None, 
                subject=None, body=None, html_content=False, smtp_server=None, smtp_port=None,
                attachment_path=None):
        self.sender = sender
        self.password = password
        self.server_type = server
        self.to_emails = to_emails or []
        self.cc_emails = cc_emails or []
        self.default_subject = subject or "Automated Email"
        self.default_body = body or "This is an automated email."
        self.html_content = html_content
        self.attachment_path = attachment_path
        
        # Set SMTP settings based on provider
        if smtp_server and smtp_port:  # Custom SMTP
            self.smtp_server = smtp_server
            self.smtp_port = smtp_port
        elif server == "Gmail":
            self.smtp_server = "smtp.gmail.com"
            self.smtp_port = 587
        elif server == "Outlook":
            self.smtp_server = "smtp.office365.com"
            self.smtp_port = 587
        else:
            raise ValueError("Unsupported email server type")
            
    def send_email(self, subject=None, body=None, to_emails=None, cc_emails=None, 
                   html_content=None, attachment_path=None):
        """Send an email with the configured settings"""
        subject = subject or self.default_subject
        body = body or self.default_body
        to_emails = to_emails or self.to_emails
        cc_emails = cc_emails or self.cc_emails
        html_content = html_content if html_content is not None else self.html_content
        attachment_path = attachment_path or self.attachment_path
        
        if not to_emails:
            logger.error("No recipient emails specified")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = ", ".join(to_emails)
            if cc_emails:
                msg['Cc'] = ", ".join(cc_emails)
            msg['Subject'] = subject
            
            # Attach body
            if html_content:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Attach audio file if provided
            if attachment_path and os.path.exists(attachment_path):
                try:
                    # Determine MIME type
                    ctype, encoding = mimetypes.guess_type(attachment_path)
                    if ctype is None or encoding is not None:
                        ctype = 'application/octet-stream'
                    maintype, subtype = ctype.split('/', 1)
                    
                    if maintype == 'audio':
                        with open(attachment_path, 'rb') as fp:
                            attachment = MIMEAudio(fp.read(), _subtype=subtype)
                        
                        # Add header to make the attachment downloadable
                        filename = os.path.basename(attachment_path)
                        attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                        msg.attach(attachment)
                        logger.info(f"Attached audio file: {filename}")
                except Exception as e:
                    logger.error(f"Failed to attach audio file: {e}")
            
            # Connect to server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender, self.password)
            
            # Send email
            all_recipients = to_emails + cc_emails
            server.sendmail(self.sender, all_recipients, msg.as_string())
            server.quit()
            
            logger.info(f"Email sent to {len(all_recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
            
    def test_connection(self):
        """Test the SMTP connection"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender, self.password)
            server.quit()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False