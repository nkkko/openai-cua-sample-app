import time
import base64
import importlib.util
import sys
from typing import Literal, List, Dict, Optional, Tuple

# Check if daytona-sdk is installed
if importlib.util.find_spec("daytona_sdk") is None:
    raise ImportError(
        "The daytona-sdk package is required to use DaytonaComputer. "
        "Please install it using: pip install daytona-sdk"
    )

from daytona_sdk import Daytona, CreateWorkspaceParams, DaytonaConfig
from daytona_sdk.daytona import WorkspaceResources


class DaytonaComputer:
    environment = "linux"
    dimensions = (1280, 720)  # Default fallback; will be updated in __enter__

    def __init__(
        self,
        api_key: Optional[str] = None,
        server_url: Optional[str] = None,
        target: Optional[str] = None,
        workspace_name: str = "cua-sandbox",
        image: str = "nikodaytona/ubuntu-vnc-firefox:1.0.0",
        display: str = ":99",
        auto_stop_interval: int = 30,  # minutes
    ):
        """
        Initialize a Daytona computer.

        Args:
            api_key: Daytona API key (uses DAYTONA_API_KEY env var if not provided)
            server_url: Daytona server URL (uses DAYTONA_SERVER_URL env var if not provided)
            target: Target region (uses DAYTONA_TARGET env var if not provided)
            workspace_name: Name for the workspace
            image: Docker image to use for the workspace (defaults to "nikodaytona/ubuntu-vnc-firefox:1.0.0")
            display: X11 display identifier
            auto_stop_interval: Auto-stop interval in minutes (0 for no auto-stop)
        """
        self.workspace_name = workspace_name
        self.image = image
        self.display = display
        self.auto_stop_interval = auto_stop_interval

        # Initialize Daytona client
        if api_key and server_url:
            config = DaytonaConfig(
                api_key=api_key,
                server_url=server_url,
                target=target or "us"
            )
            self.daytona = Daytona(config)
        else:
            # Use environment variables
            self.daytona = Daytona()

        self.workspace = None

    def __enter__(self):
        # Create a Daytona workspace
        params = CreateWorkspaceParams(
            language="python",
            name=self.workspace_name,
            image=self.image,
            resources=WorkspaceResources(
                cpu=2,
                memory=4,  # 4GB RAM
                disk=10    # 20GB disk
            ),
            env_vars={"DISPLAY": self.display},
            auto_stop_interval=self.auto_stop_interval
        )

        print(f"Creating Daytona workspace '{self.workspace_name}'...")
        self.workspace = self.daytona.create(params)

        # Install necessary tools if they're not already in the image
        print("Installing required tools...")
        self._exec("apt-get update && apt-get install -y imagemagick xdotool x11-utils")

        # Make sure the X server is running
        print("Starting X server...")
        display_num = self.display.replace(":", "")

        # Check if the X server is already running
        check_x = self._exec(f"ps aux | grep Xvfb | grep {display_num}")
        if not check_x or "grep" in check_x:
            self._exec(f"Xvfb {self.display} -screen 0 1280x720x24 &")

        # Start a window manager if needed
        check_wm = self._exec("ps aux | grep fluxbox")
        if not check_wm or "grep" in check_wm:
            self._exec(f"export DISPLAY={self.display} && fluxbox &")

        # Get the display dimensions
        geometry = self._exec(f"DISPLAY={self.display} xdotool getdisplaygeometry").strip()
        if geometry:
            w, h = geometry.split()
            self.dimensions = (int(w), int(h))

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"Removing Daytona workspace '{self.workspace_name}'...")
        if self.workspace:
            self.daytona.remove(self.workspace)

    def _exec(self, cmd: str) -> str:
        """
        Execute a command in the Daytona workspace
        """
        if not self.workspace:
            raise RuntimeError("Workspace not initialized")

        response = self.workspace.process.exec(cmd)
        return response.result

    def screenshot(self) -> str:
        """
        Takes a screenshot with ImageMagick (import), returning base64-encoded PNG.
        """
        cmd = (
            f"export DISPLAY={self.display} && "
            "import -window root png:- | base64 -w 0"
        )

        return self._exec(cmd)

    def click(self, x: int, y: int, button: str = "left") -> None:
        button_map = {"left": 1, "middle": 2, "right": 3}
        b = button_map.get(button, 1)
        self._exec(f"DISPLAY={self.display} xdotool mousemove {x} {y} click {b}")

    def double_click(self, x: int, y: int) -> None:
        self._exec(
            f"DISPLAY={self.display} xdotool mousemove {x} {y} click --repeat 2 1"
        )

    def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        """
        For simple vertical scrolling: xdotool click 4 (scroll up) or 5 (scroll down).
        """
        self._exec(f"DISPLAY={self.display} xdotool mousemove {x} {y}")
        clicks = abs(scroll_y)
        button = 4 if scroll_y < 0 else 5
        for _ in range(clicks):
            self._exec(f"DISPLAY={self.display} xdotool click {button}")

    def type(self, text: str) -> None:
        """
        Type the given text via xdotool, preserving spaces and quotes.
        """
        # Escape single quotes in the user text: ' -> '\'\''
        safe_text = text.replace("'", "'\\''")
        # Then wrap everything in single quotes for xdotool
        cmd = f"DISPLAY={self.display} xdotool type -- '{safe_text}'"
        self._exec(cmd)

    def wait(self, ms: int = 1000) -> None:
        time.sleep(ms / 1000)

    def move(self, x: int, y: int) -> None:
        self._exec(f"DISPLAY={self.display} xdotool mousemove {x} {y}")

    def keypress(self, keys: List[str]) -> None:
        mapping = {
            "ENTER": "Return",
            "LEFT": "Left",
            "RIGHT": "Right",
            "UP": "Up",
            "DOWN": "Down",
            "ESC": "Escape",
            "SPACE": "space",
            "BACKSPACE": "BackSpace",
            "TAB": "Tab",
        }
        mapped_keys = [mapping.get(key, key) for key in keys]
        combo = "+".join(mapped_keys)
        self._exec(f"DISPLAY={self.display} xdotool key {combo}")

    def drag(self, path: List[Dict[str, int]]) -> None:
        if not path:
            return
        start_x = path[0]["x"]
        start_y = path[0]["y"]
        self._exec(
            f"DISPLAY={self.display} xdotool mousemove {start_x} {start_y} mousedown 1"
        )
        for point in path[1:]:
            self._exec(f"DISPLAY={self.display} xdotool mousemove {point['x']} {point['y']}")
        self._exec(f"DISPLAY={self.display} xdotool mouseup 1")

    def get_current_url(self) -> str:
        """
        Return empty string as this is not a browser-based computer
        """
        return ""