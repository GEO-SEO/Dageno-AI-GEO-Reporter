---
name: dageno-geo-reporter
description: DagenoAI GEO Report Generation and Distribution. Use this skill to invoke DagenoAI Open API (GEO analysis, citation source analysis) for generating brand visibility reports, citation source analysis, and opportunity suggestions, with distribution via Webhook to Slack/Feishu or Email. Supports customizable data time range and generates visual charts.
---

# DagenoAI GEO Reporter

## Overview

This skill automates the extraction, report generation, and distribution of DagenoAI Open API data. By providing an API key, it calls core analysis functions, outputs structured and visually appealing reports, and distributes them through multiple channels with archiving capabilities.

## User Requirements

### Required Inputs

| Parameter | Required | Description |
|-----------|----------|-------------|
| **api_key** | **Yes** | DagenoAI API Key (can also be set via `X_API_KEY` environment variable) |
| **time_period** | **Yes** | Data time range (start_date and end_date in YYYY-MM-DD format) |
| **distribution_type** | No | Distribution method: `slack`, `feishu`, or `email` (Optional, if not provided, agent will directly output report) |

### Optional Inputs

| Parameter | Description |
|-----------|-------------|
| `webhook_url` | Webhook URL for Slack/Feishu distribution |
| `email_address` | Recipient email for email distribution |
| `smtp_server` | SMTP server address (e.g., smtp.gmail.com) |
| `smtp_port` | SMTP port (default: 587) |
| `smtp_user` | Sender email for SMTP |
| `smtp_password` | SMTP password or app-specific password |

## Core Features

### 1. DagenoAI Open API Data Extraction

Integrates the following Open API endpoints to fetch key data:

| API Endpoint | Function |
|--------------|----------|
| `GET /brand` | Get brand basic info (name, domain, summary, keywords, competitors) |
| `POST /geo/analysis` | Get geographic analysis data, evaluating brand visibility across regions |
| `GET /topics` | Get hot topics list with search volume |
| `GET /prompts` | Get efficient prompts list with performance scores |
| `GET /citations/domains` | Get aggregated citation domain data |
| `GET /citations/urls` | Get specific citation URL list |
| `GET /opportunities/content` | Get content opportunity suggestions |
| `GET /opportunities/backlink` | Get backlink opportunity suggestions |
| `GET /opportunities/community` | Get community opportunity suggestions |

### 2. Report Generation & Visualization

Automatically generates complete reports with data tables and visual charts:

- **Brand Visibility Report**: Summarizes GEO analysis results with brand visibility overview across different markets/regions
- **Citation Source Analysis**: Analyzes citation domain and URL data, revealing key citation patterns and source influence
- **Opportunity Suggestions Report**: Provides content, backlink, and community opportunity recommendations

Chart Features:
- Auto-detects and uses system Chinese fonts (prioritizes Noto Sans CJK SC, WenQuanYi series)
- Supports multiple data format adaptations (`{data: {items: [...]}}` or `{items: [...]}`)
- Generates horizontal bar charts (suitable for long category names) and vertical bar charts
- Charts auto-upload to CDN and embedded in reports

### 3. Report Distribution & Archiving

Supported distribution channels:

| Distribution Type | Configuration Requirements |
|-------------------|----------------------------|
| **Slack** | `--webhook_url` parameter specifies Slack Incoming Webhook URL |
| **Feishu** | `--webhook_url` parameter specifies Feishu Bot Webhook URL |
| **Email** | `--email_address` parameter specifies recipient, plus SMTP configuration |

Email distribution requires additional SMTP configuration:
- `--smtp_server`: SMTP server address (e.g., smtp.gmail.com)
- `--smtp_port`: SMTP port (default: 587)
- `--smtp_user`: Sender email
- `--smtp_password`: SMTP password or app-specific password

## Usage

### Basic Command

```bash
python /home/ubuntu/skills/dageno-geo-reporter/scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_DAGENOA_API_KEY" \
  --distribution_type "slack" \
  --webhook_url "YOUR_SLACK_WEBHOOK_URL" \
  --start_date "2026-03-01" \
  --end_date "2026-03-31"
```

### Feishu Distribution Example

```bash
python /home/ubuntu/skills/dageno-geo-reporter/scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_DAGENOA_API_KEY" \
  --distribution_type "feishu" \
  --webhook_url "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID" \
  --start_date "2026-04-01" \
  --end_date "2026-04-02"
```

### Email Distribution Example

```bash
python /home/ubuntu/skills/dageno-geo-reporter/scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_DAGENOA_API_KEY" \
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
export X_API_KEY="YOUR_DAGENOA_API_KEY"

# Run script (no --api_key parameter needed)
python /home/ubuntu/skills/dageno-geo-reporter/scripts/generate_and_distribute_reports.py \
  --distribution_type "slack" \
  --webhook_url "YOUR_SLACK_WEBHOOK_URL"
```

## Parameter Reference

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--api_key` | **Yes** | DagenoAI API Key (can also be set via `X_API_KEY` env variable) |
| `--distribution_type` | No | Distribution type: `slack`, `email`, or `feishu` (Optional, if not provided, agent will directly output report) |
| `--webhook_url` | Conditional | Required for Slack/Feishu distribution |
| `--email_address` | Conditional | Required for email distribution |
| `--smtp_server` | Conditional | Required for email distribution |
| `--smtp_port` | No | SMTP port, default 587 |
| `--smtp_user` | Conditional | Required for email distribution (sender email) |
| `--smtp_password` | Conditional | Required for email distribution |
| `--start_date` | **Yes** | Data start date (YYYY-MM-DD) |
| `--end_date` | **Yes** | Data end date (YYYY-MM-DD) |

## Scheduled Execution (Cron Job)

You can set up scheduled tasks using Manus' `create_cron_job` tool to automatically run this skill at specified intervals.

### Daily Report Example (Previous Day's Data)

```python
# Schedule daily report at 9:00 AM
create_cron_job(
    job_title="DagenoAI Daily GEO Report",
    job_instruction="""Run dageno-geo-reporter skill to generate and distribute the previous day's GEO report.

Execute the following command:
python /home/ubuntu/skills/dageno-geo-reporter/scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_API_KEY" \
  --distribution_type "feishu" \
  --webhook_url "YOUR_WEBHOOK_URL" \
  --start_date "$(date -d 'yesterday' +%Y-%m-%d)" \
  --end_date "$(date -d 'yesterday' +%Y-%m-%d)"

Replace the following with actual values:
- YOUR_API_KEY: Your DagenoAI API Key
- YOUR_WEBHOOK_URL: Your Feishu/Slack Webhook URL
""",
    cron_expression="0 0 9 * * *"  # Every day at 9:00 AM
)
```

### Weekly Report Example (Previous Week)

```python
# Schedule weekly report every Monday at 9:00 AM
create_cron_job(
    job_title="DagenoAI Weekly GEO Report",
    job_instruction="""Run dageno-geo-reporter skill to generate and distribute the previous week's GEO report.

Execute the following command:
python /home/ubuntu/skills/dageno-geo-reporter/scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_API_KEY" \
  --distribution_type "feishu" \
  --webhook_url "YOUR_WEBHOOK_URL" \
  --start_date "$(date -d '8 days ago' +%Y-%m-%d)" \
  --end_date "$(date -d '2 days ago' +%Y-%m-%d)"

Replace the following with actual values:
- YOUR_API_KEY: Your DagenoAI API Key
- YOUR_WEBHOOK_URL: Your Feishu/Slack Webhook URL
""",
    cron_expression="0 0 9 * * 1"  # Every Monday at 9:00 AM
)
```

### Cron Expression Reference

```
* * * * *
│ │ │ │ │
│ │ │ │ └─── day of week (0-7, 0 and 7 are Sunday)
│ │ │ └───── month (1-12)
│ │ └─────── day of month (1-31)
│ └───────── hour (0-23)
└─────────── minute (0-59)
```

## File Structure

```
dageno-geo-reporter/
├── SKILL.md                           # This document
├── scripts/
│   ├── dageno_mcp_client.py          # DagenoAI Open API client
│   ├── generate_charts.py            # Chart generation module
│   ├── distribute_report.py           # Report distribution module
│   └── generate_and_distribute_reports.py  # Main script
├── templates/                        # Chart template directory
│   ├── geo_visibility_bar_chart.png
│   ├── citation_domains_bar_chart.png
│   └── topics_bar_chart.png
└── references/
    └── api_reference.md              # API reference document
```

## Troubleshooting

### Chart Chinese Characters Display Issues

1. Check if Chinese fonts are installed:
   ```bash
   fc-list :lang=zh -f "%{family}\n" | head -5
   ```
2. If no Chinese fonts, install Chinese font package:
   ```bash
   sudo apt-get install fonts-noto-cjk
   ```

### Distribution Failures

1. **Invalid Slack/Feishu Webhook**:
   - Check if Webhook URL is correct
   - Confirm Webhook hasn't expired (Slack Webhooks typically don't expire)
   - Test if Webhook is working

2. **Email Send Failure**:
   - When using Gmail, generate an app-specific password (not login password)
   - Check SMTP server and port settings
   - Confirm sender email and password are correct

### API Call Failures

1. Confirm API Key is valid
2. Check network connection
3. Review detailed error messages in logs

## Dependencies

```
matplotlib>=3.5.0
requests>=2.28.0
```

Install dependencies:
```bash
pip install matplotlib requests
```
