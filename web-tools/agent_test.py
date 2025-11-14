from web_agent_tools import *

# Пример работы
agent = get_agent(headless=False, slow_mo_ms=100, viewport=(900, 900))
agent.screenshot()

agent.click_and_screenshot(600, 75, click_count=1)

agent.fill_and_screenshot(600, 75, "Зеленый свитер", press_enter=True)

agent.scroll_and_screenshot(delta_y=200)