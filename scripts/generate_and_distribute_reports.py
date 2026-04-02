"""
DagenoAI GEO Report Generation and Distribution Main Script
"""
import argparse
import json
from datetime import datetime, timedelta
from dageno_mcp_client import (
    get_brand_info, get_geo_analysis, get_topics, get_prompts,
    get_citation_domains, get_citation_urls,
    get_content_opportunities, get_backlink_opportunities, get_community_opportunities
)
from distribute_report import distribute_report
from generate_charts import generate_bar_chart, generate_horizontal_bar_chart, generate_pie_chart
import os
import matplotlib.pyplot as plt
import subprocess
import sys

# Add current directory to path for module imports
sys.path.insert(0, os.path.dirname(__file__))

# Set custom colors
CUSTOM_COLOR = '#ff5c23'
CHART_PALETTE = ['#ff5c23', '#3498db', '#2ecc71', '#9b59b6', '#f39c12', '#1abc9c']

def setup_matplotlib_style():
    """Configure Matplotlib style"""
    from generate_charts import setup_matplotlib_style as _setup
    _setup()

def format_json_as_markdown_table(data, title="Data Details"):
    """Format JSON data as Markdown table"""
    if not data:
        return f"### {title}\n\nNo data available.\n"

    if isinstance(data, dict):
        data = [data]

    if not data:
        return f"### {title}\n\nNo data available.\n"

    # Handle API response format: {"data": {"items": [...]}}
    if isinstance(data, dict) and "data" in data:
        inner = data["data"]
        if isinstance(inner, dict):
            if "items" in inner:
                data = inner["items"]
            elif "metrics" in inner:
                data = inner["metrics"]
            elif isinstance(inner, list):
                data = inner
        elif isinstance(inner, list):
            data = inner
    elif isinstance(data, dict) and "items" in data:
        data = data["items"]

    if not data or not isinstance(data, list):
        return f"### {title}\n\nNo data available.\n"

    # Extract headers
    all_keys = set()
    for item in data:
        if isinstance(item, dict):
            for k, v in item.items():
                if not isinstance(v, (dict, list)):
                    all_keys.add(k)
    headers = sorted(list(all_keys))

    if not headers:
        return f"### {title}\n\nNo data available.\n"

    # Build table
    markdown_table = f"### {title}\n\n"
    markdown_table += "|" + "|".join(headers) + "|\n"
    markdown_table += "|" + "|".join(["---"] * len(headers)) + "|\n"

    for item in data:
        if not isinstance(item, dict):
            continue
        row_values = []
        for header in headers:
            value = item.get(header, "")
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)[:50]
            else:
                value = str(value)[:100]
            row_values.append(value)
        markdown_table += "|" + "|".join(row_values) + "|\n"
    markdown_table += "\n"
    return markdown_table

def generate_brand_basics_report(brand_info):
    """Generate brand basic information report"""
    report = "## Brand Basic Information\n\n"
    if not brand_info or not brand_info.get("data"):
        report += "No brand information available.\n"
        return report

    data = brand_info["data"]
    report += f"- **Brand Name**: {data.get('name', 'N/A')}\n"
    report += f"- **Brand Domain**: {data.get('domain', 'N/A')}\n"
    report += f"- **Brand Summary**: {data.get('summary', 'N/A')}\n"

    keywords = data.get("keywords", [])
    if keywords:
        report += f"- **Keywords**: {', '.join(keywords) if isinstance(keywords, list) else keywords}\n"

    competitors = data.get("competitors", [])
    if competitors:
        comp_list = [comp.get('brand', 'N/A') if isinstance(comp, dict) else str(comp) for comp in competitors]
        report += f"- **Main Competitors**: {', '.join(comp_list)}\n"

    report += "\n"
    return report

def generate_visibility_analysis_report(geo_analysis_data, start_date, end_date, chart_paths):
    """Generate visibility analysis report"""
    report = f"## GEO Visibility Analysis ({start_date} to {end_date})\n\n"

    if not geo_analysis_data or not geo_analysis_data.get("data"):
        report += "No GEO visibility analysis data available.\n"
        return report

    data = geo_analysis_data["data"]

    # Handle metrics data
    metrics = data.get("metrics", [])
    if metrics:
        report += "### GEO Analysis Overview\n"
        report += format_json_as_markdown_table(metrics, "GEO Analysis Details")

        # Generate chart
        if isinstance(metrics, list) and len(metrics) > 0:
            # Try to identify numeric metrics
            chart_data = []
            for item in metrics:
                if isinstance(item, dict):
                    for k, v in item.items():
                        if isinstance(v, (int, float)):
                            chart_data.append({"metric": k, "value": v})
                            break

            if chart_data:
                chart_path = generate_bar_chart(
                    chart_data,
                    x_key="metric",
                    y_key="value",
                    title="GEO Visibility Metrics",
                    xlabel="Metric",
                    ylabel="Value",
                    filename="geo_visibility_bar_chart.png",
                    color=CUSTOM_COLOR
                )
                if chart_path:
                    chart_paths.append(chart_path)
                    report += f"### GEO Visibility Chart\n\n![GEO Visibility Chart]({{IMG_PLACEHOLDER_geo_visibility_bar_chart.png}})\n\n"

    # Handle ranking data
    ranking = data.get("ranking", [])
    if ranking:
        report += format_json_as_markdown_table(ranking, "Ranking Details")

    # Handle regions data
    regions = data.get("regions", [])
    if regions:
        report += format_json_as_markdown_table(regions, "Region Details")

    return report

def generate_topics_prompts_report(topics_data, prompts_data, start_date, end_date, chart_paths):
    """Generate topics and prompts report"""
    report = f"## Topics and Prompts Analysis ({start_date} to {end_date})\n\n"

    topics_empty = not topics_data or not topics_data.get("data")
    prompts_empty = not prompts_data or not prompts_data.get("data")

    if topics_empty and prompts_empty:
        report += "No topics and prompts data available.\n"
        return report

    # Handle topics data
    if not topics_empty:
        topics_items = topics_data.get("data", {})
        if isinstance(topics_items, dict):
            topics_items = topics_items.get("items", topics_items.get("metrics", []))
        elif not isinstance(topics_items, list):
            topics_items = []

        if topics_items:
            report += "### Hot Topics\n"
            report += format_json_as_markdown_table(topics_items, "Topic Details")

            # Generate topics chart
            if isinstance(topics_items, list) and len(topics_items) > 0:
                chart_data = []
                for item in topics_items:
                    if isinstance(item, dict):
                        topic = item.get("topic") or item.get("name") or item.get("title") or str(item.get("id", ""))
                        volume = item.get("volume") or item.get("count") or item.get("searchVolume") or item.get("value")
                        if topic and volume is not None:
                            try:
                                chart_data.append({"topic": str(topic), "volume": float(volume)})
                            except (ValueError, TypeError):
                                pass

                if chart_data:
                    chart_path = generate_horizontal_bar_chart(
                        chart_data,
                        x_key="volume",
                        y_key="topic",
                        title="Hot Topics Search Volume",
                        xlabel="Search Volume",
                        ylabel="Topic",
                        filename="topics_bar_chart.png",
                        color=CUSTOM_COLOR
                    )
                    if chart_path:
                        chart_paths.append(chart_path)
                        report += f"### Hot Topics Chart\n\n![Hot Topics Chart]({{IMG_PLACEHOLDER_topics_bar_chart.png}})\n\n"

    # Handle prompts data
    if not prompts_empty:
        prompts_items = prompts_data.get("data", {})
        if isinstance(prompts_items, dict):
            prompts_items = prompts_items.get("items", prompts_items.get("metrics", []))
        elif not isinstance(prompts_items, list):
            prompts_items = []

        if prompts_items:
            report += "### Efficient Prompts\n"
            report += format_json_as_markdown_table(prompts_items, "Prompt Details")

    return report

def generate_citation_analysis_report(citation_domains_data, citation_urls_data, start_date, end_date, chart_paths):
    """Generate citation source analysis report"""
    report = f"## Citation Source Analysis ({start_date} to {end_date})\n\n"

    domains_empty = not citation_domains_data or not citation_domains_data.get("data")
    urls_empty = not citation_urls_data or not citation_urls_data.get("data")

    if domains_empty and urls_empty:
        report += "No citation source data available.\n"
        return report

    # Handle citation domains data
    if not domains_empty:
        citation_domains_items = citation_domains_data.get("data", {})
        if isinstance(citation_domains_items, dict):
            citation_domains_items = citation_domains_items.get("items", [])
        elif not isinstance(citation_domains_items, list):
            citation_domains_items = []

        if citation_domains_items:
            report += "### Citation Domains Analysis\n"
            report += format_json_as_markdown_table(citation_domains_items, "Citation Domain Details")

            # Generate citation domains chart
            if isinstance(citation_domains_items, list) and len(citation_domains_items) > 0:
                chart_data = []
                for item in citation_domains_items:
                    if isinstance(item, dict):
                        domain = item.get("domain") or item.get("name") or str(item.get("id", ""))
                        count = item.get("citationCount") or item.get("count") or item.get("value")
                        if domain and count is not None:
                            try:
                                chart_data.append({"domain": str(domain), "count": float(count)})
                            except (ValueError, TypeError):
                                pass

                if chart_data:
                    chart_path = generate_bar_chart(
                        chart_data,
                        x_key="domain",
                        y_key="count",
                        title="Top Citation Domains",
                        xlabel="Domain",
                        ylabel="Citations",
                        filename="citation_domains_bar_chart.png",
                        color=CUSTOM_COLOR
                    )
                    if chart_path:
                        chart_paths.append(chart_path)
                        report += f"### Citation Domains Chart\n\n![Citation Domains Chart]({{IMG_PLACEHOLDER_citation_domains_bar_chart.png}})\n\n"

    # Handle citation URLs data
    if not urls_empty:
        citation_urls_items = citation_urls_data.get("data", {})
        if isinstance(citation_urls_items, dict):
            citation_urls_items = citation_urls_items.get("items", [])
        elif not isinstance(citation_urls_items, list):
            citation_urls_items = []

        if citation_urls_items:
            report += "### Specific Citation URLs\n"
            report += format_json_as_markdown_table(citation_urls_items, "Citation URL Details")

    return report

def generate_opportunities_report(content_opp, backlink_opp, community_opp, start_date, end_date):
    """Generate opportunity suggestions report"""
    report = f"## Opportunity Suggestions ({start_date} to {end_date})\n\n"

    # Content Opportunities
    if content_opp and content_opp.get("data"):
        report += "### Content Opportunities for GEO\n"
        report += format_json_as_markdown_table(content_opp["data"], "Content Suggestions")

    # Backlink Opportunities
    if backlink_opp and backlink_opp.get("data"):
        report += "### Backlink Opportunities\n"
        report += format_json_as_markdown_table(backlink_opp["data"], "Backlink Suggestions")

    # Community Opportunities
    if community_opp and community_opp.get("data"):
        report += "### Community Opportunities\n"
        report += format_json_as_markdown_table(community_opp["data"], "Community Suggestions")

    return report

def main():
    parser = argparse.ArgumentParser(description="DagenoAI GEO Report Generation and Distribution")
    parser.add_argument("--api_key", help="DagenoAI API Key")
    parser.add_argument("--start_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--distribution_type", choices=["slack", "feishu", "email"], help="Distribution type")
    parser.add_argument("--webhook_url", help="Webhook URL for Slack/Feishu")
    parser.add_argument("--email_address", help="Recipient email address")
    parser.add_argument("--smtp_server", help="SMTP server address")
    parser.add_argument("--smtp_port", type=int, default=587, help="SMTP port")
    parser.add_argument("--smtp_user", help="SMTP user (sender email)")
    parser.add_argument("--smtp_password", help="SMTP password")

    args = parser.parse_args()

    # Get API key from env if not provided
    api_key = args.api_key or os.environ.get("X_API_KEY")
    if not api_key:
        print("Error: API Key is required (use --api_key or X_API_KEY env var)")
        sys.exit(1)

    # Use yesterday if dates not provided
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = args.start_date or yesterday
    end_date = args.end_date or yesterday

    print(f"Starting DagenoAI GEO report generation for {start_date} to {end_date}...")

    # Initialize report
    report_title = f"# DagenoAI Generative Engine Optimization (GEO) Report\n\n"
    report_title += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report_title += f"Reporting Period: {start_date} to {end_date}\n\n"
    
    report_body = ""
    chart_paths = []

    # 1. Fetch Brand Info
    print("Fetching brand info...")
    brand_info = get_brand_info(api_key)
    report_body += generate_brand_basics_report(brand_info)

    # 2. Fetch GEO Analysis
    print("Fetching GEO analysis data...")
    geo_analysis = get_geo_analysis(start_date, end_date, api_key=api_key)
    report_body += generate_visibility_analysis_report(geo_analysis, start_date, end_date, chart_paths)

    # 3. Fetch Topics and Prompts
    print("Fetching topics and prompts...")
    topics = get_topics(start_date, end_date, api_key=api_key)
    prompts = get_prompts(start_date, end_date, api_key=api_key)
    report_body += generate_topics_prompts_report(topics, prompts, start_date, end_date, chart_paths)

    # 4. Fetch Citation Analysis
    print("Fetching citation source data...")
    citation_domains = get_citation_domains(start_date, end_date, api_key=api_key)
    citation_urls = get_citation_urls(start_date, end_date, api_key=api_key)
    report_body += generate_citation_analysis_report(citation_domains, citation_urls, start_date, end_date, chart_paths)

    # 5. Fetch Opportunities
    print("Fetching opportunity suggestions...")
    content_opp = get_content_opportunities(start_date, end_date, api_key=api_key)
    backlink_opp = get_backlink_opportunities(start_date, end_date, api_key=api_key)
    community_opp = get_community_opportunities(start_date, end_date, api_key=api_key)
    report_body += generate_opportunities_report(content_opp, backlink_opp, community_opp, start_date, end_date)

    # Final Report Assembly
    full_report = report_title + report_body

    # Replace chart placeholders with local paths for distribution if needed
    # In a real scenario, you'd upload these to a CDN first
    for path in chart_paths:
        filename = os.path.basename(path)
        placeholder = f"{{{{IMG_PLACEHOLDER_{filename}}}}}"
        full_report = full_report.replace(placeholder, f"./templates/{filename}")

    # Output to file
    output_filename = f"DagenoAI_GEO_Report_{start_date}_to_{end_date}.md"
    with open(output_filename, "w") as f:
        f.write(full_report)
    print(f"Report saved to {output_filename}")

    # Distribution
    if args.distribution_type:
        smtp_config = None
        if args.distribution_type == "email":
            smtp_config = {
                "smtp_server": args.smtp_server,
                "smtp_port": args.smtp_port,
                "sender_email": args.smtp_user,
                "sender_password": args.smtp_password
            }
        
        success = distribute_report(
            full_report,
            args.distribution_type,
            webhook_url=args.webhook_url,
            email_address=args.email_address,
            smtp_config=smtp_config
        )
        
        if success:
            print(f"Report distributed successfully via {args.distribution_type}")
        else:
            print(f"Failed to distribute report via {args.distribution_type}")

if __name__ == "__main__":
    main()
