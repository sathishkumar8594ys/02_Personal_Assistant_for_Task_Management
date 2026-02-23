# AI Task Orchestrator (Personal Assistant)

## Overview
This project is an AI-powered conversational CLI orchestrator built for Professionals, Software Engineers, and Android Platform Developers. Unlike generic "to-do list" applications, this AI autonomously interprets unstructured engineering brain-dumps (e.g., "I hit a blocker on Jira AND-1234, also remind me to check the Bluetooth HAL") and systematically structures them into a permanent database.

It uses a **ReAct (Reasoning + Acting)** loop to seamlessly connect **local Large Language Models** (via Ollama) to local Python execution. 100% private, no API keys needed.

---

## Technical Architecture

### 1. The Core ReAct Engine (`src/agent.py`)
The AI operates using a 5-iteration bounded reasoning loop.
1. **Intake**: The user provides a raw string prompt.
2. **Reasoning**: The LLM analyzes the prompt against its `system_prompt` rules.
3. **Acting (Tool Calls)**: The LLM outputs a JSON payload requesting to fire a specific function (e.g., `add_task` or `search_historical_tasks`).
4. **Execution**: The local Python backend safely intercepts this JSON, executes the SQL database command, and returns the raw data back to the LLM.
5. **Synthesis**: The LLM reads the database response and formats a human-readable conversational reply.

#### Robust Tool Execution
The agent uses the native `ollama` Python client to directly parse JSON tool-call schema requirements. To prevent infinite loops caused by LLM tool recursion (where the model repeatedly requests the same data), `agent.py` actively intercepts tool responses and forces the LLM to summarize the data directly for the user.

### 2. The Database Layer (`src/db.py`)
Data is stored permanently outside of the project repository at `~/.task_manager_ai/tasks.db`. This ensures that even if the developer clones the repo, updates the logic, or deletes the development folder, their personal tasks remain safe.

**Schema Definition:**
* `id` (INTEGER PRIMARY KEY)
* `description` (TEXT)
* `category` (TEXT) - Enforced via LLM logic: `Work`, `Communication`, `Unplanned_Work`, `Personal`, `Meeting`
* `status` (TEXT) - `pending`, `in_progress`, `completed`, `blocked`
* `priority` (TEXT) - `Critical`, `High`, `Medium`, `Low`
* `source_id` (TEXT) - E.g., `AND-5555`
* `created_at` (TIMESTAMP)
* `due_date` (DATE)
* `completed_at` (TIMESTAMP)

### 3. The Toolset (`src/tools.py`)
The LLM is granted access to the following deterministic SQL wrappers:
* `add_task`: Ingests descriptions, priority, categories, and due dates.
* `list_tasks`: Retrieves active or pending tasks.
* `update_task`: Dynamically modifies specific cells using a concatenated SQL `UPDATE` string, supporting simultaneous changes to `status`, `due_date`, `description`, etc.
* `search_historical_tasks`: Looks backward up to 365 days. Useful for generating end-of-year Performance Review summaries.
* `delete_task`: Hard-wipes a row. Shielded by a strict `system_prompt` rule requiring user conversational confirmation.

---

## Setup Instructions

1. **Prerequisite**: Install [Ollama](https://ollama.com/) on your local machine and pull the required model (e.g., `llama3.1:8b`).
   ```bash
   ollama pull llama3.1:8b-instruct-q4_K_M
   ```

2. **Install Python Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   Create a `.env` file in the root of the project to override the default local model if you choose to use a different one. 
   ```env
   # Optional: Override the default Ollama model ID
   LLAMA3_1_8B_LOCAL_MODEL="llama3.1:8b-instruct-q4_K_M"
   ```

4. **Run the Assistant**:
   ```bash
   python src/main.py
   ```
   *Note: Running `main.py` will automatically initialize the SQLite DB at `~/.task_manager_ai/tasks.db` if it doesn't already exist.*

---

## Example Usage
- **Unstructured Intake**: `Remind me to review the PR for AND-9876 tomorrow, it's critical.`
- **Strategic Briefings**: `What does my workload look like right now?`
- **Updates**: `Bump the due date for task 6 to next monday.`
- **Historical Analysis**: `What tasks did I complete last week regarding the battery optimization bug?`
