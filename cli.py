import argparse
import os
from agent.agent import Agent
from computers import (
    BrowserbaseBrowser,
    ScrapybaraBrowser,
    ScrapybaraUbuntu,
    LocalPlaywrightComputer,
    DockerComputer,
    DaytonaComputer,
)


def acknowledge_safety_check_callback(message: str) -> bool:
    response = input(
        f"Safety Check Warning: {message}\nDo you want to acknowledge and proceed? (y/n): "
    ).lower()
    return response.lower().strip() == "y"


def main():
    parser = argparse.ArgumentParser(
        description="Select a computer environment from the available options."
    )
    parser.add_argument(
        "--computer",
        choices=[
            "local-playwright",
            "docker",
            "browserbase",
            "scrapybara-browser",
            "scrapybara-ubuntu",
            "daytona",
        ],
        help="Choose the computer environment to use.",
        default="local-playwright",
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Initial input to use instead of asking the user.",
        default=None,
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode for detailed output.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show images during the execution.",
    )
    parser.add_argument(
        "--start-url",
        type=str,
        help="Start the browsing session with a specific URL (only for browser environments).",
        default="https://bing.com",
    )
    # Daytona parameters
    parser.add_argument(
        "--daytona-api-key",
        type=str,
        help="API key for Daytona (only for daytona computer).",
        default=os.environ.get("DAYTONA_API_KEY"),
    )
    parser.add_argument(
        "--daytona-server-url",
        type=str,
        help="Server URL for Daytona (only for daytona computer).",
        default=os.environ.get("DAYTONA_SERVER_URL"),
    )
    parser.add_argument(
        "--daytona-target",
        type=str,
        help="Target region for Daytona (only for daytona computer).",
        default=os.environ.get("DAYTONA_TARGET", "us"),
    )
    parser.add_argument(
        "--display",
        type=str,
        help="X11 display identifier (only for docker and daytona computers).",
        default=":99",
    )
    args = parser.parse_args()

    computer_mapping = {
        "local-playwright": LocalPlaywrightComputer,
        "docker": DockerComputer,
        "browserbase": BrowserbaseBrowser,
        "scrapybara-browser": ScrapybaraBrowser,
        "scrapybara-ubuntu": ScrapybaraUbuntu,
        "daytona": DaytonaComputer,
    }

    ComputerClass = computer_mapping[args.computer]

    # Initialize the appropriate computer with any necessary parameters
    if args.computer == "daytona":
        if not args.daytona_api_key or not args.daytona_server_url:
            raise ValueError("Daytona API key and server URL are required for the Daytona computer")
        
        computer_instance = ComputerClass(
            api_key=args.daytona_api_key,
            server_url=args.daytona_server_url,
            target=args.daytona_target,
            display=args.display
        )
    else:
        computer_instance = ComputerClass()

    with computer_instance as computer:
        agent = Agent(
            computer=computer,
            acknowledge_safety_check_callback=acknowledge_safety_check_callback,
        )
        items = []

        while True:
            user_input = args.input or input("> ")
            items.append({"role": "user", "content": user_input})
            output_items = agent.run_full_turn(
                items,
                print_steps=True,
                show_images=args.show,
                debug=args.debug,
            )
            items += output_items
            args.input = None


if __name__ == "__main__":
    main()
