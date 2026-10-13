import base64
import os
from collections import defaultdict, deque
from pathlib import Path
from typing import Optional, List, Generator
import json5
from qwen_agent.agents import Assistant
from qwen_agent.utils.output_beautify import multimodal_typewriter_print

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
        "temperature": 0.2,
        "top_p": 0.9,
        "repetition_penalty": 1.1
    }
}

# Кандидаты для вывода
MAX_CANDIDATES = 3

# ЗДЕСЬ НАДО СДЕЛАТЬ БД, ЭТО ТОЛЬКО ДЛЯ MVP
_user_history = defaultdict(list)
_user_candidates = defaultdict(lambda: deque(maxlen=MAX_CANDIDATES))

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

def reset_agent(show_browser: bool = False):
    global _agent_singleton, _web_agent_singleton
    _agent_singleton, _web_agent_singleton = init_agent(show_browser=show_browser)

def get_agents(show_browser: bool = False):
    """
    Возвращает созданный или существующий экземпляр Assistant и WebAgent.
    """
    global _agent_singleton, _web_agent_singleton

    if _agent_singleton is None:
        _agent_singleton, _web_agent_singleton = init_agent(show_browser=show_browser)

    return _agent_singleton, _web_agent_singleton

def _clear_session():
    global _web_agent_singleton
    _web_agent_singleton.close()

def _new_session():
    global _web_agent_singleton, _agent_singleton
    _web_agent_singleton.new_session()

def _file_to_base64(file_path: str) -> str | None:
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


def _run_agent(user_id: str, query: str, messages: List, debug_print: bool = False) -> Generator[str, None, None]:
    """
    Запуск агента с заданной историей сообщений и входным запросом.
    """
    global _user_candidates, _user_history
    agent, web_agent = get_agents(show_browser=False)
    _new_session()

    start_screen_path = web_agent.screenshot()
    start_screen_base64 = _file_to_base64(str(start_screen_path))
    chunk_data = {"type": "image", "content": start_screen_base64}
    yield json5.dumps(chunk_data, quote_keys=True, ensure_ascii=False) + "\n"

    messages += [
        {"role": "system", "content": [{"text": f"USER_QUERY::{query}"}]},
        {"role": "user", "content": [
            {"image": start_screen_base64},
            {"text": prompts.QUERY_PROMPT.format(query=query)}
        ]}
    ]

    ans = ''
    for ret_messages_list in agent.run(messages):
        if not ret_messages_list:
            continue

        if debug_print:
            ans = multimodal_typewriter_print(ret_messages_list, ans)

        last_message = ret_messages_list[-1]
        content = last_message.get('content', '') if isinstance(last_message, dict) else last_message.content

        if last_message.get("role") == "function" and last_message.get("name") == "validate_candidate_item":
            content = last_message["content"][0]
            text = content.get("text")
            response = json5.loads(text)
            if response.get("response") == "OK":
                _user_candidates[user_id].append(web_agent.get_current_url())

        if isinstance(content, str):
            chunk_data = {"type": "text", "content": content}
            yield json5.dumps(chunk_data, quote_keys=True, ensure_ascii=False) + "\n"
        elif isinstance(content, list):
            for item in content:
                if 'text' in item and item['text']:
                    chunk_data = {"type": "text", "content": item['text']}
                    yield json5.dumps(chunk_data, quote_keys=True, ensure_ascii=False) + "\n"
                elif 'image' in item and item['image']:
                    image_data = item['image']
                    image_data = _file_to_base64(image_data)
                    chunk_data = {"type": "image", "content": image_data}
                    yield json5.dumps(chunk_data, quote_keys=True, ensure_ascii=False) + "\n"

    _user_history[user_id] = messages
    _clear_session()
    print('Запрос завершен')
    yield json5.dumps({"type": "products", "items": list(_user_candidates[user_id])}, quote_keys=True, ensure_ascii=False) + "\n"

def run_new_search(user_id: str, query: str, debug_print: bool = False) -> Generator[str, None, None]:
    global _user_history, _user_candidates
    _user_history[user_id] = []
    _user_candidates[user_id] = deque(maxlen=MAX_CANDIDATES)
    yield from _run_agent(user_id, query, [], debug_print=debug_print)

def clarify_search(user_id: str, query: str) -> Generator[str, None, None]:
    global _user_history, _user_candidates
    messages = _user_history.get(user_id, [])
    _user_candidates[user_id] = deque(maxlen=MAX_CANDIDATES)
    yield from _run_agent(user_id, query, messages)