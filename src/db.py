import sqlite3
import os
from datetime import datetime
from rich.console import Console

console = Console()

# We save the DB in a persistent user directory, ensuring year-long retention
DB_DIR = os.path.expanduser("~/.task_manager_ai")
DB_PATH = os.path.join(DB_DIR, "tasks.db")

def init_db():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        console.print(f"[green]Created database directory at {DB_DIR}[/green]")
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create the tasks table tailored for an Android Platform Engineer
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        status TEXT DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'blocked'
        priority TEXT DEFAULT 'Medium', -- 'Critical', 'High', 'Medium', 'Low'
        category TEXT DEFAULT 'Personal', -- 'Jira', 'Email', 'Unplanned_Work', 'Personal', 'Meeting'
        source_id TEXT, -- e.g., Jira Ticket ID limits like 'AND-1234'
        due_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)

if __name__ == "__main__":
    init_db()
    console.print(f"[bold green]Database initialized successfully at {DB_PATH}[/bold green]")
