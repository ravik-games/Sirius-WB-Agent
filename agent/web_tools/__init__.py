import json5
from typing import List
from qwen_agent.llm.schema import ContentItem
from qwen_agent.tools.base import BaseTool, register_tool
from .web_agent_tools import get_agent_async

# ---------- helper (optionally) ----------
# No run_until_complete here — we are in an async environment (FastAPI).

# ---------- Click ----------
@register_tool("click")
class ClickTool(BaseTool):
    description = (
        "Clicks at given X,Y coordinates with left/right/middle button and optional double click. "
        "Returns a screenshot after the action."
    )
    parameters = [
        {'name':'x','type':'integer','required':True},
        {'name':'y','type':'integer','required':True},
        {'name':'button','type':'string','required':False},
        {'name':'click_count','type':'integer','required':False},
    ]

    async def call(self, params: str, **kwargs) -> List[ContentItem]:
        args = json5.loads(params)
        # support either [x,y] or separate fields
        if isinstance(args.get('x'), list):
            x, y = args['x']
        else:
            x, y = int(args['x']), int(args['y'])
        button = args.get('button', 'left')
        click_count = args.get('click_count', 1)

        agent = await get_agent_async()
        path = await agent.click_and_screenshot(
            x=x, y=y, button=button, click_count=click_count
        )
        return [ContentItem(image=str(path))]


# ---------- TypeText ----------
@register_tool("type_text")
class TypeTextTool(BaseTool):
    is_async = True
    description = "Type text into the currently focused field and return a screenshot."

    parameters = [
        {'name':'text','type':'string','required':True},
        {'name':'press_enter','type':'boolean','required':False},
        {'name':'clear_before','type':'boolean','required':False},
    ]

    async def call(self, params: str, **kwargs) -> List[ContentItem]:
        args = json5.loads(params)
        text = args['text']
        press_enter = args.get('press_enter', True)
        clear_before = args.get('clear_before', True)

        agent = await get_agent_async()
        path = await agent.fill_and_screenshot(
            text=text, press_enter=press_enter, clear_before=clear_before
        )
        return [ContentItem(image=str(path))]


# ---------- Scroll ----------
@register_tool("scroll")
class ScrollTool(BaseTool):
    is_async = True
    description = "Scrolls the page and returns a screenshot."

    parameters = [
        {'name':'delta_x','type':'integer','required':False},
        {'name':'delta_y','type':'integer','required':False},
    ]

    async def call(self, params: str, **kwargs) -> List[ContentItem]:
        args = json5.loads(params) if params else {}
        delta_x = -args.get('delta_x', 0)
        delta_y = -args.get('delta_y', 1000)

        agent = await get_agent_async()
        path = await agent.scroll_and_screenshot(delta_x=delta_x, delta_y=delta_y)
        return [ContentItem(image=str(path))]


# ---------- Wait ----------
@register_tool("wait")
class WaitTool(BaseTool):
    is_async = True
    description = "Waits for ms milliseconds then returns a screenshot."

    parameters = [{'name':'ms','type':'integer','required':False}]

    async def call(self, params: str, **kwargs) -> List[ContentItem]:
        args = json5.loads(params) if params else {}
        ms = args.get('ms', 1000)
        agent = await get_agent_async()
        path = await agent.wait(ms=ms)
        return [ContentItem(image=str(path))]


# ---------- Go Back ----------
@register_tool("go_back")
class GoBackTool(BaseTool):
    is_async = True
    description = "Goes back in history and returns screenshot."

    async def call(self, params: str, **kwargs) -> List[ContentItem]:
        agent = await get_agent_async()
        path = await agent.go_back_and_screenshot()
        return [ContentItem(image=str(path))]


# ---------- Get Current URL ----------
@register_tool("get_current_url")
class GetCurrentURL(BaseTool):
    is_async = True
    description = "Returns current page URL."

    async def call(self, params: str, **kwargs) -> List[ContentItem]:
        agent = await get_agent_async()
        return [ContentItem(text=agent.get_current_url())]


# ---------- Zoom ----------
@register_tool("zoom")
class ZoomTool(BaseTool):
    is_async = True
    description = "Zoom bbox to viewport and return screenshot."

    parameters = [
      {'name':'x','type':'number','required':True},
      {'name':'y','type':'number','required':True},
      {'name':'width','type':'number','required':True},
      {'name':'height','type':'number','required':True},
    ]

    async def call(self, params: str, **kwargs) -> List[ContentItem]:
        args = json5.loads(params)
        x, y, width, height = args['x'], args['y'], args['width'], args['height']
        agent = await get_agent_async()
        path = await agent.zoom_bbox_and_screenshot(x=x, y=y, width=width, height=height)
        return [ContentItem(image=str(path))]


def make_web_tools() -> list[BaseTool]:
    return [
        ClickTool(),
        TypeTextTool(),
        ScrollTool(),
        WaitTool(),
        GoBackTool(),
        GetCurrentURL(),
        ZoomTool(),
    ]
