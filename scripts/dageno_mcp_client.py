
import requests
import json
import os
from datetime import datetime, timedelta

BASE_URL = "https://api.dageno.ai/business/api/v1/open-api"

def call_dageno_api(api_key: str, endpoint: str, method: str = "GET", params: dict = None, json_data: dict = None):
    """Calls the DagenoAI Open API and returns the JSON response."""
    if not api_key:
        import os
        api_key = os.getenv("X_API_KEY")
        if not api_key: raise ValueError("API Key is required. Please provide it as an argument or set the X_API_KEY environment variable.")
    headers = {
        "x-api-key": api_key,
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

        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling DagenoAI API for {endpoint}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        return None

def get_brand_info(api_key: str = None):
    return call_dageno_api(api_key, "brand")

def get_geo_analysis(start_at: str, end_at: str, api_key: str = None):
    json_data = {
        "target": {
            "entity": "brand",
            "metrics": [
                "visibility",
                "citation"
            ],
            "filters": {
                "dateRange": {
                    "startAt": f"{start_at}T00:00:00.000Z",
                    "endAt": f"{end_at}T00:00:00.000Z"
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
    return call_dageno_api(api_key, "geo/analysis", method="POST", json_data=json_data)

def get_topics(start_at: str, end_at: str, page: int = 1, pageSize: int = 10, api_key: str = None):
    params = {
        "page": page,
        "pageSize": pageSize,
        "startAt": f"{start_at}T00:00:00.000Z",
        "endAt": f"{end_at}T00:00:00.000Z"
    }
    return call_dageno_api(api_key, "topics", params=params)

def get_prompts(start_at: str, end_at: str, page: int = 1, pageSize: int = 10, api_key: str = None):
    params = {
        "page": page,
        "pageSize": pageSize,
        "startAt": f"{start_at}T00:00:00.000Z",
        "endAt": f"{end_at}T00:00:00.000Z"
    }
    return call_dageno_api(api_key, "prompts", params=params)

def get_citation_domains(start_at: str, end_at: str, page: int = 1, pageSize: int = 10, api_key: str = None):
    params = {
        "page": page,
        "pageSize": pageSize,
        "startAt": f"{start_at}T00:00:00.000Z",
        "endAt": f"{end_at}T00:00:00.000Z"
    }
    return call_dageno_api(api_key, "citations/domains", params=params)

def get_citation_urls(start_at: str, end_at: str, page: int = 1, pageSize: int = 10, api_key: str = None):
    params = {
        "page": page,
        "pageSize": pageSize,
        "startAt": f"{start_at}T00:00:00.000Z",
        "endAt": f"{end_at}T00:00:00.000Z"
    }
    return call_dageno_api(api_key, "citations/urls", params=params)

def get_content_opportunities(start_at: str, end_at: str, page: int = 1, pageSize: int = 10, api_key: str = None):
    params = {
        "page": page,
        "pageSize": pageSize,
        "startAt": f"{start_at}T00:00:00.000Z",
        "endAt": f"{end_at}T00:00:00.000Z"
    }
    return call_dageno_api(api_key, "opportunities/content", params=params)

def get_backlink_opportunities(start_at: str, end_at: str, page: int = 1, pageSize: int = 10, api_key: str = None):
    params = {
        "page": page,
        "pageSize": pageSize,
        "startAt": f"{start_at}T00:00:00.000Z",
        "endAt": f"{end_at}T00:00:00.000Z"
    }
    return call_dageno_api(api_key, "opportunities/backlink", params=params)

def get_community_opportunities(start_at: str, end_at: str, page: int = 1, pageSize: int = 10, api_key: str = None):
    params = {
        "page": page,
        "pageSize": pageSize,
        "startAt": f"{start_at}T00:00:00.000Z",
        "endAt": f"{end_at}T00:00:00.000Z"
    }
    return call_dageno_api(api_key, "opportunities/community", params=params)

if __name__ == '__main__':
    # api_key = "sk_536PomxokdrfKhdJZSaFke10rFwrkwny2tCGm3N4aWCQb9iKiG8HQLDT0l4CojDi" # Removed for flexibility
    api_key = os.getenv("X_API_KEY")
    if not api_key: raise ValueError("API Key is required for testing.")
    test_start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    test_end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    print("Testing get_brand_info...")
    brand_info = get_brand_info(api_key=api_key)
    if brand_info:
        print("Brand Info:")
        print(json.dumps(brand_info, indent=2, ensure_ascii=False))

    print("Testing get_geo_analysis...")
    geo_analysis = get_geo_analysis(test_start_date, test_end_date, api_key=api_key)
    if geo_analysis:
        print("GEO Analysis:")
        print(json.dumps(geo_analysis, indent=2, ensure_ascii=False))

    print("Testing get_topics...")
    topics = get_topics(test_start_date, test_end_date, api_key=api_key)
    if topics:
        print("Topics:")
        print(json.dumps(topics, indent=2, ensure_ascii=False))

    print("Testing get_prompts...")
    prompts = get_prompts(test_start_date, test_end_date, api_key=api_key)
    if prompts:
        print("Prompts:")
        print(json.dumps(prompts, indent=2, ensure_ascii=False))

    print("Testing get_citation_domains...")
    citation_domains = get_citation_domains(test_start_date, test_end_date, api_key=api_key)
    if citation_domains:
        print("Citation Domains:")
        print(json.dumps(citation_domains, indent=2, ensure_ascii=False))

    print("Testing get_citation_urls...")
    citation_urls = get_citation_urls(test_start_date, test_end_date, api_key=api_key)
    if citation_urls:
        print("Citation URLs:")
        print(json.dumps(citation_urls, indent=2, ensure_ascii=False))

    print("Testing get_content_opportunities...")
    content_opportunities = get_content_opportunities(test_start_date, test_end_date, api_key=api_key)
    if content_opportunities:
        print("Content Opportunities:")
        print(json.dumps(content_opportunities, indent=2, ensure_ascii=False))

    print("Testing get_backlink_opportunities...")
    backlink_opportunities = get_backlink_opportunities(test_start_date, test_end_date, api_key=api_key)
    if backlink_opportunities:
        print("Backlink Opportunities:")
        print(json.dumps(backlink_opportunities, indent=2, ensure_ascii=False))

    print("Testing get_community_opportunities...")
    community_opportunities = get_community_opportunities(test_start_date, test_end_date, api_key=api_key)
    if community_opportunities:
        print("Community Opportunities:")
        print(json.dumps(community_opportunities, indent=2, ensure_ascii=False))
