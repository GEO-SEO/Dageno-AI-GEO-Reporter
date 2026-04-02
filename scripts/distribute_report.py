"""
报告分发模块 - 支持 Slack、飞书和邮件分发
"""
import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Optional

class ReportDistributor:
    """报告分发器类"""

    def __init__(self):
        self.last_error = None

    def distribute_to_slack(self, report_content: str, webhook_url: str) -> bool:
        """通过 Slack Webhook 发送报告"""
        if not webhook_url or not webhook_url.startswith('http'):
            self.last_error = "Invalid Slack webhook URL"
            print(f"Error: {self.last_error}")
            return False

        # 格式化消息（Slack 限制消息大小，分割长消息）
        max_message_length = 30000

        if len(report_content) > max_message_length:
            print(f"Warning: Report content exceeds Slack limit. Splitting into multiple messages...")
            chunks = self._split_content(report_content, max_message_length)
        else:
            chunks = [report_content]

        success = True
        for i, chunk in enumerate(chunks):
            payload = {
                "text": f"📊 DagenoAI GEO 报告 (Part {i+1}/{len(chunks)})\n\n{chunk}"
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
        """通过飞书 Webhook 发送报告"""
        if not webhook_url or not webhook_url.startswith('http'):
            self.last_error = "Invalid Feishu webhook URL"
            print(f"Error: {self.last_error}")
            return False

        # 飞书消息限制
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
                    "text": f"📊 DagenoAI GEO 报告 (Part {i+1}/{len(chunks)})\n\n{chunk}"
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
        """通过 SMTP 发送邮件报告"""
        if not all([smtp_server, sender_email, sender_password, recipient_email]):
            self.last_error = "Missing email configuration"
            print(f"Error: {self.last_error}")
            return False

        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header('DagenoAI GEO 报告', 'utf-8')
            msg['From'] = sender_email
            msg['To'] = recipient_email

            # 添加纯文本版本
            text_content = self._markdown_to_text(report_content)
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))

            # 添加 HTML 版本
            html_content = self._markdown_to_html(report_content)
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # 发送邮件
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
        """将内容分割为多个块"""
        chunks = []
        lines = content.split('\n')
        current_chunk = []

        for line in lines:
            # 检查添加这一行是否超过限制
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
        """将 Markdown 转换为纯文本"""
        import re

        # 移除图片
        text = re.sub(r'!\[.*?\]\(.*?\)', '', markdown)
        # 移除标题标记
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        # 移除粗体和斜体标记
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        # 移除链接
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        # 移除水平线
        text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)

        return text.strip()

    def _markdown_to_html(self, markdown: str) -> str:
        """将 Markdown 转换为 HTML"""
        import re

        html = markdown

        # 转换标题
        html = re.sub(r'^### (.*)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # 转换图片
        html = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1" />', html)

        # 转换链接
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)

        # 转换列表
        html = re.sub(r'^- (.*)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'<li>(.*)</li>\n<li>', r'<li>\1</li><li>', html)
        html = re.sub(r'</li>\n(?!<li>)', '</li><br>', html)

        # 转换段落
        paragraphs = html.split('\n\n')
        html = '</p><p>'.join([p.strip() for p in paragraphs if p.strip()])

        # 清理
        html = re.sub(r'\n', '<br>', html)
        html = f'<html><body><p>{html}</p></body></html>'

        return html

    def get_last_error(self) -> Optional[str]:
        """获取最近的错误信息"""
        return self.last_error


def distribute_report(
    report_content: str,
    distribution_type: str,
    webhook_url: str = None,
    email_address: str = None,
    smtp_config: dict = None
) -> bool:
    """
    分发报告到指定渠道

    Args:
        report_content: 报告内容
        distribution_type: 分发类型 (slack, feishu, email)
        webhook_url: Webhook URL (用于 Slack/飞书)
        email_address: 邮箱地址 (用于邮件)
        smtp_config: SMTP 配置字典，包含 smtp_server, smtp_port, sender_email, sender_password

    Returns:
        是否成功分发
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
            print("Please configure SMTP settings: smtp_server, smtp_port, sender_email, sender_password")
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


# 示例用法
if __name__ == '__main__':
    test_report = """
    # DagenoAI GEO 报告

    ## 品牌基础信息
    - 品牌名称: Example Brand
    - 品牌域名: example.com

    ## 可见度分析
    这是测试报告的内容。
    """

    # Slack 示例（需要真实的 webhook URL）
    # distribute_report(test_report, "slack", webhook_url="https://hooks.slack.com/services/...")

    # 飞书示例（需要真实的 webhook URL）
    # distribute_report(test_report, "feishu", webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/...")

    # 邮件示例
    # smtp_config = {
    #     'smtp_server': 'smtp.gmail.com',
    #     'smtp_port': 587,
    #     'sender_email': 'your-email@gmail.com',
    #     'sender_password': 'your-app-password'
    # }
    # distribute_report(test_report, "email", email_address="recipient@example.com", smtp_config=smtp_config)

    print("Report distributor module loaded. Configure webhook URLs or SMTP settings for distribution.")