# [Dageno AI](https://dageno.ai/?utm_source=georeporter&utm_medium=github) GEO Reporter

![Dageno AI GEO Reporter Banner](./banner.webp)

## Overview

This skill automates the extraction, report generation, and distribution of DagenoAI Open API data. By providing an API key, it calls core analysis functions to evaluate **Generative Engine Optimization (GEO)** performance, outputs structured and visually appealing reports, and distributes them through multiple channels with archiving capabilities.

> **Note on GEO**: In this project, **GEO** stands for **Generative Engine Optimization**, focusing on improving brand visibility and citation within AI-driven search and generative engines.

## Core Features

### 1. DagenoAI Open API Data Extraction

Integrates the following Open API endpoints to fetch key data:

| API Endpoint | Function |
|--------------|----------|
| `GET /brand` | Get basic brand information (name, domain, summary, keywords, competitors) |
| `POST /geo/analysis` | Get GEO analysis data, evaluating brand visibility across generative engines |
| `GET /topics` | Get hot topics list and search volume |
| `GET /prompts` | Get efficient prompts list and performance scores |
| `GET /citations/domains` | Get aggregated citation domain data |
| `GET /citations/urls` | Get specific citation URL list |
| `GET /opportunities/content` | Get content opportunity suggestions for GEO |
| `GET /opportunities/backlink` | Get backlink opportunity suggestions |
| `GET /opportunities/community` | Get community opportunity suggestions |

### 2. Report Generation & Visualization

Automatically generates comprehensive reports including data tables and visual charts:

- **Brand Visibility Report**: Summarizes GEO analysis results, providing an overview of brand visibility across different AI platforms and markets.
- **Citation Source Analysis**: Analyzes citation domains and URL data to reveal key citation patterns and source influence.
- **Opportunity Suggestions Report**: Provides recommendations for content, backlinks, and community engagement to optimize for generative engines.

Chart Features:
- Automatically detects and uses system fonts.
- Supports various data format adaptations (`{data: {items: [...]}}` or `{items: [...]}`).
- Generates horizontal bar charts (for long category names) and vertical bar charts.
- Charts are automatically embedded in the reports.

### 3. Report Distribution & Archiving

Supported distribution channels:

| Distribution Type | Configuration Requirements |
|-------------------|----------------------------|
| **Slack** | `--webhook_url` parameter specifies the Slack Incoming Webhook URL |
| **Feishu** | `--webhook_url` parameter specifies the Feishu Bot Webhook URL |
| **Email** | `--email_address` parameter specifies the recipient, along with SMTP configuration |

Email distribution requires additional SMTP configuration:
- `--smtp_server`: SMTP server address (e.g., smtp.gmail.com)
- `--smtp_port`: SMTP port (default: 587)
- `--smtp_user`: Sender email address
- `--smtp_password`: SMTP password or app-specific password

## Usage

### Basic Command
Click [here](https://dageno.ai/?utm_source=georeporter&utm_medium=github
) to get your API KEY

```bash
python scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_DAGENO_API_KEY" \
  --distribution_type "slack" \
  --webhook_url "YOUR_SLACK_WEBHOOK_URL" \
  --start_date "2026-03-01" \
  --end_date "2026-03-31"
```

### Feishu Distribution Example

```bash
python scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_DAGENO_API_KEY" \
  --distribution_type "feishu" \
  --webhook_url "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID" \
  --start_date "2026-04-01" \
  --end_date "2026-04-02"
```

### Email Distribution Example

```bash
python scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_DAGENO_API_KEY" \
  --distribution_type "email" \
  --email_address "recipient@example.com" \
  --smtp_server "smtp.gmail.com" \
  --smtp_port 587 \
  --smtp_user "your-email@gmail.com" \
  --smtp_password "your-app-password" \
  --start_date "2026-04-01" \
  --end_date "2026-04-02"
```

### Using Environment Variables

```bash
# Set API Key environment variable
export X_API_KEY="YOUR_DAGENO_API_KEY"

# Run script (no --api_key parameter needed)
python scripts/generate_and_distribute_reports.py \
  --distribution_type "slack" \
  --webhook_url "YOUR_SLACK_WEBHOOK_URL"
```

## Parameter Reference

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--api_key` | **Yes** | DagenoAI API Key (can also be set via `X_API_KEY` environment variable) |
| `--distribution_type` | No | Distribution type: `slack`, `email`, or `feishu` (Optional; if not provided, the report is output directly) |
| `--webhook_url` | Conditional | Required for Slack/Feishu distribution |
| `--email_address` | Conditional | Required for email distribution |
| `--smtp_server` | Conditional | Required for email distribution |
| `--smtp_port` | No | SMTP port, default 587 |
| `--smtp_user` | Conditional | Required for email distribution (sender email) |
| `--smtp_password` | Conditional | Required for email distribution |
| `--start_date` | **Yes** | Data start date (YYYY-MM-DD) |
| `--end_date` | **Yes** | Data end date (YYYY-MM-DD) |

## Scheduled Execution (Cron Job)

You can use Manus's `create_cron_job` tool to set up scheduled tasks to run this skill automatically at specified intervals.

### Daily Report Example (Previous Day's Data)

```python
# Schedule daily report at 9:00 AM
create_cron_job(
    job_title="DagenoAI Daily GEO Report",
    job_instruction="""Run the dageno-geo-reporter skill to generate and distribute the previous day's GEO report.

Execute the following command:
python /home/ubuntu/skills/dageno-geo-reporter/scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_API_KEY" \
  --distribution_type "feishu" \
  --webhook_url "YOUR_WEBHOOK_URL" \
  --start_date "$(date -d 'yesterday' +%Y-%m-%d)" \
  --end_date "$(date -d 'yesterday' +%Y-%m-%d)"

Please replace the following with actual values:
- YOUR_API_KEY: Your DagenoAI API Key
- YOUR_WEBHOOK_URL: Your Feishu/Slack Webhook URL
""",
    cron_expression="0 0 9 * * *"  # 9:00 AM daily
)
```

### Weekly Report Example (Previous Week)

```python
# Schedule weekly report every Monday at 9:00 AM
create_cron_job(
    job_title="DagenoAI Weekly GEO Report",
    job_instruction="""Run the dageno-geo-reporter skill to generate and distribute the previous week's GEO report.

Execute the following command:
python /home/ubuntu/skills/dageno-geo-reporter/scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_API_KEY" \
  --distribution_type "feishu" \
  --webhook_url "YOUR_WEBHOOK_URL" \
  --start_date "$(date -d '8 days ago' +%Y-%m-%d)" \
  --end_date "$(date -d '2 days ago' +%Y-%m-%d)"

Please replace the following with actual values:
- YOUR_API_KEY: Your DagenoAI API Key
- YOUR_WEBHOOK_URL: Your Feishu/Slack Webhook URL
""",
    cron_expression="0 0 9 * * 1"  # 9:00 AM every Monday
)
```

## File Structure

```
dageno-geo-reporter/
├── README.md                          # This document
├── SKILL.md                           # Skill definition document
├── scripts/
│   ├── dageno_mcp_client.py          # DagenoAI Open API client
│   ├── generate_charts.py            # Chart generation module
│   ├── distribute_report.py           # Report distribution module
│   └── generate_and_distribute_reports.py  # Main script
├── templates/                        # Chart templates directory
│   ├── geo_visibility_bar_chart.png
│   ├── citation_domains_bar_chart.png
│   └── topics_bar_chart.png
└── references/
    └── api_reference.md              # API reference document
```

## Troubleshooting

### Chart Font Issues

If you encounter issues with text rendering in charts, ensure that basic system fonts are available. The script will automatically fall back to available fonts like DejaVu Sans if specific CJK fonts are not found.

### Distribution Failures

1. **Invalid Slack/Feishu Webhook**:
   - Verify the Webhook URL is correct.
   - Ensure the Webhook has not expired.
   - Test the Webhook manually if possible.

2. **Email Sending Failures**:
   - For Gmail, use an App Password instead of your regular login password.
   - Verify SMTP server and port settings.
   - Ensure the sender email and password are correct.

### API Call Failures

1. Verify the API Key is valid.
2. Check your internet connection.
3. Review detailed error messages in the logs.

## Dependencies

```
matplotlib>=3.5.0
requests>=2.28.0
```

Install dependencies:
```bash
pip install matplotlib requests
```
