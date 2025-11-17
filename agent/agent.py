from pathlib import Path
from typing import Optional, List, Generator

import json5

from web_tools.web_agent_tools import WebAgent
from web_tools import make_web_tools, init_session, close_session
from config import settings
import prompts
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

def init_agent(show_browser: bool = False):
    """
    Инициализация агентов.
    """
    web_agent = init_session(screenshot_path=Path("../screenshots"), headless=not show_browser)
    web_tools = make_web_tools()

    agent = Assistant(
        llm=llm_cfg,
        function_list=web_tools,
        system_message=prompts.SYSTEM_PROMPT,
    )
    return agent, web_agent

def get_agents(show_browser: bool = False):
    """
    Возвращает созданный или существующий экземпляр Assistant и WebAgent.
    """
    global _agent_singleton, _web_agent_singleton

    if _agent_singleton is None:
        _agent_singleton, _web_agent_singleton = init_agent(show_browser=show_browser)

    return _agent_singleton, _web_agent_singleton

def run_agent(query: str, messages: List = None) -> Generator[str, None, None]:
    """
    Запуск агента с заданной историей сообщений и входным запросом.
    """
    agent, web_agent = get_agents(show_browser=False)

    if not messages:
        messages = []

    start_screen = web_agent.screenshot()
    messages += [
        {"role": "user", "content": [
            {"image": str(start_screen)},
            {"text": prompts.QUERY_PROMPT.format(query=query)}
        ]}
    ]

    for ret_messages_list in agent.run(messages):
        if ret_messages_list:
            last_message = ret_messages_list[-1]
            content = last_message.get('content', '') if isinstance(last_message, dict) else last_message.content

            if isinstance(content, str):
                chunk_data = {"type": "text", "content": content}
                yield json5.dumps(chunk_data) + "\n"
            elif isinstance(content, list):
                for item in content:
                    if 'text' in item and item['text']:
                        chunk_data = {"type": "text", "content": item['text']}
                        yield json5.dumps(chunk_data) + "\n"
                    elif 'image' in item and item['image']:
                        chunk_data = {"type": "image", "content": item['image']}
                        yield json5.dumps(chunk_data) + "\n"
                    elif 'image_url' in item and item['image_url'].get('url'):
                        chunk_data = {"type": "image", "content": item['image_url']['url']}
                        yield json5.dumps(chunk_data) + "\n"

    close_session()
    yield json5.dumps({"type": "status", "content": "session_closed"}) + "\n"