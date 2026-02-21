import sqlite3
from db import get_connection
from typing import List, Dict, Optional
import datetime

# Categories: 'Jira', 'Email', 'Unplanned_Work', 'Personal', 'Meeting'
# Priorities: 'Critical', 'High', 'Medium', 'Low'
# Status: 'pending', 'in_progress', 'completed', 'blocked', 'all'

def add_task(description: str = "", category: str = "Unplanned_Work", priority: str = 'Medium', source_id: Optional[str] = None, due_date: Optional[str] = None, **kwargs) -> str:
    """Adds a new task to the persistent SQLite database."""
    if not description:
        return "Error: Missing required parameter 'description'."
    if not category:
        category = "Unplanned_Work"
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (description, category, priority, source_id, due_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (description, category, priority, source_id, due_date))
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return f"Task added successfully with ID: {task_id}"

def list_tasks(status: str = 'all', category: Optional[str] = None, **kwargs) -> str:
    """Lists current active tasks based on status and optionally category."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, description, category, priority, source_id, due_date, status FROM tasks WHERE 1=1"
    params = []
    
    if status != 'all':
        query += " AND status = ?"
        params.append(status)
        
    if category:
        query += " AND category = ?"
        params.append(category)
        
    query += " ORDER BY CASE priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 WHEN 'Low' THEN 4 ELSE 5 END"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        status_str = f"status '{status}'" if status != 'all' else "any status"
        return f"No tasks found with {status_str}" + (f" in category {category}" if category else ".")
        
    result = f"Current tasks ({status}):\n"
    for row in rows:
        t_id, desc, cat, prio, src_id, due, stat = row
        src_str = f" [{src_id}]" if src_id else ""
        due_str = f" (Due: {due})" if due else ""
        result += f"- ID {t_id}: [{prio}] [{stat}] [{cat}]{src_str} {desc}{due_str}\n"
    return result

def search_historical_tasks(query: str = "", days_back: int = 365, **kwargs) -> str:
    """Searches for completed or old tasks over the past year. Crucial for performance reviews and remembering past work."""
    if not query:
        return "Error: Missing required parameter 'query'."
        
    days_back = int(days_back)
    conn = get_connection()
    cursor = conn.cursor()
    
    target_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
    
    sql = """
        SELECT id, description, category, status, completed_at, source_id 
        FROM tasks 
        WHERE description LIKE ? AND created_at >= ?
        ORDER BY created_at DESC
    """
    
    cursor.execute(sql, ('%' + query + '%', target_date.strftime("%Y-%m-%d %H:%M:%S")))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return f"No historical tasks found matching '{query}' in the last {days_back} days."
        
    result = f"Historical tasks matching '{query}':\n"
    for row in rows:
        t_id, desc, cat, stat, comp_at, src_id = row
        src_str = f" [{src_id}]" if src_id else ""
        comp_str = f" (Completed: {comp_at})" if comp_at else ""
        result += f"- ID {t_id}: [{cat}]{src_str} {desc} [{stat}]{comp_str}\n"
    return result

def update_task(task_id: int = 0, status: str = "", description: str = "", due_date: str = "", priority: str = "", **kwargs) -> str:
    """Updates an existing task's properties. Provide only the fields you want to update."""
    if not task_id:
        return "Error: Missing required parameter 'task_id'."
        
    task_id = int(task_id)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if status:
        valid_statuses = ['pending', 'in_progress', 'completed', 'blocked']
        if status not in valid_statuses:
            return f"Error: Invalid status. Must be one of: {', '.join(valid_statuses)}"
        updates.append("status = ?")
        params.append(status)
        if status == 'completed':
            updates.append("completed_at = CURRENT_TIMESTAMP")
            
    if description:
        updates.append("description = ?")
        params.append(description)
        
    if due_date:
        updates.append("due_date = ?")
        params.append(due_date)
        
    if priority:
        valid_priorities = ['Critical', 'High', 'Medium', 'Low']
        if priority not in valid_priorities:
            return f"Error: Invalid priority. Must be one of: {', '.join(valid_priorities)}"
        updates.append("priority = ?")
        params.append(priority)
        
    if not updates:
        return "Error: No fields provided to update."
        
    query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
    params.append(task_id)
    
    cursor.execute(query, params)
    
    if cursor.rowcount == 0:
        conn.close()
        return f"Error: Task ID {task_id} not found."
        
    conn.commit()
    conn.close()
    return f"Task ID {task_id} updated successfully."

def delete_task(task_id: int = 0, **kwargs) -> str:
    """Hard-deletes a task from the database."""
    if not task_id:
        return "Error: Missing required parameter 'task_id'."
        
    task_id = int(task_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        return f"Task ID {task_id} not found."
        
    conn.commit()
    conn.close()
    return f"Task ID {task_id} deleted."
