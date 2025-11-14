# Sirius-WB-Agent

## Web tools на основе Playwright

Установка:

```
pip install -r requirements.txt
playwright install-deps
playwright install chromium
```

Пример использования:

```
from pathlib import Path
from web_tools import make_web_tools, init_session, close_session

# Пример создания агента
web_agent = init_session(screenshot_path=Path("screenshots"), headless=True) # headless=False для отображения браузера
# Список инструментов для агентной модели
web_tools = make_web_tools(agent)

web_agent.screenshot()
web_agent.click_and_screenshot(100, 100, click_count=1)
web_agent.fill_and_screenshot(600, 75, 'Зеленый свитер', press_enter=True)
web_agent.wait(10000)

close_session()
```