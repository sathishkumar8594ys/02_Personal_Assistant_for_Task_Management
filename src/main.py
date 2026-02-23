import os
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# Load environment variables - explicitly point to the .env in the project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from db import init_db
from agent import TaskAgent

console = Console()

def main():
    console.print(Panel.fit("[bold blue]AI Task Orchestrator[/bold blue]"))
    
    # Ensure DB is created
    init_db()
    
    try:
        agent = TaskAgent()
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        console.print("Please set your API keys in a .env file or export them.")
        return

    console.print("[dim]Type 'exit' or 'quit' to close.[/dim]\n")
    
    while True:
        try:
            user_input = console.input("[bold green]You:[/] ")
            
            if user_input.lower() in ['exit', 'quit']:
                console.print("[yellow]Goodbye! Keep crushing those Jira tickets![/yellow]")
                break
                
            if not user_input.strip():
                continue
                
            response = agent.chat(user_input)
            console.print(f"[bold purple]Assistant:[/] {response}\n")
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]An error occurred:[/] {str(e)}")
            break

if __name__ == "__main__":
    main()
