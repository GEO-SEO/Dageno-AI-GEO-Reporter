"""
Report Distribution Module - Supports Slack, Feishu, and Email distribution
"""
import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Optional

class ReportDistributor:
    """Report Distributor Class"""

    def __init__(self):
        self.last_error = None

    def distribute_to_slack(self, report_content: str, webhook_url: str) -> bool:
        """Send report via Slack Webhook"""
        if not webhook_url or not webhook_url.startswith('http'):
            self.last_error = "Invalid Slack webhook URL"
            print(f"Error: {self.last_error}")
            return False

        # Format message (Slack limits message size, split long messages)
        max_message_length = 30000

        if len(report_content) > max_message_length:
            print(f"Warning: Report content exceeds Slack limit. Splitting into multiple messages...")
            chunks = self._split_content(report_content, max_message_length)
        else:
            chunks = [report_content]

        success = True
        for i, chunk in enumerate(chunks):
            payload = {
                "text": f"📊 DagenoAI GEO Report (Part {i+1}/{len(chunks)})\n\n{chunk}"
            }
            headers = {"Content-type": "application/json"}

            try:
                response = requests.post(webhook_url, json=payload, headers=headers, timeout=30)
                response.raise_for_status()
                print(f"Part {i+1}/{len(chunks)} sent to Slack successfully")
            except requests.exceptions.Timeout:
                self.last_error = f"Slack webhook timeout for part {i+1}"
                print(f"Error: {self.last_error}")
                success = False
            except requests.exceptions.RequestException as e:
                self.last_error = f"Error sending to Slack: {str(e)}"
                print(f"Error: {self.last_error}")
                success = False

        return success

    def distribute_to_feishu(self, report_content: str, webhook_url: str) -> bool:
        """Send report via Feishu Webhook"""
        if not webhook_url or not webhook_url.startswith('http'):
            self.last_error = "Invalid Feishu webhook URL"
            print(f"Error: {self.last_error}")
            return False

        # Feishu message limits
        max_message_length = 4000

        if len(report_content) > max_message_length:
            print(f"Warning: Report content exceeds Feishu limit. Splitting into multiple messages...")
            chunks = self._split_content(report_content, max_message_length)
        else:
            chunks = [report_content]

        success = True
        for i, chunk in enumerate(chunks):
            payload = {
                "msg_type": "text",
                "content": {
                    "text": f"📊 DagenoAI GEO Report (Part {i+1}/{len(chunks)})\n\n{chunk}"
                }
            }
            headers = {"Content-type": "application/json"}

            try:
                response = requests.post(webhook_url, json=payload, headers=headers, timeout=30)
                response.raise_for_status()
                print(f"Part {i+1}/{len(chunks)} sent to Feishu successfully")
            except requests.exceptions.Timeout:
                self.last_error = f"Feishu webhook timeout for part {i+1}"
                print(f"Error: {self.last_error}")
                success = False
            except requests.exceptions.RequestException as e:
                self.last_error = f"Error sending to Feishu: {str(e)}"
                print(f"Error: {self.last_error}")
                success = False

        return success

    def distribute_to_email(
        self,
        report_content: str,
        smtp_server: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
        recipient_email: str
    ) -> bool:
        """Send email report via SMTP"""
        if not all([smtp_server, sender_email, sender_password, recipient_email]):
            self.last_error = "Missing email configuration"
            print(f"Error: {self.last_error}")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header('DagenoAI GEO Report', 'utf-8')
            msg['From'] = sender_email
            msg['To'] = recipient_email

            # Add plain text version
            text_content = self._markdown_to_text(report_content)
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))

            # Add HTML version
            html_content = self._markdown_to_html(report_content)
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # Send email
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()

            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [recipient_email], msg.as_string())
            server.quit()

            print(f"Email sent to {recipient_email} successfully")
            return True

        except smtplib.SMTPAuthenticationError:
            self.last_error = "Email authentication failed"
            print(f"Error: {self.last_error}")
            return False
        except smtplib.SMTPException as e:
            self.last_error = f"SMTP error: {str(e)}"
            print(f"Error: {self.last_error}")
            return False
        except Exception as e:
            self.last_error = f"Error sending email: {str(e)}"
            print(f"Error: {self.last_error}")
            return False

    def _split_content(self, content: str, max_length: int) -> list:
        """Split content into multiple chunks"""
        chunks = []
        lines = content.split('\n')
        current_chunk = []

        for line in lines:
            # Check if adding this line exceeds the limit
            potential = '\n'.join(current_chunk + [line])
            if len(potential) > max_length and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
            else:
                current_chunk.append(line)

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def _markdown_to_text(self, markdown: str) -> str:
        """Convert Markdown to plain text"""
        import re

        # Remove images
        text = re.sub(r'!\[.*?\]\(.*?\)', '', markdown)
        # Remove header markers
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        # Remove bold and italic markers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        # Remove links
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        # Remove horizontal rules
        text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)

        return text.strip()

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert Markdown to HTML"""
        import re

        html = markdown

        # Convert headers
        html = re.sub(r'^### (.*)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Convert images
        html = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1" />', html)

        # Convert links
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)

        # Convert lists
        html = re.sub(r'^- (.*)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'<li>(.*)</li>\n<li>', r'<li>\1</li><li>', html)
        html = re.sub(r'</li>\n(?!<li>)', '</li><br>', html)

        # Convert paragraphs
        paragraphs = html.split('\n\n')
        html = '</p><p>'.join([p.strip() for p in paragraphs if p.strip()])

        # Cleanup
        html = re.sub(r'\n', '<br>', html)
        html = f'<html><body><p>{html}</p></body></html>'

        return html

    def get_last_error(self) -> Optional[str]:
        """Get the most recent error message"""
        return self.last_error


def distribute_report(
    report_content: str,
    distribution_type: str,
    webhook_url: str = None,
    email_address: str = None,
    smtp_config: dict = None
) -> bool:
    """
    Distribute report to specified channel

    Args:
        report_content: Report content
        distribution_type: Distribution type (slack, feishu, email)
        webhook_url: Webhook URL (for Slack/Feishu)
        email_address: Email address (for Email)
        smtp_config: SMTP configuration dictionary
    
    Returns:
        Whether distribution was successful
    """
    distributor = ReportDistributor()

    if distribution_type == "slack":
        if not webhook_url:
            print("Error: Slack distribution requires a webhook_url")
            return False
        print(f"Distributing report to Slack: {webhook_url[:50]}...")
        return distributor.distribute_to_slack(report_content, webhook_url)

    elif distribution_type == "feishu":
        if not webhook_url:
            print("Error: Feishu distribution requires a webhook_url")
            return False
        print(f"Distributing report to Feishu: {webhook_url[:50]}...")
        return distributor.distribute_to_feishu(report_content, webhook_url)

    elif distribution_type == "email":
        if not email_address:
            print("Error: Email distribution requires an email_address")
            return False

        if not smtp_config:
            print("Error: Email distribution requires smtp_config")
            return False

        print(f"Sending email to {email_address}...")
        return distributor.distribute_to_email(
            report_content,
            smtp_config['smtp_server'],
            smtp_config['smtp_port'],
            smtp_config['sender_email'],
            smtp_config['sender_password'],
            email_address
        )

    else:
        print(f"Error: Unsupported distribution type: {distribution_type}")
        return False


# Example usage
if __name__ == '__main__':
    test_report = """
    # DagenoAI GEO Report

    ## Brand Basic Information
    - Brand Name: Example Brand
    - Brand Domain: example.com

    ## Visibility Analysis
    This is test report content.
    """

    # Slack Example
    # distribute_report(test_report, "slack", webhook_url="https://hooks.slack.com/services/...")

    # Feishu Example
    # distribute_report(test_report, "feishu", webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/...")

    # Email Example
    # smtp_config = {
    #     'smtp_server': 'smtp.gmail.com',
    #     'smtp_port': 587,
    #     'sender_email': 'your-email@gmail.com',
    #     'sender_password': 'your-app-password'
    # }
    # distribute_report(test_report, "email", email_address="recipient@example.com", smtp_config=smtp_config)

    print("Report distributor module loaded.")
