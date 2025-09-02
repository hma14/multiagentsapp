import requests
import os
from openai import OpenAI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv, find_dotenv

dotenv_path = find_dotenv(usecwd=True)
#print("Dotenv found at:", dotenv_path)

load_dotenv(dotenv_path=dotenv_path, override=True)  # Load environment variables from .env file
#print("API KEY:", os.getenv("OPENAI_API_KEY"))

id = "gd_m5mbdl081229ln6t4a"

OpenAI_api_key = os.getenv("OPENAI_API_KEY")
BRIGHTDATA_TOKEN = os.getenv("BRIGHTDATA_TOKEN")
BRIGHTDATA_BASE = "https://api.brightdata.com/datasets"
client = OpenAI(api_key=OpenAI_api_key)

def get_dataset_id(dataset_name: str) -> str | None:
    # sourcery skip: inline-variable, move-assign-in-block, use-named-expression
    """
    Get Bright Data dataset ID (gd_xxx) by dataset name.

    :param api_token: Your Bright Data API token
    :param dataset_name: Name of the dataset you created
    :return: Dataset ID (gd_xxx...) if found, otherwise None
    """
    url = BRIGHTDATA_BASE + "/list"
    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_TOKEN}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        datasets = response.json()

        return next(
            (
                ds.get("id")
                for ds in datasets
                if dataset_name in ds.get("name")
            ),
            None,
        )
    except requests.exceptions.RequestException as e:
        print(f"Error fetching datasets: {e}")
        return None


def get_brightdata_datasets():
    
    dataset_name = "Booking"  # whatever you named it in Bright Data

    if dataset_id := get_dataset_id(dataset_name):
        print(f"Dataset ID for '{dataset_name}': {dataset_id}")
    else:
        print(f"Dataset '{dataset_name}' not found.")
        
    headers = {"Authorization": f"Bearer {BRIGHTDATA_TOKEN}", "Accept": "application/json"}
    try:      
        resp = requests.get(f"{BRIGHTDATA_BASE}/{dataset_id}/snapshots", headers=headers, timeout=30)
        print("Status:", resp.status_code)
        print(resp.text)
        return resp.json()
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

def run_agents(prompt: str) -> str:
    try:
        datasets = get_brightdata_datasets()

        if datasets.status_code == 500:
            return JSONResponse(content={"error": datasets.body}, status_code=500)
        # Ask GPT to analyze dataset names/descriptions against prompt
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI data analyst."},
                {"role": "user", "content": f"Prompt: {prompt}\nDatasets: {datasets}"}
            ]
        )

        return response.choices[0].message.content
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)