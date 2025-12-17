from dotenv import load_dotenv
import os
import json
from fastapi import FastAPI
import requests
from urllib.parse import quote_plus
from .snapshot_operations import download_snapshot, poll_snapshot_status
from bs4 import BeautifulSoup
from typing import Any, Dict
import httpx
import contextlib
from pydantic import BaseModel, Field, ValidationError
import time
import clients

load_dotenv(override=True)

dataset_id = "gd_lvz8ah06191smkebj4"

import os
import json
from typing import Any, Dict
import httpx

# -----------------------------------------------
#  Logging helper
# -----------------------------------------------
def log(message: str) -> None:
    print(f"[API] {message}")


# -----------------------------------------------
#  Pydantic Response Model
# -----------------------------------------------
class ApiResponse(BaseModel):
    knowledge: Dict[str, Any] = Field(default_factory=dict)
    organic: list = Field(default_factory=list)
    
    
# -----------------------------------------------
#  Unified JSON / HTML parsing
# -----------------------------------------------
def parse_response_text(text: str) -> Dict[str, Any]:
    """
    Tries JSON parsing first.
    If JSON fails, falls back to HTML parsing.
    Always returns a dict.
    """
    # Try JSON
    with contextlib.suppress(json.JSONDecodeError):
        return json.loads(text)    

    # Try HTML
    with contextlib.suppress(Exception):
        soup = BeautifulSoup(text, "html.parser")

        # Example logic: extract text blocks or divs
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
        return {"html_raw": text, "html_parsed": paragraphs}

    # Fallback: empty dict
    return {}
    

async def _make_api_request(
    url: str,
    engine: str,
    **kwargs: Any, 
   
) -> Dict[str, Any]:
    """Make an async HTTP POST request and always return a dict."""

    api_key = os.getenv("BRIGHTDATA_TOKEN")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # Exponential backoff schedule
    backoff_delays = [0.5, 1.0, 2.0]  # seconds
    
   
    if clients.client is None:
        raise RuntimeError("HTTP client not initialized")
    
    # Simple retry logic (3 attempts)
    for attempt in range(len(backoff_delays) + 1):
        try:
            log(f"Sending request to {engine} (Attempt {attempt + 1})")
            response = await clients.client.post(url, headers=headers, **kwargs)
            response.raise_for_status()

            text = response.text

            # Baidu may return HTML → attempt both
            if engine == "baidu":
                data = parse_response_text(text)
            else:
                # Normal engines return JSON
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    data = parse_response_text(text)

                # Validate using Pydantic
                try:
                    validated = ApiResponse(**data)
                    log("Response validated successfully.")
                    return validated.model_dump()
                except ValidationError as e:
                    log(f"Validation failed: {e}")
                    return {}

        except httpx.RequestError as e:
            log(f"Connection error: {e}")

        except httpx.HTTPStatusError as e:
            log(f"HTTP {e.response.status_code}: {e}")

        # If failed and retries left → wait
        if attempt < len(backoff_delays):
            delay = backoff_delays[attempt]
            log(f"Retrying in {delay}s...")
            time.sleep(delay)

    log("All retries failed.")

    # If all retries failed → safe fallback
    return {}

def parse_baidu_html(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for item in soup.select(".result"):  # Baidu SERPs usually use .result class
        title_tag = item.select_one("h3 a")
        snippet_tag = item.select_one(".c-abstract")
        if title_tag:
            results.append({
                "title": title_tag.get_text(strip=True),
                "url": title_tag.get("href"),
                "snippet": snippet_tag.get_text(strip=True) if snippet_tag else ""
            })
    return results

async def serp_search(query, engine="google"):
    if engine == "google":
        base_url = "https://www.google.com/search"
        query_param = "q"
    elif engine == "bing":
        base_url = "https://www.bing.com/search"
        query_param = "q"
    elif engine == "baidu":
        base_url = "https://www.baidu.com/s"
        query_param = "wd"
    else:
        raise ValueError(f"Unknown engine {engine}")

    url = "https://api.brightdata.com/request"
    
    if engine in ["google", "bing"]:
        url_with_query = f"{base_url}?{query_param}={quote_plus(query)}&brd_json=1"    
    elif engine == "baidu":
        url_with_query = f"{base_url}?{query_param}={quote_plus(query)}"

    payload = {"zone": "ai_agent", "url": url_with_query, "format": "raw"}
    full_response = await _make_api_request(url, engine, json=payload)
    
    if not full_response:
        return None

    # Special case for Baidu → parse HTML
    if engine == "baidu":
        results = parse_baidu_html(full_response)
        return {"organic": results, "knowledge": {}}
    
    return {
        "knowledge": full_response.get("knowledge", {}), 
        "organic": full_response.get("organic", []), 
    }


async def _trigger_and_download_snapshot(trigger_url, params, data, operation_name="operation"):
    trigger_result = await _make_api_request(trigger_url, engine="", params=params, json=data)
    if not trigger_result:
        return None

    snapshot_id = trigger_result.get("snapshot_id")  # type: ignore[arg-type]
    if not snapshot_id:
        return None

    if not poll_snapshot_status(snapshot_id):
        return None

    return download_snapshot(snapshot_id)


async def reddit_search_api(keyword, date="All time", sort_by="Hot", num_of_posts=15):
    
    #trigger_url = f"https://api.brightdata.com/datasets/request_collection?dataset_id={dataset_id}&type=discover_new"

    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"

    params = {
        "dataset_id": dataset_id,
        "include_errors": "true",
        "type": "discover_new",
        "discover_by": "keyword"
    }

    data = [
        {
            "keyword": keyword,
            "date": date,
            "sort_by": sort_by,
            "num_of_posts": num_of_posts,
        }
    ]

    raw_data = await _trigger_and_download_snapshot(
        trigger_url, params, data, operation_name="reddit"
    )

    if not raw_data:
        return None

    parsed_data = []
    #if parsed_data:
    for post in raw_data:
        parsed_post = {
            "title": post.get("title"),
            "url": post.get("url")
        }
        parsed_data.append(parsed_post)

    return {"parsed_posts": parsed_data, "total_found": len(parsed_data)}

import requests

def get_dataset_id(api_token: str, dataset_name: str) -> str | None:
    # sourcery skip: inline-variable, move-assign-in-block, use-named-expression
    """
    Get Bright Data dataset ID (gd_xxx) by dataset name.

    :param api_token: Your Bright Data API token
    :param dataset_name: Name of the dataset you created
    :return: Dataset ID (gd_xxx...) if found, otherwise None
    """
    
    url = "https://api.brightdata.com/datasets"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        datasets = response.json().get("datasets", [])

        return next(
            (
                ds.get("id")
                for ds in datasets
                if ds.get("name") == dataset_name
            ),
            None,
        )
    except requests.exceptions.RequestException as e:
        print(f"Error fetching datasets: {e}")
        return None

    """
    # Example usage
    API_TOKEN = "your_real_api_token_here"
    dataset_name = "My Lotto Dataset"  # whatever you named it in Bright Data

    dataset_id = get_dataset_id(API_TOKEN, dataset_name)
    if dataset_id:
        print(f"Dataset ID for '{dataset_name}': {dataset_id}")
    else:
        print(f"Dataset '{dataset_name}' not found.")
    """


async def reddit_post_retrieval(urls, days_back=10, load_all_replies=False, comment_limit=""):
    if not urls:
        return None

    #trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
    
    dataset_id = "gd_lvzdpsdlw09j6t702"
    trigger_url = f"https://api.brightdata.com/datasets/request_collection?dataset_id={dataset_id}&type=discover_new"

    API_KEY = os.getenv("BRIGHTDATA_TOKEN")
    dataset_name = "Reddit"  # whatever you named it in Bright Data

    if not API_KEY:
        return None
    
    if dataset_id2 := get_dataset_id(API_KEY, dataset_name):
        print(f"Dataset ID for '{dataset_name}': {dataset_id2}")
    else:
        print(f"Dataset '{dataset_name}' not found.")
    params = {
        #"dataset_id": "gd_lvzdpsdlw09j6t702",
        "include_errors": "true"
    }

    data = [
        {
            "url": url,
            "days_back": days_back,
            "load_all_replies": load_all_replies,
            "comment_limit": comment_limit
        }
        for url in urls
    ]

    raw_data = await _trigger_and_download_snapshot(
        trigger_url, params, data, operation_name="reddit comments"
    )
    if not raw_data:
        return None

    parsed_comments = []
    for comment in raw_data:
        parsed_comment = {
            "comment_id": comment.get("comment_id"),
            "content": comment.get("comment"),
            "date": comment.get("date_posted"),
        }
        parsed_comments.append(parsed_comment)

    return {"comments": parsed_comments, "total_retrieved": len(parsed_comments)}

