---
name: dageno-geo-reporter
description: DagenoAI GEO Report Generation and Distribution. Use this skill to invoke DagenoAI Open API (GEO analysis, citation source analysis) for generating brand visibility reports, citation source analysis, and opportunity suggestions for Generative Engine Optimization (GEO). Supports distribution via Webhook to Slack/Feishu or Email, customizable data time ranges, and visual charts.
---

# DagenoAI GEO Reporter

## Overview

This skill automates the extraction, report generation, and distribution of DagenoAI Open API data. By providing an API key, it calls core analysis functions to evaluate **Generative Engine Optimization (GEO)** performance, outputs structured and visually appealing reports, and distributes them through multiple channels with archiving capabilities.

> **Note on GEO**: In this project, **GEO** stands for **Generative Engine Optimization**, focusing on improving brand visibility and citation within AI-driven search and generative engines.

## User Requirements

### Required Inputs

| Parameter | Required | Description |
|-----------|----------|-------------|
| **api_key** | **Yes** | DagenoAI API Key (can also be set via `X_API_KEY` environment variable) |
| **time_period** | **Yes** | Data time range (start_date and end_date in YYYY-MM-DD format) |
| **report_format** | No | Output format: `html` (default) or `plain_text`. Users can choose between rendered HTML report or plain text markdown format. |
| **distribution_type** | No | Distribution method: `slack`, `feishu`, or `email` (Optional; if not provided, the report is output directly) |

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
| `POST /geo/analysis` | Get GEO analysis data, evaluating brand visibility across generative engines |
| `GET /topics` | Get hot topics list with search volume |
| `GET /prompts` | Get efficient prompts list with performance scores |
| `GET /citations/domains` | Get aggregated citation domain data |
| `GET /citations/urls` | Get specific citation URL list |
| `GET /opportunities/content` | Get content opportunity suggestions for GEO |
| `GET /opportunities/backlink` | Get backlink opportunity suggestions |
| `GET /opportunities/community` | Get community opportunity suggestions |

### 2. Report Generation & Visualization

Automatically generates complete reports with data tables and visual charts:

- **Brand Visibility Report**: Summarizes GEO analysis results with brand visibility overview across different AI platforms and regions.
- **Citation Source Analysis**: Analyzes citation domain and URL data, revealing key citation patterns and source influence.
- **Opportunity Suggestions Report**: Provides content, backlink, and community opportunity recommendations for generative engine optimization.

#### Report Format Options

Users can choose between two output formats:

| Format | Description |
|--------|-------------|
| **HTML** (default) | Rendered HTML report with interactive charts, modern flat UI design, white background with black text and #ff5c23 accent color. Professional and visually appealing format suitable for presentations. |
| **Plain Text** | Traditional markdown format. Lightweight and compatible with all platforms, suitable for email distribution and text-based workflows. |

#### HTML Report Design Specifications

The HTML report follows these design standards:
- **Color Scheme**: White background (#ffffff), black text (#1a1a2e), orange accent (#ff5c23)
- **Typography**: Inter font family
- **Layout**: Flat, modern, responsive design
- **Charts**: Interactive Chart.js visualizations including:
  - Platform visibility bar charts
  - Citation distribution doughnut charts
  - Monthly trend line charts
  - Topics horizontal bar charts
- **Features**: Executive summary, metrics cards, data tables, opportunity lists

#### Plain Text Report Specifications

The plain text report provides:
- Markdown-formatted content
- ASCII-based data tables
- Embedded chart descriptions
- Clean, text-readable layout

Chart Features:
- Auto-detects and uses system fonts.
- Supports multiple data format adaptations (`{data: {items: [...]}}` or `{items: [...]}`).
- Generates horizontal bar charts (suitable for long category names) and vertical bar charts.
- Charts are automatically embedded in the reports.

### 3. Report Distribution & Archiving

Supported distribution channels:

| Distribution Type | Configuration Requirements |
|-------------------|----------------------------|
| **Slack** | `--webhook_url` parameter specifies the Slack Incoming Webhook URL |
| **Feishu** | `--webhook_url` parameter specifies the Feishu Bot Webhook URL |
| **Email** | `--email_address` parameter specifies the recipient, plus SMTP configuration |

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

### HTML Report (Default) Example

```bash
# Generate HTML report (default format)
python /home/ubuntu/skills/dageno-geo-reporter/scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_DAGENOA_API_KEY" \
  --report_format "html" \
  --start_date "2026-03-01" \
  --end_date "2026-03-31"
```

### Plain Text Report Example

```bash
# Generate plain text markdown report
python /home/ubuntu/skills/dageno-geo-reporter/scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_DAGENOA_API_KEY" \
  --report_format "plain_text" \
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
| `--report_format` | No | Output format: `html` (default) or `plain_text` |
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

You can set up scheduled tasks using Manus's `create_cron_job` tool to automatically run this skill at specified intervals.

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
    job_instruction="""Run the dageno-geo-reporter skill to generate and distribute the previous week's GEO report.

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
├── templates/                        # Chart templates directory
│   ├── geo_visibility_bar_chart.png
│   ├── citation_domains_bar_chart.png
│   ├── topics_bar_chart.png
│   └── geo_report_template.html      # HTML report template (no logo version)
└── references/
    └── api_reference.md              # API reference document
```

## Report Samples

### HTML Report Sample

A sample HTML report is available at: `templates/geo_report_template.html`

The HTML report features:
- Modern flat UI design with white background and #ff5c23 accent color
- Interactive Chart.js visualizations
- Responsive layout for all screen sizes
- Executive summary section with key metrics
- Detailed platform performance breakdown
- Opportunity recommendations
- Citation analysis tables

### Plain Text Report Sample

```
DagenoAI GEO Report
Period: March 1 - March 31, 2026

Executive Summary
-----------------
Your brand's visibility across generative AI platforms has shown strong momentum...

Key Metrics
-----------
- GEO Score: 87.4 (+8.2%)
- AI Platform Mentions: 2,847 (+24%)
- Citation Sources: 156 (+12)
- Sentiment Positive: 94% (+3%)

Platform Visibility
-------------------
| Platform     | Mentions | Score |
|--------------|----------|-------|
| ChatGPT      | 1,284    | 92    |
| Claude       | 892      | 85    |
| Perplexity   | 423      | 78    |
| Gemini       | 248      | 64    |

... (additional sections)
```

## Troubleshooting

### Chart Font Issues

Ensure system fonts are available for chart rendering. The script will automatically fall back to available fonts like DejaVu Sans if specific CJK fonts are not found.

### Distribution Failures

1. **Invalid Slack/Feishu Webhook**:
   - Check if Webhook URL is correct.
   - Confirm Webhook hasn't expired.
   - Test if Webhook is working.

2. **Email Send Failure**:
   - For Gmail, generate an app-specific password (not login password).
   - Check SMTP server and port settings.
   - Confirm sender email and password are correct.

### API Call Failures

1. Confirm API Key is valid.
2. Check network connection.
3. Review detailed error messages in logs.

## Dependencies

```
matplotlib>=3.5.0
requests>=2.28.0
```

Install dependencies:
```bash
pip install matplotlib requests
```
