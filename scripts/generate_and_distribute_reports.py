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
    """Configure Matplotlib style (moved to generate_charts module for compatibility)"""
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
        comp_list = [comp.get("brand", "N/A") if isinstance(comp, dict) else str(comp) for comp in competitors]
        report += f"- **Main Competitors**: {', '.join(comp_list)}\n"

    report += "\n"
    return report

def generate_visibility_analysis_report(geo_analysis_data, start_date, end_date, chart_paths):
    """Generate visibility analysis report"""
    report = f"## Visibility Analysis ({start_date} to {end_date})\n\n"

    if not geo_analysis_data or not geo_analysis_data.get("data"):
        report += "No visibility analysis data available.\n"
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

    # Handle regions data (if any)
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
                # Try to extract topic name and volume
                chart_data = []
                for item in topics_items:
                    if isinstance(item, dict):
                        # Try to find topic name and volume fields
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
                        count = item.get("citationCount") or item.get("count") or item.get("citations")
                        if domain and count is not None:
                            try:
                                chart_data.append({"domain": str(domain), "citationCount": float(count)})
                            except (ValueError, TypeError):
                                pass

                if chart_data:
                    chart_path = generate_horizontal_bar_chart(
                        chart_data,
                        x_key="citationCount",
                        y_key="domain",
                        title="Top Citation Domains",
                        xlabel="Citation Count",
                        ylabel="Domain",
                        filename="citation_domains_bar_chart.png",
                        color=CUSTOM_COLOR
                    )
                    if chart_path:
                        chart_paths.append(chart_path)
                        report += f"### Top Citation Domains Chart\n\n![Top Citation Domains Chart]({{IMG_PLACEHOLDER_citation_domains_bar_chart.png}})\n\n"

    # Handle citation URLs data
    if not urls_empty:
        citation_urls_items = citation_urls_data.get("data", {})
        if isinstance(citation_urls_items, dict):
            citation_urls_items = citation_urls_items.get("items", [])
        elif not isinstance(citation_urls_items, list):
            citation_urls_items = []

        if citation_urls_items:
            report += "### Citation URLs Analysis\n"
            report += format_json_as_markdown_table(citation_urls_items, "Citation URL Details")

            # Generate citation URLs chart
            if isinstance(citation_urls_items, list) and len(citation_urls_items) > 0:
                chart_data = []
                for item in citation_urls_items:
                    if isinstance(item, dict):
                        url = item.get("url") or item.get("link") or str(item.get("id", ""))
                        count = item.get("citationCount") or item.get("count") or item.get("citations")
                        if url and count is not None:
                            try:
                                # Truncate long URLs
                                display_url = url[:50] + "..." if len(url) > 50 else url
                                chart_data.append({"url": display_url, "citationCount": float(count)})
                            except (ValueError, TypeError):
                                pass

                if chart_data:
                    chart_path = generate_horizontal_bar_chart(
                        chart_data,
                        x_key="citationCount",
                        y_key="url",
                        title="Top Citation URLs",
                        xlabel="Citation Count",
                        ylabel="URL",
                        filename="citation_urls_bar_chart.png",
                        color=CUSTOM_COLOR
                    )
                    if chart_path:
                        chart_paths.append(chart_path)
                        report += f"### Top Citation URLs Chart\n\n![Top Citation URLs Chart]({{IMG_PLACEHOLDER_citation_urls_bar_chart.png}})\n\n"

    return report

def generate_opportunity_suggestions(content_opportunities, backlink_opportunities, community_opportunities):
    """Generate opportunity suggestions report"""
    report = "## Opportunity Suggestions\n\n"

    all_empty = (
        (not content_opportunities or not content_opportunities.get("data")) and
        (not backlink_opportunities or not backlink_opportunities.get("data")) and
        (not community_opportunities or not community_opportunities.get("data"))
    )

    if all_empty:
        report += "No opportunity suggestions data available.\n"
        return report

    # Content opportunities
    if content_opportunities and content_opportunities.get("data"):
        items = content_opportunities.get("data", {})
        if isinstance(items, dict):
            items = items.get("items", [])
        if items:
            report += "### Content Opportunities\n"
            report += format_json_as_markdown_table(items, "Content Opportunity Details")
            report += "Based on the above content opportunities, it is recommended to prioritize creating or optimizing high-priority, high-impact content to improve brand visibility and user engagement.\n\n"

    # Backlink opportunities
    if backlink_opportunities and backlink_opportunities.get("data"):
        items = backlink_opportunities.get("data", {})
        if isinstance(items, dict):
            items = items.get("items", [])
        if items:
            report += "### Backlink Opportunities\n"
            report += format_json_as_markdown_table(items, "Backlink Opportunity Details")
            report += "Based on the above backlink opportunities, it is recommended to actively cooperate with high-authority domains to acquire quality backlinks and improve search engine rankings.\n\n"

    # Community opportunities
    if community_opportunities and community_opportunities.get("data"):
        items = community_opportunities.get("data", {})
        if isinstance(items, dict):
            items = items.get("items", [])
        if items:
            report += "### Community Opportunities\n"
            report += format_json_as_markdown_table(items, "Community Opportunity Details")
            report += "Based on the above community opportunities, it is recommended to actively participate in discussions on active community platforms (such as Reddit, LinkedIn groups) and share valuable content to expand brand influence.\n\n"

    return report

def upload_files_and_get_cdn_urls(file_paths):
    """Upload files to CDN and return URL mapping"""
    if not file_paths:
        return {}

    # Filter non-existent files
    existing_files = [f for f in file_paths if os.path.exists(f)]
    if not existing_files:
        return {}

    command = ["manus-upload-file"] + existing_files
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=120)
        cdn_urls = {}

        for line in result.stdout.splitlines():
            if "CDN URL: " in line:
                parts = line.split("CDN URL: ")
                if len(parts) > 1:
                    cdn_url = parts[1].strip()
                    for fp in existing_files:
                        if os.path.basename(fp) in cdn_url:
                            cdn_urls[os.path.basename(fp)] = cdn_url
                            break

        print(f"Uploaded {len(cdn_urls)} files to CDN")
        return cdn_urls

    except (subprocess.CalledProcessError, PermissionError, FileNotFoundError) as e:
        print(f"Warning: CDN upload not available ({type(e).__name__}). Charts will be saved locally.")
        return {}
    except subprocess.TimeoutExpired:
        print("Warning: CDN upload timed out")
        return {}

def main():
    parser = argparse.ArgumentParser(description="Generate and distribute DagenoAI GEO reports")
    parser.add_argument("--api_key", help="DagenoAI API Key. Can also be set via X_API_KEY env variable")
    parser.add_argument("--distribution_type", required=True, choices=["slack", "email", "feishu"],
                        help="Distribution type (slack, email, feishu)")
    parser.add_argument("--webhook_url", help="Webhook URL for Slack/Feishu distribution")
    parser.add_argument("--email_address", help="Email address for email distribution")
    parser.add_argument("--start_date", help="Start date (YYYY-MM-DD), defaults to yesterday")
    parser.add_argument("--end_date", help="End date (YYYY-MM-DD), defaults to yesterday")

    # SMTP configuration parameters (for email distribution)
    parser.add_argument("--smtp_server", help="SMTP server for email distribution")
    parser.add_argument("--smtp_port", type=int, default=587, help="SMTP port (default: 587)")
    parser.add_argument("--smtp_user", help="SMTP username/email")
    parser.add_argument("--smtp_password", help="SMTP password")

    args = parser.parse_args()

    # Initialize Matplotlib style
    setup_matplotlib_style()

    # Handle dates
    today = datetime.now()
    if args.start_date:
        try:
            start_date_obj = datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            start_date_obj = today - timedelta(days=1)
    else:
        start_date_obj = today - timedelta(days=1)

    if args.end_date:
        try:
            end_date_obj = datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError:
            end_date_obj = today - timedelta(days=1)
    else:
        end_date_obj = today - timedelta(days=1)

    start_date_str = start_date_obj.strftime("%Y-%m-%d")
    end_date_str = end_date_obj.strftime("%Y-%m-%d")

    print(f"=" * 60)
    print(f"DagenoAI GEO Report Generator")
    print(f"Date Range: {start_date_str} to {end_date_str}")
    print(f"Distribution: {args.distribution_type}")
    print(f"=" * 60)

    # Get API Key
    api_key = args.api_key or os.getenv("X_API_KEY")
    if not api_key:
        print("Error: API Key is required. Set --api_key or X_API_KEY environment variable.")
        sys.exit(1)

    # Call DagenoAI API
    print("\n[1/4] Fetching data from DagenoAI API...")
    try:
        brand_info = get_brand_info(api_key=api_key)
        geo_analysis = get_geo_analysis(start_date_str, end_date_str, api_key=api_key)
        topics = get_topics(start_date_str, end_date_str, api_key=api_key)
        prompts = get_prompts(start_date_str, end_date_str, api_key=api_key)
        citation_domains = get_citation_domains(start_date_str, end_date_str, api_key=api_key)
        citation_urls = get_citation_urls(start_date_str, end_date_str, api_key=api_key)
        content_opps = get_content_opportunities(start_date_str, end_date_str, api_key=api_key)
        backlink_opps = get_backlink_opportunities(start_date_str, end_date_str, api_key=api_key)
        community_opps = get_community_opportunities(start_date_str, end_date_str, api_key=api_key)

        print("Data fetch completed.")
    except Exception as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

    # Generate report
    print("\n[2/4] Generating reports...")
    chart_paths = []

    report_parts = []
    report_parts.append(generate_brand_basics_report(brand_info))
    report_parts.append(generate_visibility_analysis_report(geo_analysis, start_date_str, end_date_str, chart_paths))
    report_parts.append(generate_topics_prompts_report(topics, prompts, start_date_str, end_date_str, chart_paths))
    report_parts.append(generate_citation_analysis_report(citation_domains, citation_urls, start_date_str, end_date_str, chart_paths))
    report_parts.append(generate_opportunity_suggestions(content_opps, backlink_opps, community_opps))

    full_report_content = "\n".join(report_parts)

    # Upload charts to CDN
    print(f"\n[3/4] Uploading {len(chart_paths)} charts to CDN...")
    cdn_url_map = upload_files_and_get_cdn_urls(chart_paths)

    # Replace image placeholders with CDN URLs
    for filename, cdn_url in cdn_url_map.items():
        placeholder = f"{{{{IMG_PLACEHOLDER_{filename}}}}}"
        full_report_content = full_report_content.replace(placeholder, cdn_url)

    # Handle non-uploaded charts (keep placeholders or remove)
    import re
    full_report_content = re.sub(r'!\[\[IMG_PLACEHOLDER_.*?\]\]\([^)]+\)', '', full_report_content)
    full_report_content = re.sub(r'!\[\]\(\{\{IMG_PLACEHOLDER_[^}]+\}\}\)', '', full_report_content)

    # Generate complete report
    full_report = f"""# DagenoAI GEO Report

**Generated At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Data Range**: {start_date_str} to {end_date_str}
**Brand Info**: {brand_info.get('data', {}).get('name', 'N/A') if brand_info and brand_info.get('data') else 'N/A'}

---

{full_report_content}

---

*This report was automatically generated by DagenoAI GEO Reporter*
"""

    # Save report
    report_filename = f"DagenoAI_GEO_Report_{start_date_str}_to_{end_date_str}.md"
    report_path = os.path.join(os.getcwd(), report_filename)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(full_report)
    print(f"Report saved to: {report_path}")

    # Distribute report
    print(f"\n[4/4] Distributing report via {args.distribution_type}...")

    smtp_config = None
    if args.distribution_type == "email":
        if args.smtp_server and args.smtp_user and args.smtp_password:
            smtp_config = {
                'smtp_server': args.smtp_server,
                'smtp_port': args.smtp_port,
                'sender_email': args.smtp_user,
                'sender_password': args.smtp_password
            }
        else:
            print("Warning: Email distribution requires SMTP configuration. Skipping distribution.")
            print("Please provide: --smtp_server, --smtp_user, --smtp_password")
            success = False
    else:
        if not args.webhook_url:
            print(f"Warning: {args.distribution_type} distribution requires --webhook_url")
            print("Report will be saved locally but not distributed.")
            success = False

    if args.distribution_type == "email" and smtp_config:
        success = distribute_report(
            full_report,
            args.distribution_type,
            webhook_url=None,
            email_address=args.email_address,
            smtp_config=smtp_config
        )
    elif args.webhook_url:
        success = distribute_report(
            full_report,
            args.distribution_type,
            webhook_url=args.webhook_url,
            email_address=args.email_address
        )
    else:
        success = False

    # Print result
    print("\n" + "=" * 60)
    if success:
        print("Report generated and distributed successfully!")
    else:
        print("Report generated (distribution skipped or failed)")
    print(f"Report file: {report_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
