# Autonomous Gemini 3.5 Market Research Agent
[![Lablab.ai Hackathon](https://img.shields.io/badge/Built%20for-Lablab.ai%20Hackathon-blueviolet?style=flat-square)](https://lablab.ai)

An autonomous market research agent powered by Gemini 3.5 Flash and the `google-genai` SDK. It implements a ReAct (Reason + Act) loop utilizing Bright Data's SERP and Web Unlocker APIs to autonomously search, scrape, and synthesize live web data into clean, structured Markdown reports.

Instead of relying on static training data or manual browsing, this agent dynamically gathers real-time information—including company overviews, founding members, funding history, and current news—directly from live web sources.

---

## Architecture Overview
+-----------------------------------+
              |        Gemini 3.5 Flash           |
              |  (Decision Maker / Orchestrator)  |
              +-----------------+---------+-------+
                                |         ^
            Requests Tool Calls |         | Tool Results
                                v         |
              +-----------------+---------+-------+
              |          Python Runtime           |
              |     (google-genai Client Loop)    |
              +--------+-----------------+--------+
                       |                 |
         `search_web`  |                 |  `scrape_url`
                       v                 v
              +--------+----+   +--------+--------+
              | Bright Data |   |   Bright Data   |
              |  SERP API   |   |  Web Unlocker   |
              +-------------+   +-----------------+

              - **Core Orchestrator**: Gemini 3.5 Flash evaluates the user's research query, determines what information is missing, and requests parallel searches or webpage scraping.
- **Auto-Inferred Tool Schemas**: The project uses the modern `google-genai` SDK, which automatically extracts JSON schemas for model tool-use from native Python function signatures, type hints, and docstrings.
- **Robust Web Retrieval**:
  - **SERP API** returns structured search results directly from Google without complex browser configurations.
  - **Web Unlocker** automatically bypasses CAPTCHAs, manages proxy rotation, and handles dynamic client-side rendering to fetch clean page text.

---

## Prerequisites

Before setting up, make sure you have:
- Python 3.10 or higher installed.
- A **Google AI Studio** API Key ([Get an API Key](https://aistudio.google.com/)).
- A **Bright Data** account (a free trial is available).

---

## Setup & Installation

### 1. Configure Bright Data Zones
Log into your Bright Data dashboard and set up two zones:
1. **SERP API Zone**: Create a new API zone, select **SERP API**, assign a name (e.g., `serp_api2`), and set the default response format to **Full JSON**.
2. **Web Unlocker Zone**: Create another API zone, select **Web Unlocker API**, and assign a name (e.g., `web_unlocker1`). 

*Note: Your API key on the Bright Data dashboard home page applies to both zones.*

### 2. Clone the Repository
Clone the project and navigate to the root directory:
```bash
git clone https://github.com/your-username/gemini-brightdata-research-agent.git
cd gemini-brightdata-research-agent

3. Create a Virtual Environment

python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt


4. Configure Environment Variables
Create a .env file in the root of the project:

GEMINI_API_KEY=your_google_ai_studio_api_key
BRIGHT_DATA_API_KEY=your_bright_data_api_key
SERP_ZONE=serp_api2
UNLOCKER_ZONE=web_unlocker1

Code Base Structure
    agent.py: Contains the tool definitions (search_web, scrape_url) and the core manual execution loop utilizing the google-genai SDK.

    .env: Holds your credentials and configuration zones (git-ignored).

    requirements.txt: Manages package dependencies.


Usage
You can run the agent directly from the command line by passing the name of the company or startup you want to research:


Bash
python agent.py "Mistral AI"
What happens behind the scenes:

    The agent initializes a multi-turn conversation with Gemini 3.5 Flash.

    The model decides to run parallel searches (e.g., targeting founding details, leadership, or recent funding).

    The Python script executes these requests concurrently through Bright Data's APIs and returns the results to the model context.

    The model identifies high-value URLs (such as news reports or company directories) and calls scrape_url.

    Once the data is consolidated, the agent saves a formatted .md report to your directory (e.g., mistral_ai_report.md).


    Technical Considerations
    Parallelism: Gemini 3.5 Flash native parallel tool execution is supported. The agent can request multiple search or scraping tasks in a single turn.

Context Management: Conversation turns are correctly tagged using types.Part.from_function_response and paired with individual query IDs (id=fc.id) to maintain reliable conversational state.

Robust Scrapes: Raw HTML is stripped of inline CSS style and JavaScript blocks inside the script, reducing tokens sent to the model while preserving document readability.


License

---
*Built as part of the Web Data UNLOCKED Hackathon on [Lablab.ai](https://lablab.ai).*