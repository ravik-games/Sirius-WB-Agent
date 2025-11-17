import base64
import os
from pathlib import Path
from typing import Optional, List, Generator
import json5
from qwen_agent.agents import Assistant

from web_tools.web_agent_tools import WebAgent
from web_tools import make_web_tools, init_session
from config import settings
import prompts

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

def clear_session():
    global _web_agent_singleton
    if _web_agent_singleton is not None:
        try:
            _web_agent_singleton.close()
        finally:
            _web_agent_singleton = None

def file_to_base64(file_path: str) -> str | None:
    """
    Преобразует файл изображения в строку данных Data URI (base64).
    """
    if not file_path or not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/png;base64,{encoded_string}"
    except IOError as e:
        print(f"Ошибка при чтении файла {file_path}: {e}")
        return None


def run_agent(query: str, messages: List = None) -> Generator[str, None, None]:
    """
    Запуск агента с заданной историей сообщений и входным запросом.
    """
    agent, web_agent = get_agents(show_browser=False)

    if not messages:
        messages = []

    start_screen_path = web_agent.screenshot()
    start_screen_base64 = file_to_base64(str(start_screen_path))
    chunk_data = {"type": "image", "content": start_screen_base64}
    yield json5.dumps(chunk_data, ensure_ascii=False) + "\n"

    messages += [
        {"role": "user", "content": [
            {"image": start_screen_base64},
            {"text": prompts.QUERY_PROMPT.format(query=query)}
        ]}
    ]

    for ret_messages_list in agent.run(messages):
        if ret_messages_list:
            last_message = ret_messages_list[-1]
            content = last_message.get('content', '') if isinstance(last_message, dict) else last_message.content

            if isinstance(content, str):
                chunk_data = {"type": "text", "content": content}
                yield json5.dumps(chunk_data, ensure_ascii=False) + "\n"
            elif isinstance(content, list):
                for item in content:
                    if 'text' in item and item['text']:
                        chunk_data = {"type": "text", "content": item['text']}
                        yield json5.dumps(chunk_data, ensure_ascii=False) + "\n"
                    elif 'image' in item and item['image']:
                        image_data = item['image']
                        image_data = file_to_base64(image_data)
                        chunk_data = {"type": "image", "content": image_data}
                        yield json5.dumps(chunk_data, ensure_ascii=False) + "\n"

    clear_session()
    yield json5.dumps({"type": "status", "content": "end"}, ensure_ascii=False) + "\n"