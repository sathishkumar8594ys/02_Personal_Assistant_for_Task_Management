# Personal Task Manager AI Agent

## Overview
This project is an AI-powered CLI Personal Assistant tailored specifically for an Android Platform Engineer. It utilizes the ReAct pattern to process unstructured natural language into structured, persistently stored tasks.

It categorizes work streams seamlessly—distinguishing between Jira tickets, emails, unplanned engineering work, and personal matters—all stored outside the project folder (`~/.task_manager_ai/tasks.db`) to ensure long-term retention across years.

## Features
- **Intelligent Task Extraction**: Tell the bot "I got a Jira AND-1234 to fix Bluetooth" and it automatically parses the category, priority, and source ID.
- **Year-Long Persistence**: Tasks are saved in an SQLite database in your home directory, guaranteeing they won't be lost if you delete the project folder.
- **Strategic Prioritization**: Ask "What should I do today?" and the AI will query the DB, weighing corporate high-priority Jira targets against personal tasks, and give you a structured path forward.
- **Historical Search**: Prepare for performance reviews by asking "What did I work on related to the framework last month?" The agent can retrieve all historical data.

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Create a `.env` file in the root of the project with your LLM API key:
   ```env
   GROQ_API_KEY=your_groq_key_here
   # OR
   # OPENAI_API_KEY=your_openai_key_here
   ```

3. **Run the Assistant**:
   ```bash
   python src/main.py
   ```
   *Note: Running `main.py` will automatically initialize the SQLite DB at `~/.task_manager_ai/tasks.db` if it doesn't already exist.*

## Example Usage
- `Remind me to review the PR for AND-9876 tomorrow, it's critical.`
- `What does my workload look like right now?`
- `Mark task ID 2 as completed.`
- `What tasks did I complete last week regarding the battery optimization bug?`
