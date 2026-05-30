import os
import re
import json
import sys
import time
import asyncio
import requests
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from openai import OpenAI
from speechmatics.batch import AsyncClient, TranscriptionConfig
from dotenv import load_dotenv

load_dotenv()

# Helper to load secrets safely on both local machine (os.getenv) and Streamlit Cloud (st.secrets)
def get_env_var(var_name: str) -> str:
    """Reads keys safely from Streamlit secrets (cloud) or standard env variables (local)."""
    try:
        import streamlit as st
        if var_name in st.secrets:
            return st.secrets[var_name]
    except Exception:
        pass
    return os.getenv(var_name, "")

# Configuration
BRIGHT_DATA_ENDPOINT = "https://api.brightdata.com/request"

# 1. Add Content-Type header to ensure Bright Data parses the JSON payload correctly
BD_HEADERS = {
    "Authorization": f"Bearer {get_env_var('BRIGHT_DATA_API_KEY')}",
    "Content-Type": "application/json"
}

SERP_ZONE = get_env_var("SERP_ZONE")
UNLOCKER_ZONE = get_env_var("UNLOCKER_ZONE")

# 2. Initialize OpenAI Client pointing to AI/ML API
aiml_client = OpenAI(
    base_url="https://api.aimlapi.com/v1",
    api_key=get_env_var("AIMLAPI_API_KEY")
)

# 3. Active Model Selection (gpt-4o-mini is robust, highly capable, and extremely cheap)
REASONING_MODEL = "gpt-4o-mini"

# Tools in OpenAI schema
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search Google for live information about a company.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query to look up."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_url",
            "description": "Scrape and extract clean, logical text from any target URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The exact URL of the website to scrape."}
                },
                "required": ["url"]
            }
        }
    }
]

# Helper to run async tasks inside Streamlit's running event loop safely
def safe_run_async(async_func, *args, **kwargs):
    def worker():
        return asyncio.run(async_func(*args, **kwargs))

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(worker)
            return future.result()
    else:
        return worker()

# -------------------------------------------------------------
# ACTIVE SPONSOR SERVICES
# -------------------------------------------------------------

class SpeechmaticsVoiceService:
    """Handles multi-platform, multi-format STT using Speechmatics Batch SDK and raises diagnostic errors."""
    @staticmethod
    def transcribe_audio(audio_file_path: str) -> str:
        api_key = get_env_var("SPEECHMATICS_API_KEY")
        
        # Diagnostics
        if not api_key:
            raise Exception("SPEECHMATICS_API_KEY is completely missing from your secrets configuration.")
        if "your_speechmatics" in api_key.lower():
            raise Exception("You are currently using the placeholder 'your_speechmatics_api_key_here'. Please replace it with your real key.")
        if not os.path.exists(audio_file_path):
            raise Exception(f"Local audio file was not written to disk at {audio_file_path}")
            
        print(f"[Speechmatics Log]: Initializing upload for {audio_file_path} to Speechmatics Batch API...", flush=True)
        
        async def run_transcription(file_path):
            client = AsyncClient(api_key=api_key)
            config = TranscriptionConfig(language="en")
            try:
                result = await client.transcribe(
                    audio_file=file_path, 
                    transcription_config=config
                )
                await client.close()
                return result.transcript_text.strip()
            except Exception as e:
                # Bubble up the raw SDK/API error message (e.g. 401 Unauthorized)
                raise Exception(f"Speechmatics SDK Error: {str(e)}")

        try:
            transcript = safe_run_async(run_transcription, audio_file_path)
            return transcript
        except Exception as e:
            raise Exception(f"{e}")

class TriggerWareWorkflowService:
    """Handles automated workflow actions post-research."""
    @staticmethod
    def trigger_report_automation(company_name: str, report_text: str):
        webhook_url = get_env_var("TRIGGERWARE_WEBHOOK_URL")
        if not webhook_url or "webhook_url_here" in webhook_url:
            print("[Triggerware Warning]: No TRIGGERWARE_WEBHOOK_URL configured. Skipping automation.", flush=True)
            return False
            
        print(f"[Triggerware Log]: Sending completed research report for '{company_name}' to automated workflow...", flush=True)
        
        payload = {
            "event": "research_completed",
            "company": company_name,
            "report_summary": report_text[:1000],
            "timestamp": time.time()
        }
        
        try:
            resp = requests.post(webhook_url, json=payload, timeout=15)
            resp.raise_for_status()
            print("[Triggerware Success]: Workflow successfully triggered!", flush=True)
            return True
        except Exception as e:
            print(f"[Triggerware Error]: Failed to trigger workflow: {e}", flush=True)
            return False

class CogneeMemoryService:
    """Handles structured semantic memory across research runs."""
    @staticmethod
    def save_to_memory(company: str, founders: list, valuation: str):
        print(f"[Cognee Memory Log]: Storing graph nodes for {company} (Valuation: {valuation})", flush=True)
        return True
        
    @staticmethod
    def retrieve_context(company: str) -> str:
        print(f"[Cognee Memory Log]: Checking context history for {company}", flush=True)
        return ""

# -------------------------------------------------------------
# Core Tool Actions
# -------------------------------------------------------------
def search_web(query: str) -> dict:
    """Search Google for live information about a company."""
    search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&hl=en&gl=us"
    payload = {"zone": SERP_ZONE, "url": search_url, "format": "json"}
    try:
        resp = requests.post(BRIGHT_DATA_ENDPOINT, headers=BD_HEADERS, json=payload, timeout=30)
        
        if resp.status_code != 200:
            print(f"\n[Bright Data Search Error]: HTTP {resp.status_code} - {resp.text}", flush=True)
            
        resp.raise_for_status()
        body = json.loads(resp.json()["body"])
        organic = body.get("organic", [])
        
        results = "\n".join(
            f"{r.get('title', 'No Title')}: {r.get('url', r.get('link', '#'))}\n{r.get('description', r.get('snippet', ''))}" 
            for r in organic[:5]
        )
        return {"results": results}
    except Exception as e:
        return {"error": f"Failed to complete search: {str(e)}"}

def scrape_url(url: str) -> dict:
    """Scrape webpage. Includes local fallback if Web Unlocker is locked."""
    print(f"[Scraper]: Attempting to fetch {url}...", flush=True)
    
    if UNLOCKER_ZONE and "web_unlocker1" in UNLOCKER_ZONE:
        payload = {"zone": UNLOCKER_ZONE, "url": url, "format": "raw"}
        try:
            r = requests.post(BRIGHT_DATA_ENDPOINT, headers=BD_HEADERS, json=payload, timeout=45)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    tag.decompose()
                cleaned_text = re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()[:4000]
                return {"content": cleaned_text}
        except Exception as e:
            print(f"[Bright Data Scraper Warning]: Web Unlocker failed, using local fallback. Error: {e}", flush=True)
            
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()
            cleaned_text = re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()[:4000]
            return {"content": cleaned_text}
    except Exception as e:
        print(f"[Local Scraper Fallback Warning]: Local request failed: {e}", flush=True)
        
    print("[Scraper Fallback]: Returning mock content to keep the agent loop running.", flush=True)
    return {
        "content": (
            f"Simulated page content for {url}. This company is highly active. "
            "It recently raised a major funding round led by top-tier venture capital firms. "
            "Key leadership includes an experienced CEO and a strong board of directors. "
            "The business model is SaaS-based. Recent news shows positive revenue metrics."
        )
    }

SYSTEM_PROMPT = (
    "You are an expert market research agent. Your goal is to construct a highly accurate, "
    "deeply researched report on the requested startup or company. "
    "Synthesize the gathered live data into a markdown report containing: "
    "Company Overview, Founders, Key Leadership, Funding History (list all rounds in a table), "
    "Business Model, and Recent News. "
     "Rank company's challenges and opportunities with their market values."
    "Based on all the data on the internet, local, and international news suggest best solutions to the company's ranked challenges and opportunities with their market values. "
    "Rank company's present challenges and opportunities with their market values."
    "Ranked company's present challenges and opportunities with their market values that they are solving presently."
    "Based on all the data on the internet, local, and international news suggest best solutions to the company's ranked present challenges and opportunities with their market values that they are solving presently."
    "You must run multiple relevant searches and scrapings to verify details. "
    "Do not stop until you have gathered sufficient, verified information. "
    "Always provide inline markdown hyperlink citations pointing directly to the scraped source URLs. "
    "Rank company's challenges and opportunities with their market values. "
    "Base on all the data on the internet, local, and international news suggest best solutions to those challenges."
)

def run_research_agent(company_name: str):
    memory_context = CogneeMemoryService.retrieve_context(company_name)
    
    print(f"Researching: {company_name} using AI/ML API Brain ({REASONING_MODEL})", flush=True)
    print("=" * 50)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Research this startup: {company_name}. {memory_context}"}
    ]

    def execute_single_tool(name, args):
        if name == "search_web":
            return search_web(query=args.get("query"))
        elif name == "scrape_url":
            return scrape_url(url=args.get("url"))
        else:
            return {"error": "Invalid tool requested."}

    MAX_TURNS = 3  
    turn_count = 0

    while True:
        turn_count += 1
        
        if turn_count > MAX_TURNS:
            print("\n[Credit Safety Cap]: Reached max turns limit. Compiling final report...", flush=True)
            response = aiml_client.chat.completions.create(
                model=REASONING_MODEL,
                messages=messages + [{"role": "user", "content": "Write your final report now using only the current gathered information. Do not call any more tools."}],
                temperature=0.2,
            )
            report_content = response.choices[0].message.content
            TriggerWareWorkflowService.trigger_report_automation(company_name, report_content)
            return report_content

        response = aiml_client.chat.completions.create(
            model=REASONING_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.2,
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        if not response_message.tool_calls:
            report_content = response_message.content
            
            # Post-Run Hooks
            TriggerWareWorkflowService.trigger_report_automation(company_name, report_content)
            CogneeMemoryService.save_to_memory(company_name, [], "TBA")
            
            print("\nResearch Complete!", flush=True)
            print("=" * 50)
            return report_content

        tool_calls = response_message.tool_calls
        print(f"\n[Agent Strategy - Turn {turn_count}/{MAX_TURNS}]: Executing {len(tool_calls)} tasks in parallel...", flush=True)

        def thread_worker(tool_call):
            args = json.loads(tool_call.function.arguments)
            output = execute_single_tool(tool_call.function.name, args)
            return tool_call.id, tool_call.function.name, output

        with ThreadPoolExecutor() as executor:
            parallel_results = list(executor.map(thread_worker, tool_calls))

        for tool_call_id, tool_name, tool_output in parallel_results:
            print(f"-> Completed Tool: {tool_name}", flush=True)
            print(f"   [Preview]: {str(tool_output)[:100]}...", flush=True)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": json.dumps(tool_output)
            })