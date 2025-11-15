from pathlib import Path
from typing import Optional
import json5
from web_tools.web_agent_tools import close_agent, WebAgent, get_agent
from qwen_agent.tools.base import BaseTool, register_tool

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


@register_tool("click")
class ClickTool(BaseTool):
    description = (
        "Clicks at given X,Y coordinates with left/right/middle button and optional double click. "
        "Returns a screenshot after the action."
    )
    parameters = [
        {
            'name': 'x',
            'type': 'integer',
            'description': 'X coordinate in CSS pixels from 0 to 1000.',
            'required': True
        },
        {
            'name': 'y',
            'type': 'integer',
            'description': 'Y coordinate in CSS pixels from 0 to 1000.',
            'required': True
        },
        {
            'name': 'button',
            'type': 'string',
            'description': "Mouse button to click: 'left', 'right', or 'middle'.",
            'required': False
        },
        {
            'name': 'click_count',
            'type': 'integer',
            'description': 'Number of clicks: 1 for single click, 2 for double click.',
            'required': False
        },
    ]

    def call(self, params: str, **kwargs) -> str:
        args = json5.loads(params)
        x = args['x']
        y = args['y']
        button = args.get('button', 'left')
        click_count = args.get('click_count', 1)

        agent = get_agent()
        path = agent.click_and_screenshot(
            x=x,
            y=y,
            button=button,
            click_count=click_count,
        )
        return str(path)


@register_tool("type_text")
class TypeTextTool(BaseTool):
    description = (
        "Focuses at X,Y, optionally clears the input, optionally presses Enter, "
        "then returns a screenshot."
    )
    parameters = [
        {
            'name': 'x',
            'type': 'integer',
            'description': 'X coordinate in CSS pixels from 0 to 1000.',
            'required': True
        },
        {
            'name': 'y',
            'type': 'integer',
            'description': 'Y coordinate in CSS pixels from 0 to 1000.',
            'required': True
        },
        {
            'name': 'text',
            'type': 'string',
            'description': 'Text to type into the focused field.',
            'required': True
        },
        {
            'name': 'press_enter',
            'type': 'boolean',
            'description': 'Press Enter after typing.',
            'required': True
        },
        {
            'name': 'clear_before',
            'type': 'boolean',
            'description': 'Clears input field before typing.',
            'required': True
        },
    ]

    def call(self, params: str, **kwargs) -> str:
        args = json5.loads(params)
        x = args['x']
        y = args['y']
        text = args['text']
        press_enter = args.get('press_enter', True)
        clear_before = args.get('clear_before', False)

        agent = get_agent()
        path = agent.fill_and_screenshot(
            x=x,
            y=y,
            text=text,
            press_enter=press_enter,
            clear_before=clear_before,
        )
        return str(path)


@register_tool("scroll")
class ScrollTool(BaseTool):
    description = "Scrolls the page by deltaX and deltaY and returns a screenshot."
    parameters = [
        {
            'name': 'delta_x',
            'type': 'integer',
            'description': 'Horizontal scroll delta (positive = right, negative = left).',
            'required': False
        },
        {
            'name': 'delta_y',
            'type': 'integer',
            'description': 'Vertical scroll delta (positive = down, negative = up).',
            'required': False
        },
    ]

    def call(self, params: str, **kwargs) -> str:
        args = json5.loads(params) if params else {}
        delta_x = args.get('delta_x', 0)
        delta_y = args.get('delta_y', 800)

        agent = get_agent()
        path = agent.scroll_and_screenshot(
            delta_x=delta_x,
            delta_y=delta_y,
        )
        return str(path)


@register_tool("wait")
class WaitTool(BaseTool):
    description = "Waits for a specified number of milliseconds, then returns a screenshot."
    parameters = [
        {
            'name': 'ms',
            'type': 'integer',
            'description': 'Milliseconds to wait.',
            'required': False
        },
    ]

    def call(self, params: str, **kwargs) -> str:
        args = json5.loads(params) if params else {}
        ms = args.get('ms', 1000)
        agent = get_agent()
        path = agent.wait(ms=ms)
        return str(path)

def make_web_tools(agent: WebAgent | None = None) -> list[BaseTool]:
    """Возвращает список зарегистрированных web-tools.

    Параметр agent сохраняем для обратной совместимости, но не используем,
    так как инструменты работают через singleton get_agent().
    """
    return [
        ClickTool(),
        TypeTextTool(),
        ScrollTool(),
        WaitTool(),
    ]