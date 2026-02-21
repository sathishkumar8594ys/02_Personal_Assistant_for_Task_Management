# AI Task Orchestrator (Personal Assistant)

## Overview
This project is an AI-powered conversational CLI orchestrator built for Professionals, Software Engineers, and Android Platform Developers. Unlike generic "to-do list" applications, this AI autonomously interprets unstructured engineering brain-dumps (e.g., "I hit a blocker on Jira AND-1234, also remind me to check the Bluetooth HAL") and systematically structures them into a permanent database.

It uses a **ReAct (Reasoning + Acting)** loop to seamlessly connect the Groq/OpenAI Large Language Models to local Python execution.

---

## Technical Architecture

### 1. The Core ReAct Engine (`src/agent.py`)
The AI operates using a 5-iteration bounded reasoning loop.
1. **Intake**: The user provides a raw string prompt.
2. **Reasoning**: The LLM analyzes the prompt against its `system_prompt` rules.
3. **Acting (Tool Calls)**: The LLM outputs a JSON payload requesting to fire a specific function (e.g., `add_task` or `search_historical_tasks`).
4. **Execution**: The local Python backend safely intercepts this JSON, executes the SQL database command, and returns the raw data back to the LLM.
5. **Synthesis**: The LLM reads the database response and formats a human-readable conversational reply.

#### Hallucination Resistance & Recovery
A common failure point in ReAct agents is LLM hallucination (requesting tools that don't exist, or omitting required parameters). This project implements two advanced safeguards:
* **JSON Schema Enforcement**: All required parameters in `tools.py` naturally fallback to empty strings instead of throwing unhandled exceptions if the LLM emits `{}`.
* **Regex Fallback Recovery**: If the Groq API fails to natively parse the LLM's XML response into a tool call, `agent.py` catches the `failed_generation` exception, runs a Regex extractor to find `<function=...>`, and manually injects the execution back into the loop.

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

1. **Install Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Create a `.env` file in the root of the project with your LLM API key. The agent supports both Groq and OpenAI natively:
   ```env
   GROQ_API_KEY="gsk_..."
   AI_BASE_URL="https://api.groq.com/openai/v1"
   AI_MODEL="llama-3.3-70b-versatile"
   
   # Or for OpenAI:
   # OPENAI_API_KEY="sk-..."
   # AI_MODEL="gpt-4o"
   ```

3. **Run the Assistant**:
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
