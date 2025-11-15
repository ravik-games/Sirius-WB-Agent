from pathlib import Path
from typing import Optional, List

from agent.web_tools import WebAgent
from web_tools import make_web_tools, init_session, close_session
from config import settings
import prompts

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

def run_agent(query: str, messages: List = None):
    """
    Запуск агента с заданной историей сообщений и входным запросом.
    """
    agent, web_agent = get_agents(show_browser=True)

    if not messages:
        messages = []

    start_screen = web_agent.screenshot()
    messages += [
        {"role": "user", "content": [
            {"image": str(start_screen)},
            {"text": prompts.QUERY_PROMPT} # TODO
        ]}
    ]

    # TODO подумать как возвращать ответ и размышления агента
    response_plain_text = ''
    for ret_messages in agent.run(messages):
        response_plain_text = multimodal_typewriter_print(ret_messages, response_plain_text)

    close_session()

    return response_plain_text