import os
import re
import json
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from google.genai.errors import ServerError
from dotenv import load_dotenv

load_dotenv()

# Configuration
BRIGHT_DATA_ENDPOINT = "https://api.brightdata.com/request"
BD_HEADERS = {"Authorization": f"Bearer {os.getenv('BRIGHT_DATA_API_KEY')}"}
SERP_ZONE = os.getenv("SERP_ZONE")
UNLOCKER_ZONE = os.getenv("UNLOCKER_ZONE")

def search_web(query: str) -> dict:
    """
    Search Google for live information about a company. 
    Use this to find overview data, founders, funding rounds, business model details, and news.

    Args:
        query: The search query to look up on Google.
    """
    search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&hl=en&gl=us"
    payload = {"zone": SERP_ZONE, "url": search_url, "format": "json"}
    try:
        resp = requests.post(BRIGHT_DATA_ENDPOINT, headers=BD_HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
        body = json.loads(resp.json()["body"])
        organic = body.get("organic", [])
        results = "\n".join(
            f"{r['title']}: {r['url']}\n{r.get('description','')}" 
            for r in organic[:5]
        )
        return {"results": results}
    except Exception as e:
        return {"error": f"Failed to complete search: {str(e)}"}

def scrape_url(url: str) -> dict:
    """
    Scrape and extract clean, logical text from any target URL. 
    Use this to fetch the full details of a specific webpage.

    Args:
        url: The exact URL of the website to scrape.
    """
    payload = {"zone": UNLOCKER_ZONE, "url": url, "format": "raw"}
    try:
        r = requests.post(BRIGHT_DATA_ENDPOINT, headers=BD_HEADERS, json=payload, timeout=45)
        r.raise_for_status()
        
        # Parse HTML cleanly with BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Drop navigation elements, scripts, styles, and footers
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
            
        # Extract structured text separated by single spaces
        text = soup.get_text(separator=" ")
        cleaned_text = re.sub(r"\s+", " ", text).strip()[:4000]
        return {"content": cleaned_text}
    except Exception as e:
        return {"error": f"Failed to scrape URL: {str(e)}"}

client = genai.Client()

SYSTEM_PROMPT = (
    "You are an expert market research agent. Your goal is to construct a highly accurate, "
    "deeply researched report on the requested startup or company. "
    "Synthesize the gathered live data into a markdown report containing: "
    "Company Overview, Founders, Key Leadership, Funding History (list all rounds in a table), "
    "Business Model, and Recent News. "
    "Company or startup challenges and opportunities."
    "Rank the challenges and opportunies base on their market values."
    "Company or startup present challenges and opportunities that they are trying to solve."
    "Rank the present challenges that they are trying to solve base on their market values"
    "Suggest solution to the challenges and opportunities to the best of your ability base on the information on the internet and news."
    "Suggest solution to the present challenges and opportunities to the best of your ability base on the information on the internet and news."
    "You must run multiple relevant searches and scrapings to verify details. "
    "Do not stop until you have gathered sufficient, verified information. "
    "Always provide inline markdown hyperlink citations pointing directly to the scraped source URLs "
    "to verify your claims."
)

MODELS_FALLBACK = ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-1.5-flash"]

def generate_content_with_retry(client, contents, config, max_retries=5):
    """
    Calls Gemini API and handles transient 503/server errors using exponential backoff.
    """
    current_model_idx = 0
    delay = 2
    
    for attempt in range(max_retries):
        model_name = MODELS_FALLBACK[current_model_idx]
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            return response
        except ServerError as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print(f"\n[Gemini API Warning]: Server overloaded ({model_name} returned 503).")
                if attempt >= 1 and current_model_idx < len(MODELS_FALLBACK) - 1:
                    current_model_idx += 1
                    print(f"-> Switching fallback path to: {MODELS_FALLBACK[current_model_idx]}")
                print(f"-> Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                delay *= 2
            else:
                raise e
                
    raise Exception("Unable to contact Gemini API due to ongoing Google server overload (503). Please try again shortly.")

def run_research_agent(company_name: str):
    print(f"Researching: {company_name}")
    print("=" * 50)

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"Research this startup: {company_name}")]
        )
    ]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[search_web, scrape_url],
        temperature=0.2,
    )

    # Parallel tool runner helper
    def execute_single_tool(fc):
        if fc.name == "search_web":
            return fc.id, fc.name, search_web(query=fc.args.get("query"))
        elif fc.name == "scrape_url":
            return fc.id, fc.name, scrape_url(url=fc.args.get("url"))
        else:
            return fc.id, fc.name, {"error": "Invalid tool requested."}

    while True:
        response = generate_content_with_retry(client, contents, config)

        if not response.function_calls:
            print("\nResearch Complete!")
            print("=" * 50)
            return response.text

        contents.append(response.candidates[0].content)

        # Run multiple tool execution requests concurrently using a ThreadPoolExecutor
        print(f"\n[Agent Strategy]: Executing {len(response.function_calls)} tasks in parallel...")
        with ThreadPoolExecutor() as executor:
            parallel_results = list(executor.map(execute_single_tool, response.function_calls))

        tool_results_parts = []
        for fc_id, fc_name, tool_output in parallel_results:
            print(f"-> Completed Tool: {fc_name}")
            print(f"   [Preview]: {str(tool_output)[:100]}...")
            
            tool_results_parts.append(
                types.Part.from_function_response(
                    name=fc_name,
                    response=tool_output,
                    id=fc_id
                )
            )

        contents.append(
            types.Content(
                role="tool",
                parts=tool_results_parts
            )
        )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py <company_name>")
        sys.exit(1)
        
    target_company = sys.argv[1]
    report = run_research_agent(target_company)
    
    output_filename = f"{target_company.lower().replace(' ', '_')}_report.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"\nMarkdown report generated and saved to {output_filename}")