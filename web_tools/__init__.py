from pathlib import Path
from typing import Optional

from web_tools.web_agent_tools import close_agent, WebAgent, get_agent


def init_session(
        headless: bool = False,
        url: str = "https://www.wildberries.ru/",
        slow_mo_ms: int = 0,
        viewport: Optional[tuple[int, int]] = (1000, 1000),
        user_agent: Optional[str] = None,
        screenshot_path: Path = Path("web-tools/screenshots"),
) -> WebAgent:

    agent = get_agent(
        headless=headless, url=url, slow_mo_ms=slow_mo_ms, viewport=viewport, user_agent=user_agent,
        screenshot_path=screenshot_path
    )

    return agent

def close_session() -> None:
    close_agent()

def make_web_tools(agent: WebAgent) -> list:
    web_tools = [
        {
            "name": "Screenshot",
            "description": "Makes screenshot of the current web-page status. Returns created image.",
            "parameters": {},
            "function": agent.screenshot
        },
        {
            "name": "Click",
            "description": "Clicks at given X,Y coordinates with left/right/middle button and optional double click. Returns a screenshot after the action.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "X coordinate in CSS pixels from 0 to 1000."
                    },
                    "y": {
                        "type": "integer",
                        "description": "Y coordinate in CSS pixels from 0 to 1000."
                    },
                    "button": {
                        "type": "string",
                        "enum": ["left", "right", "middle"],
                        "default": "left",
                        "description": "Mouse button to click."
                    },
                    "click_count": {
                        "type": "integer",
                        "enum": [1, 2],
                        "default": 1,
                        "description": "Number of clicks."
                    },
                },
                "required": ["x", "y"],
            },
            "function": agent.click_and_screenshot
        },
        {
            "name": "TypeText",
            "description": "Focuses at X,Y, optionally clears the input, optionally presses Enter, then returns a screenshot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "X coordinate in CSS pixels from 0 to 1000."
                    },
                    "y": {
                        "type": "integer",
                        "description": "Y coordinate in CSS pixels from 0 to 1000."
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to type into the focused field."
                    },
                    "press_enter": {
                        "type": "boolean",
                        "default": False,
                        "description": "Press Enter after typing."
                    },
                    "clear_before": {
                        "type": "boolean",
                        "default": True,
                        "description": "Clears input field before typing."
                    },
                },
                "required": ["x", "y", "text"]
            },
            "function": agent.fill_and_screenshot
        },
        {
            "name": "Scroll",
            "description": "Scrolls the page by deltaX and deltaY and returns a screenshot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "delta_x": {
                        "type": "integer",
                        "default": 0,
                        "description": "Horizontal scroll delta (positive = right, negative = left)."
                    },
                    "delta_y": {
                        "type": "integer",
                        "default": 800,
                        "description": "Vertical scroll delta (positive = down, negative = up)."
                    },
                }
            },
            "function": agent.scroll_and_screenshot
        },
        {
            "name": "Wait",
            "description": "Waits for a specified number of milliseconds, then returns a screenshot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ms": {
                        "type": "integer",
                        "default": 1000,
                        "description": "Milliseconds to wait."
                    }
                }
            },
            "function": agent.wait
        },
    ]
    return web_tools
