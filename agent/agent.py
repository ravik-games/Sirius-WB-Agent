from pathlib import Path
from typing import Optional, List

import anyio

from .web_tools.web_agent_tools import WebAgent, init_session, close_session
from .web_tools import make_web_tools
from .config import settings
from . import prompts

from qwen_agent.utils.output_beautify import multimodal_typewriter_print
from qwen_agent.agents import Assistant

# Конфиг работы LLM/VLM модели агента
llm_cfg = {
    'model_type': settings.model_type,
    'model': settings.model_name,
    'model_server': settings.model_server,
    'api_key': settings.api_key,

    'generate_cfg': {
        "temperature": 0.05,
        "top_p": 1.0,
        "repetition_penalty": 1.1
    }
}

_agent_singleton: Optional[Assistant] = None
_web_agent_singleton: Optional[WebAgent] = None

async def init_agent(show_browser: bool = False):
    """
    Инициализация агентов.
    """
    web_agent = await init_session(screenshot_path=Path("../screenshots"), headless=not show_browser)
    web_tools = make_web_tools()

    agent = Assistant(
        llm=llm_cfg,
        function_list=web_tools,
        system_message=prompts.SYSTEM_PROMPT,
    )
    return agent, web_agent

async def get_agents(show_browser: bool = False):
    """
    Возвращает созданный или существующий экземпляр Assistant и WebAgent.
    """
    global _agent_singleton, _web_agent_singleton

    if _agent_singleton is None:
        _agent_singleton, _web_agent_singleton = await init_agent(show_browser=show_browser)

    return _agent_singleton, _web_agent_singleton

async def run_agent(query: str, messages: List = None):
    """
    Запуск агента с заданной историей сообщений и входным запросом.
    """
    agent, web_agent = await get_agents(show_browser=False)

    if not messages:
        messages = []

    start_screen = await web_agent.screenshot()
    messages += [
        {"role": "user", "content": [
            {"image": str(start_screen)},
            {"text": prompts.QUERY_PROMPT.format(query=query)}
        ]}
    ]

    # TODO подумать как возвращать ответ и размышления агента
    response_plain_text = ''
    for ret_messages in agent.run(messages):
        response_plain_text = multimodal_typewriter_print(ret_messages, response_plain_text)

    await close_session()

    return response_plain_text

async def run_agent_async(agent, message):
    result = await anyio.to_thread.run_sync(agent.run, message)
    return result