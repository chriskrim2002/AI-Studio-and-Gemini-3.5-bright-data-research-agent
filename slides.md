---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #0f172a
color: #f8fafc
style: |
  section {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    padding: 40px;
  }
  h1 {
    color: #38bdf8;
  }
  h2 {
    color: #38bdf8;
    border-bottom: 2px solid #334155;
  }
  footer {
    font-size: 0.5em;
    color: #64748b;
  }
  code {
    background-color: #1e293b;
    color: #38bdf8;
  }
---

# Gemini 3.5 Autonomous Research Agent
### Real-Time Market Intelligence on Demand

**Track:** Finance & Market Intelligence
**Built by:** @chriskrim2002
**Stack:** Gemini 3.5 Flash, Bright Data, Streamlit

---

## The Problem: The Static Data Gap

*   **Knowledge Cutoffs:** Traditional LLMs lack real-time access, rendering them ineffective for tracking active startups, recent funding, or breaking news.
*   **Manual Overhead:** Compiling comprehensive corporate dossiers manually takes hours of human search, navigation, and synthesis.
*   **Anti-Bot Scraping Blocks:** Standard web-scraping scripts fail immediately due to CAPTCHAs, IP bans, and complex JavaScript rendering.

---

## The Solution: Real-Time Autonomous ReAct Loop

*   **Gemini 3.5 Flash Orchestrator:** Drives a dynamic ReAct (Reason + Act) loop, autonomously deciding when to search and which pages to scrape.
*   **Bright Data SERP API:** Programmatically executes Google searches to retrieve clean organic results without browser automation [3].
*   **Bright Data Web Unlocker:** Bypasses anti-bot walls and rotates proxies automatically to retrieve raw HTML.
*   **BeautifulSoup Parsing:** Extracts clean text layout dynamically, preserving tabular data and dropping code bloat [1].

---

## Performance & UX Optimization

*   **Parallel Execution:** Orchestrates a `ThreadPoolExecutor` to process multiple search and scrape tasks concurrently, cutting total latency by up to 60% [1].
*   **Resiliency Layer:** Employs exponential backoff to handle transient 503 capacity limits by automatically transitioning to fallback paths.
*   **Streamlined Streamlit UI:** Features a direct, responsive web interface allowing judges to input queries and instantly download generated Markdown reports [1].

---

## Business Impact & Use Cases

*   **Finance & Market Intelligence:** Automates extraction of startup valuations, funding rounds, key leadership transitions, and business models.
*   **GTM (Go-To-Market) Intelligence:** Empowers sales teams with real-time prospect profiling and market positioning dossiers before meetings.
*   **Extensible Architecture:** Designed as a clean, modular template that can easily scale to incorporate custom private APIs, CRM hooks, or vector storage.