"""
Example of using the DaytonaComputer with the CUA loop.

To run this example:
1. Install the Daytona SDK: pip install daytona-sdk
2. Set environment variables or provide API credentials directly:
   - DAYTONA_API_KEY
   - DAYTONA_SERVER_URL
   - DAYTONA_TARGET (optional)
3. Run: python -m examples.daytona_example
"""

import os
import time
from computers import DaytonaComputer
from agent import Agent
from simple_cua_loop import run_cua_loop


def main():
    # You can provide credentials directly or use environment variables
    api_key = os.environ.get("DAYTONA_API_KEY")
    server_url = os.environ.get("DAYTONA_SERVER_URL")
    
    # Create a prompt for the agent
    prompt = """You are a helpful assistant that can control a computer. 
    Your goal is to create a simple text file that contains a greeting.
    
    1. Use the terminal to create a text file called 'greeting.txt' with the content "Hello, World!"
    2. Verify the file was created by viewing its contents
    """
    
    # Create an agent
    agent = Agent(model="gpt-4o-2024-05-13", prompt=prompt)
    
    with DaytonaComputer(
        api_key=api_key,
        server_url=server_url,
        workspace_name="cua-demo",
        image="nikodaytona/ubuntu-vnc-firefox:1.0.0",
        display=":99"
    ) as computer:
        # Run the CUA loop
        run_cua_loop(agent, computer)


if __name__ == "__main__":
    main()