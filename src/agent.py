import os
import json
import re
import ollama
from tools import add_task, list_tasks, search_historical_tasks, update_task, delete_task
from rich.console import Console
import logging

logging.basicConfig(filename='agent_debug.log', level=logging.INFO, format='%(asctime)s - %(message)s')

console = Console()

class TaskAgent:
    def __init__(self):
        # Using Llama 3.1 local model via Ollama
        self.model = os.environ.get("LLAMA3_1_8B_LOCAL_MODEL", "llama3.1:8b-instruct-q4_K_M")
        
        self.system_prompt = """
ROLE:
You are TaskMaster AI, an elite Personal Assistant tailored for Software Engineers, Professionals, and Android Platform Developers.

OBJECTIVE:
1. Convert unstructured user thoughts into structured task entries.
2. Classify each task into ONE category:
   - Work (e.g., Jira tickets, GitHub PRs, coding features)
   - Communication (e.g., Emails, Slack, teams messages)
   - Unplanned_Work (e.g., sudden production bugs, hotfixes)
   - Personal
   - Meeting
3. Assign ONE priority:
   - Critical
   - High
   - Medium
   - Low
4. Provide strategic daily planning using real database data.

DATABASE ACCESS:
You have full access to the task database via tools.
You MUST use tools before answering questions about tasks.

STRICT TOOL RULES:

A. When user asks:
   - "all tasks"
   - "my tasks"
   - "remaining tasks"
   → CALL list_tasks with status="all"

B. When user asks:
   - "what should I do today?"
   - "priorities"
   - "daily plan"
   → FIRST call list_tasks with status="pending"
   → THEN generate a strategic plan using ONLY returned data.

C. After a tool returns:
   → Immediately answer the user.
   → DO NOT call the same tool again.
   → DO NOT fabricate missing data.

D. If tool returns empty:
   → Say clearly: "There are no tasks."

E. If tool returns an error:
   → Inform the user that the tool failed.
   → Do NOT pretend success.

F. If user wants to DELETE a task:
   → Ask: "Are you sure you want to delete task <task_name>?"
   → WAIT for explicit confirmation.
   → Only after confirmation, call delete_task.

ANTI-HALLUCINATION RULES:

1. Never guess task data.
2. Never invent database results.
3. Only use tool output as source of truth.
4. If unsure, ask for clarification.
5. Do NOT assume implicit deletions or updates.

RESPONSE STYLE:

- Be concise.
- Be structured.
- Be strategic (corporate work > critical bugs > meetings > personal).
- Always prioritize production issues and blockers.

OUTPUT FORMAT FOR NEW TASK CREATION:

{
  "title": "...",
  "category": "...",
  "priority": "...",
  "notes": "..."
}
"""
        self.messages = [{"role": "system", "content": self.system_prompt}]
        
        # Define the tools JSON schema for the LLM
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_task",
                    "description": "Adds a new task to the permanent database.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string", "description": "The description of the task"},
                            "category": {"type": "string", "enum": ["Work", "Communication", "Unplanned_Work", "Personal", "Meeting"]},
                            "priority": {"type": "string", "enum": ["Critical", "High", "Medium", "Low"]},
                            "source_id": {"type": "string", "description": "Optional Jira ticket ID, GitHub PR, or Email ID like 'AND-1234'"},
                            "due_date": {"type": "string", "description": "Optional due date in 'YYYY-MM-DD' format"}
                        },
                        "required": ["description", "category"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tasks",
                    "description": "Lists current tasks based on status and optionally category.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "blocked", "all"], "default": "all"},
                            "category": {"type": "string", "enum": ["Work", "Communication", "Unplanned_Work", "Personal", "Meeting"]}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_historical_tasks",
                    "description": "Searches for completed or old tasks over the past year. Crucial for performance reviews and reporting past work.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Keywords to search for in task descriptions."},
                            "days_back": {"type": "integer", "description": "Number of days back to search. Default is 365."}
                        },
                        "required": ["query"]
                    }
                }
            },
             {
                "type": "function",
                "function": {
                    "name": "update_task",
                    "description": "Updates an existing task's properties. Provide only the fields you want to update.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "integer", "description": "The ID of the task to update."},
                            "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "blocked"]},
                            "description": {"type": "string", "description": "New description"},
                            "due_date": {"type": "string", "description": "New due date in 'YYYY-MM-DD' format"},
                            "priority": {"type": "string", "enum": ["Critical", "High", "Medium", "Low"]}
                        },
                        "required": ["task_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_task",
                    "description": "Permanently deletes a task from the database. You MUST ask the user for confirmation before calling this tool.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "integer", "description": "The integer ID of the task to delete."}
                        },
                        "required": ["task_id"]
                    }
                }
            }
        ]
        
        self.available_functions = {
            "add_task": add_task,
            "list_tasks": list_tasks,
            "search_historical_tasks": search_historical_tasks,
            "update_task": update_task,
            "delete_task": delete_task
        }

    def chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})
        console.print("[dim]Agent is thinking...[/dim]")
        
        max_iterations = 5
        iterations = 0
        
        while iterations < max_iterations:
            iterations += 1
            try:
                # If the last message was a tool/user result, DO NOT provide tools again so the LLM is forced to respond to the user.
                if self.messages and self.messages[-1]["role"] == "user" and "returned:" in self.messages[-1]["content"]:
                    response = ollama.chat(
                        model=self.model,
                        messages=self.messages
                    )
                else:
                    response = ollama.chat(
                        model=self.model,
                        messages=self.messages,
                        tools=self.tools,
                    )
            except Exception as e:
                raise e
            
            response_message = response.message
            
            message_dict = {
                "role": response_message.role,
                "content": response_message.content or "",
            }
            
            if response_message.tool_calls:
                message_dict["tool_calls"] = [
                    {
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in response_message.tool_calls
                ]
            
            self.messages.append(message_dict)
            
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = self.available_functions[function_name]
                    function_args = tool_call.function.arguments
                    if not isinstance(function_args, dict):
                        function_args = {}
                    
                    logging.info(f"NATIVE TOOL CALL: {function_name}({function_args})")
                    # Silently execute the native tool instead of printing to console
                    try:
                        function_response = function_to_call(**function_args)
                    except Exception as e:
                        function_response = f"Error executing tool: {str(e)}"
                        
                    logging.info(f"NATIVE TOOL RESULT: {function_response}")
                    self.messages.append(
                        {
                            "role": "user",
                            "content": f"The tool '{function_name}' returned:\n{str(function_response)}\n\nPlease summarize this for the user without making up any additional information.",
                        }
                    )
            else:
                if response_message.content:
                    # Clear the "Agent is thinking..." line by moving up and clearing the line (ANSI escape)
                    print("\033[A\033[K", end="")
                    return response_message.content
                else:
                    print("\033[A\033[K", end="")
                    return "Sorry, I am having trouble interpreting the database. Let's try rephrasing."
                    
        print("\033[A\033[K", end="")
        return "I've reached my maximum internal iteration limit. Please tell me exactly what you'd like me to output."
