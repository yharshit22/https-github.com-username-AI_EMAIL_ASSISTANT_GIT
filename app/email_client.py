import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from email.utils import parsedate_to_datetime
import logging
from datetime import datetime, timedelta
from flask import current_app
from app.models import Email, EmailAttachment
import re

logger = logging.getLogger(__name__)

class EmailClient:
    """Email client for IMAP and SMTP operations"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.imap_host = current_app.config['IMAP_HOST']
        self.imap_port = current_app.config['IMAP_PORT']
        self.imap_username = current_app.config['IMAP_USERNAME']
        self.imap_password = current_app.config['IMAP_PASSWORD']
        
        self.smtp_host = current_app.config['SMTP_HOST']
        self.smtp_port = current_app.config['SMTP_PORT']
        self.smtp_username = current_app.config['SMTP_USERNAME']
        self.smtp_password = current_app.config['SMTP_PASSWORD']
    
    def fetch_emails(self, folder='INBOX', limit=50, since_days=7):
        """Fetch emails from IMAP server"""
        emails = []
        
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            mail.login(self.imap_username, self.imap_password)
            
            # Select folder
            status, messages = mail.select(folder)
            if status != 'OK':
                logger.error(f"Failed to select folder {folder}")
                return emails
            
            # Search for emails since specified days
            since_date = datetime.now() - timedelta(days=since_days)
            search_criteria = f'(SINCE "{since_date.strftime("%d-%b-%Y")}")'
            
            status, message_ids = mail.search(None, search_criteria)
            if status != 'OK':
                logger.error("Failed to search emails")
                return emails
            
            # Get message IDs
            message_ids = message_ids[0].split()
            message_ids = message_ids[-limit:]  # Get latest emails
            
            for msg_id in message_ids:
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    # Parse email
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    
                    # Extract email data
                    email_data = self._parse_email(email_message)
                    if email_data:
                        emails.append(email_data)
                        
                except Exception as e:
                    logger.error(f"Error processing email {msg_id}: {str(e)}")
                    continue
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
        
        return emails
    
    def _parse_email(self, email_message):
        """Parse email message and extract relevant data"""
        try:
            # Extract headers
            message_id = email_message.get('Message-ID', '').strip()
            from_address = self._decode_header(email_message.get('From', ''))
            to_address = self._decode_header(email_message.get('To', ''))
            cc_address = self._decode_header(email_message.get('Cc', ''))
            subject = self._decode_header(email_message.get('Subject', ''))
            date_str = email_message.get('Date', '')
            
            # Parse date
            received_at = None
            if date_str:
                try:
                    received_at = parsedate_to_datetime(date_str)
                except:
                    received_at = datetime.now()
            else:
                received_at = datetime.now()
            
            # Extract body
            body_plain, body_html, body = self._extract_body(email_message)
            
            # Get message size
            message_size = len(str(email_message))
            
            # Extract in-reply-to and references
            in_reply_to = email_message.get('In-Reply-To', '')
            references = email_message.get('References', '')
            
            return {
                'message_id': message_id,
                'from_address': from_address,
                'to_address': to_address,
                'cc_address': cc_address,
                'subject': subject,
                'body': body,
                'body_plain': body_plain,
                'body_html': body_html,
                'received_at': received_at,
                'message_size': message_size,
                'in_reply_to': in_reply_to,
                'references': references,
                'attachments': self._extract_attachments(email_message)
            }
            
        except Exception as e:
            logger.error(f"Error parsing email: {str(e)}")
            return None
    
    def _decode_header(self, header):
        """Decode email header"""
        if not header:
            return ''
        
        decoded_parts = []
        for part, encoding in decode_header(header):
            if isinstance(part, bytes):
                if encoding:
                    try:
                        decoded_parts.append(part.decode(encoding))
                    except:
                        decoded_parts.append(part.decode('utf-8', errors='ignore'))
                else:
                    decoded_parts.append(part.decode('utf-8', errors='ignore'))
            else:
                decoded_parts.append(str(part))
        
        return ' '.join(decoded_parts)
    
    def _extract_body(self, email_message):
        """Extract email body content"""
        body_plain = ''
        body_html = ''
        body = ''
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                # Get content
                try:
                    content = part.get_payload(decode=True)
                    if content:
                        charset = part.get_content_charset() or 'utf-8'
                        content = content.decode(charset, errors='ignore')
                        
                        if content_type == "text/plain":
                            body_plain += content
                        elif content_type == "text/html":
                            body_html += content
                except:
                    continue
        else:
            # Single part message
            try:
                content = email_message.get_payload(decode=True)
                if content:
                    charset = email_message.get_content_charset() or 'utf-8'
                    content = content.decode(charset, errors='ignore')
                    
                    if email_message.get_content_type() == "text/plain":
                        body_plain = content
                    elif email_message.get_content_type() == "text/html":
                        body_html = content
            except:
                pass
        
        # Choose best body content
        if body_html:
            body = self._html_to_text(body_html)
        elif body_plain:
            body = body_plain
        else:
            body = "No readable content found"
        
        return body_plain.strip(), body_html.strip(), body.strip()
    
    def _html_to_text(self, html):
        """Convert HTML to plain text"""
        # Simple HTML to text conversion
        text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_attachments(self, email_message):
        """Extract attachment information"""
        attachments = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_disposition = str(part.get("Content-Disposition"))
                
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            'filename': self._decode_header(filename),
                            'content_type': part.get_content_type(),
                            'size': len(part.get_payload(decode=True) or b''),
                            'content_id': part.get('Content-ID', ''),
                            'is_inline': 'inline' in content_disposition
                        })
        
        return attachments
    
    def send_email(self, to_address, subject, body, cc_address=None, bcc_address=None):
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = to_address
            msg['Subject'] = subject
            
            if cc_address:
                msg['Cc'] = cc_address
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            # Send email
            recipients = [to_address]
            if cc_address:
                recipients.append(cc_address)
            if bcc_address:
                recipients.append(bcc_address)
            
            server.send_message(msg, self.smtp_username, recipients)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def save_email_to_db(self, email_data):
        """Save email data to database"""
        try:
            # Check if email already exists
            existing_email = Email.query.filter_by(
                message_id=email_data['message_id'],
                user_id=self.user_id
            ).first()
            
            if existing_email:
                logger.info(f"Email {email_data['message_id']} already exists")
                return existing_email
            
            # Create new email
            email = Email(
                message_id=email_data['message_id'],
                user_id=self.user_id,
                from_address=email_data['from_address'],
                to_address=email_data['to_address'],
                cc_address=email_data['cc_address'],
                subject=email_data['subject'],
                body=email_data['body'],
                body_plain=email_data['body_plain'],
                body_html=email_data['body_html'],
                received_at=email_data['received_at'],
                message_size=email_data['message_size'],
                in_reply_to=email_data['in_reply_to'],
                references=email_data['references']
            )
            
            db.session.add(email)
            db.session.commit()
            
            # Save attachments
            for attachment_data in email_data['attachments']:
                attachment = EmailAttachment(
                    email_id=email.id,
                    filename=attachment_data['filename'],
                    content_type=attachment_data['content_type'],
                    size=attachment_data['size'],
                    content_id=attachment_data['content_id'],
                    is_inline=attachment_data['is_inline']
                )
                db.session.add(attachment)
            
            db.session.commit()
            
            logger.info(f"Email saved to database: {email.subject}")
            return email
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving email to database: {str(e)}")
            return None