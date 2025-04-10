from __future__ import annotations
from dotenv import load_dotenv
from rich.markdown import Markdown
from rich.console import Console
from rich.live import Live
import asyncio
from agent_service import service

load_dotenv()

async def main():
    """Run the CLI interface for the agent system."""
    print("MCP Agent Army - Multi-agent system using Model Context Protocol")
    print("Enter 'exit' to quit the program.")
    
    console = Console()
    messages = []        
        
    while True:
        # Get user input
        user_input = input("\n[You] ")
        
        # Check if user wants to exit
        if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            print("Goodbye!")
            break
        
        try:
            # Process the user input and output the response
            print("\n[Assistant]")
            with Live('', console=console, vertical_overflow='visible') as live:
                result = await service.process_query(user_input, message_history=messages)
                live.update(Markdown(result.get("result", "")))
            
            # Add the new messages to the chat history
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": result.get("result", "")})
            
        except Exception as e:
            print(f"\n[Error] An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
