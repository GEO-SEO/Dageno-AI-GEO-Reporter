"""
Fetch all API data for the new report template
"""
import requests
import json
import os
from datetime import datetime, timedelta

BASE_URL = "https://api.dageno.ai/business/api/v1/open-api"
API_KEY = "sk_358PomyokdrfKhdJZSaFke10rFwrkwny1tCGm3N4aWCQb9iKiG8HQLDT0l4Coyxx"

def call_dageno_api(endpoint: str, method: str = "GET", params: dict = None, json_data: dict = None):
    """Calls the DagenoAI Open API and returns the JSON response."""
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    url = f"{BASE_URL}/{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json_data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling DagenoAI API for {endpoint}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        return None

def get_brand_info():
    return call_dageno_api("brand")

def get_geo_analysis_summary(start_at: str, end_at: str):
    json_data = {
        "target": {
            "entity": "brand",
            "metrics": ["visibility", "citation", "sentiment"],
            "filters": {
                "dateRange": {
                    "startAt": f"{start_at}T00:00:00.000Z",
                    "endAt": f"{end_at}T23:59:59.999Z"
                }
            }
        },
        "analysis": {
            "type": "summary"
        }
    }
    return call_dageno_api("geo/analysis", method="POST", json_data=json_data)

def get_geo_analysis_trend(start_at: str, end_at: str):
    json_data = {
        "target": {
            "entity": "brand",
            "metrics": ["visibility", "citation", "sentiment"],
            "filters": {
                "dateRange": {
                    "startAt": f"{start_at}T00:00:00.000Z",
                    "endAt": f"{end_at}T23:59:59.999Z"
                }
            }
        },
        "analysis": {
            "type": "trend"
        }
    }
    return call_dageno_api("geo/analysis", method="POST", json_data=json_data)

def get_geo_analysis_ranking(start_at: str, end_at: str):
    json_data = {
        "target": {
            "entity": "brand",
            "metrics": ["visibility", "citation"],
            "filters": {
                "dateRange": {
                    "startAt": f"{start_at}T00:00:00.000Z",
                    "endAt": f"{end_at}T23:59:59.999Z"
                }
            }
        },
        "analysis": {
            "type": "ranking",
            "ranking": {
                "orderBy": "visibility",
                "direction": "desc"
            }
        }
    }
    return call_dageno_api("geo/analysis", method="POST", json_data=json_data)

def get_topics(start_at: str, end_at: str, page: int = 1, pageSize: int = 20):
    params = {
        "page": page,
        "pageSize": pageSize,
        "startAt": f"{start_at}T00:00:00.000Z",
        "endAt": f"{end_at}T23:59:59.999Z"
    }
    return call_dageno_api("topics", params=params)

def get_topic_trend(start_at: str, end_at: str):
    json_data = {
        "target": {
            "entity": "topic",
            "metrics": ["visibility", "sentiment", "citation"],
            "filters": {
                "dateRange": {
                    "startAt": f"{start_at}T00:00:00.000Z",
                    "endAt": f"{end_at}T23:59:59.999Z"
                }
            }
        },
        "analysis": {
            "type": "trend"
        }
    }
    return call_dageno_api("geo/analysis", method="POST", json_data=json_data)

def get_topic_ranking(start_at: str, end_at: str):
    json_data = {
        "target": {
            "entity": "topic",
            "metrics": ["visibility", "sentiment", "citation"],
            "filters": {
                "dateRange": {
                    "startAt": f"{start_at}T00:00:00.000Z",
                    "endAt": f"{end_at}T23:59:59.999Z"
                }
            }
        },
        "analysis": {
            "type": "ranking",
            "ranking": {
                "orderBy": "visibility",
                "direction": "desc"
            }
        }
    }
    return call_dageno_api("geo/analysis", method="POST", json_data=json_data)

def get_prompts(start_at: str, end_at: str, page: int = 1, pageSize: int = 10):
    params = {
        "page": page,
        "pageSize": pageSize,
        "startAt": f"{start_at}T00:00:00.000Z",
        "endAt": f"{end_at}T23:59:59.999Z"
    }
    return call_dageno_api("prompts", params=params)

def get_citation_domains(start_at: str, end_at: str, page: int = 1, pageSize: int = 10):
    params = {
        "page": page,
        "pageSize": pageSize,
        "startAt": f"{start_at}T00:00:00.000Z",
        "endAt": f"{end_at}T23:59:59.999Z"
    }
    return call_dageno_api("citations/domains", params=params)

def get_citation_urls(start_at: str, end_at: str, page: int = 1, pageSize: int = 10):
    params = {
        "page": page,
        "pageSize": pageSize,
        "startAt": f"{start_at}T00:00:00.000Z",
        "endAt": f"{end_at}T23:59:59.999Z"
    }
    return call_dageno_api("citations/urls", params=params)

def get_content_opportunities(start_at: str, end_at: str, page: int = 1, pageSize: int = 10):
    params = {
        "page": page,
        "pageSize": pageSize,
        "startAt": f"{start_at}T00:00:00.000Z",
        "endAt": f"{end_at}T23:59:59.999Z"
    }
    return call_dageno_api("opportunities/content", params=params)

def get_backlink_opportunities(start_at: str, end_at: str, page: int = 1, pageSize: int = 10):
    params = {
        "page": page,
        "pageSize": pageSize,
        "startAt": f"{start_at}T00:00:00.000Z",
        "endAt": f"{end_at}T23:59:59.999Z"
    }
    return call_dageno_api("opportunities/backlink", params=params)

def get_community_opportunities(start_at: str, end_at: str, page: int = 1, pageSize: int = 10):
    params = {
        "page": page,
        "pageSize": pageSize,
        "startAt": f"{start_at}T00:00:00.000Z",
        "endAt": f"{end_at}T23:59:59.999Z"
    }
    return call_dageno_api("opportunities/community", params=params)

def get_platform_ranking(start_at: str, end_at: str):
    json_data = {
        "target": {
            "entity": "platform",
            "metrics": ["visibility", "citation"],
            "filters": {
                "dateRange": {
                    "startAt": f"{start_at}T00:00:00.000Z",
                    "endAt": f"{end_at}T23:59:59.999Z"
                }
            }
        },
        "analysis": {
            "type": "ranking",
            "ranking": {
                "orderBy": "visibility",
                "direction": "desc"
            }
        }
    }
    return call_dageno_api("geo/analysis", method="POST", json_data=json_data)

def main():
    # Date range: last 7 days (weekly report)
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Also get 30-day data for comparison
    start_date_30d = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"Fetching data for period: {start_date} to {end_date}")
    print(f"Fetching 30-day data for: {start_date_30d} to {end_date}")
    print("="*60)

    all_data = {}

    # 1. Brand Info
    print("\n[1/15] Fetching brand info...")
    brand_info = get_brand_info()
    all_data['brand_info'] = brand_info
    print(f"  Brand: {brand_info.get('data', {}).get('name', 'N/A')}")

    # 2. Brand Summary (last 7 days)
    print("\n[2/15] Fetching brand summary (7 days)...")
    brand_summary_7d = get_geo_analysis_summary(start_date, end_date)
    all_data['brand_summary_7d'] = brand_summary_7d

    # 3. Brand Trend (last 7 days)
    print("\n[3/15] Fetching brand trend (7 days)...")
    brand_trend_7d = get_geo_analysis_trend(start_date, end_date)
    all_data['brand_trend_7d'] = brand_trend_7d

    # 4. Brand Trend (30 days)
    print("\n[4/15] Fetching brand trend (30 days)...")
    brand_trend_30d = get_geo_analysis_trend(start_date_30d, end_date)
    all_data['brand_trend_30d'] = brand_trend_30d

    # 5. Brand Ranking
    print("\n[5/15] Fetching brand ranking...")
    brand_ranking = get_geo_analysis_ranking(start_date, end_date)
    all_data['brand_ranking'] = brand_ranking

    # 6. Topics Summary
    print("\n[6/15] Fetching topics...")
    topics = get_topics(start_date, end_date)
    all_data['topics'] = topics

    # 7. Topic Trend
    print("\n[7/15] Fetching topic trend...")
    topic_trend = get_topic_trend(start_date, end_date)
    all_data['topic_trend'] = topic_trend

    # 8. Topic Ranking
    print("\n[8/15] Fetching topic ranking...")
    topic_ranking = get_topic_ranking(start_date, end_date)
    all_data['topic_ranking'] = topic_ranking

    # 9. Prompts
    print("\n[9/15] Fetching prompts...")
    prompts = get_prompts(start_date, end_date)
    all_data['prompts'] = prompts

    # 10. Citation Domains
    print("\n[10/15] Fetching citation domains...")
    citation_domains = get_citation_domains(start_date, end_date)
    all_data['citation_domains'] = citation_domains

    # 11. Citation URLs
    print("\n[11/15] Fetching citation URLs...")
    citation_urls = get_citation_urls(start_date, end_date)
    all_data['citation_urls'] = citation_urls

    # 12. Content Opportunities
    print("\n[12/15] Fetching content opportunities...")
    content_opp = get_content_opportunities(start_date, end_date)
    all_data['content_opportunities'] = content_opp

    # 13. Backlink Opportunities
    print("\n[13/15] Fetching backlink opportunities...")
    backlink_opp = get_backlink_opportunities(start_date, end_date)
    all_data['backlink_opportunities'] = backlink_opp

    # 14. Community Opportunities
    print("\n[14/15] Fetching community opportunities...")
    community_opp = get_community_opportunities(start_date, end_date)
    all_data['community_opportunities'] = community_opp

    # 15. Platform Ranking
    print("\n[15/15] Fetching platform ranking...")
    platform_ranking = get_platform_ranking(start_date, end_date)
    all_data['platform_ranking'] = platform_ranking

    # Save all data to JSON
    output_file = "all_api_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"All data saved to: {output_file}")
    print(f"Report period: {start_date} to {end_date}")
    print(f"Comparison period (30d): {start_date_30d} to {end_date}")

    return all_data

if __name__ == "__main__":
    main()
