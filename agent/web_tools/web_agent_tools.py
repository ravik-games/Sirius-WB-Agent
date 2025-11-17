"""
Async Web Agent — Playwright (async) implementation

Переписанная в async версия твоего web_agent_tools.py.
Изменения:
- использует playwright.async_api
- фабрика WebAgent.create(...) вместо __init__ (async constructor)
- все публичные методы — async def, сохраняют имена: click_and_screenshot, fill_and_screenshot, scroll_and_screenshot, wait, go_back_and_screenshot, get_current_url, zoom_bbox_and_screenshot, screenshot, wait_until_stable, close
- ассинхронный singleton: get_agent_async / close_agent_async
- async init_session / close_session helper

Интерфейс остался максимально близким к оригиналу — теперь нужно вызывать методы через await.
"""
from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Optional, Literal

from playwright.async_api import (
    Playwright,
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PWTimeoutError,
    ViewportSize,
)


class WebAgent:
    """Async WebAgent using playwright.async_api.

    Use via factory:
        agent = await WebAgent.create(...)
        await agent.click_and_screenshot(...)
        await agent.close()
    """

    def __init__(
        self,
        headless: bool,
        url: str,
        slow_mo_ms: int,
        viewport: Optional[tuple[int, int]],
        user_agent: Optional[str],
        screenshot_path: Path,
    ) -> None:
        # constructor is lightweight — heavy init done in create()
        self._playwright_cm = None  # type: ignore
        self._pw: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self.url = url
        self.screenshot_path = screenshot_path
        self._headless = headless
        self._slow_mo_ms = slow_mo_ms
        self._viewport = viewport
        self._user_agent = user_agent

    @classmethod
    async def create(
        cls,
        headless: bool = True,
        url: str = "https://www.wildberries.ru/",
        slow_mo_ms: int = 0,
        viewport: Optional[tuple[int, int]] = (1366, 900),
        user_agent: Optional[str] = None,
        screenshot_path: Path = Path("screenshots"),
    ) -> "WebAgent":
        self = cls(headless, url, slow_mo_ms, viewport, user_agent, screenshot_path)

        # start playwright
        self._playwright_cm = async_playwright()
        self._pw = await self._playwright_cm.start()

        self._browser = await self._pw.chromium.launch(
            headless=headless,
            slow_mo=slow_mo_ms or 0,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--no-default-browser-check",
                "--disable-notifications",
            ],
        )

        context_args = dict(
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            ignore_https_errors=True,
        )
        if viewport:
            context_args["viewport"] = ViewportSize(width=viewport[0], height=viewport[1])

        if user_agent:
            context_args["user_agent"] = user_agent

        self._context = await self._browser.new_context(**context_args)
        self._page = await self._context.new_page()

        # navigate
        await self._page.goto(self.url, wait_until="load")
        await self.wait_until_stable(max_wait_ms=1000)
        return self

    # --------------------------- Публичные операции ---------------------------
    @property
    def page(self) -> Page:
        assert self._page is not None, "Страница ещё не инициализирована или агент закрыт"
        return self._page

    async def wait_until_stable(self, max_wait_ms: int = 500, dom_quiet_ms: int = 500) -> None:
        """Ждёт «стабилизацию» страницы — не только load, но и паузу DOM-мутаций."""
        p = self.page
        deadline = time.time() + max_wait_ms / 1000

        def _remaining() -> int:
            return max(0, int((deadline - time.time()) * 1000))

        try:
            await p.wait_for_load_state("domcontentloaded", timeout=_remaining())
        except PWTimeoutError:
            pass
        try:
            await p.wait_for_load_state("load", timeout=_remaining())
        except PWTimeoutError:
            pass
        await self._wait_for_dom_quiet(quiet_ms=dom_quiet_ms, timeout_ms=_remaining())

    async def screenshot(self, screenshot_path: Optional[str | os.PathLike] = None, full_page: bool = False) -> Path:
        """Сохраняет скриншот страницы и возвращает путь к файлу."""
        p = self.page
        out_path = self._ensure_path(screenshot_path)
        await self.wait_until_stable()
        await p.screenshot(path=str(out_path), full_page=full_page, type="png")
        return out_path

    async def click_and_screenshot(
        self,
        x: int,
        y: int,
        screenshot_path: Optional[str | os.PathLike] = None,
        button: Literal["left", "right", "middle"] = "left",
        click_count: int = 1,
        full_page: bool = False,
    ) -> Path:
        """Кликает мышью по координатам (x, y) в области страницы и делает скриншот."""
        p = self.page
        await p.mouse.click(x, y, button=button, click_count=click_count)
        await self.wait_until_stable()
        return await self.screenshot(screenshot_path, full_page=full_page)

    async def fill_and_screenshot(
        self,
        text: str,
        x: int = None,
        y: int = None,
        screenshot_path: Optional[str | os.PathLike] = None,
        press_enter: bool = False,
        typing_delay_ms: int = 10,
        clear_before: bool = True,
        full_page: bool = False,
    ) -> Path:
        """Кликает по координатам (x, y) для фокуса, вводит текст с клавиатуры и делает скриншот."""
        p = self.page
        if x is not None and y is not None:
            try:
                vs = p.viewport_size
                if vs is not None:
                    vw, vh = vs.get("width", 0), vs.get("height", 0)
                    if x < 0 or y < 0 or x >= vw or y >= vh:
                        raise ValueError(f"Coordinates out of viewport: ({x},{y}) not in [0..{vw - 1}]x[0..{vh - 1}]")
            except Exception:
                pass

            await p.mouse.click(x, y)
            await p.wait_for_timeout(300)

        if clear_before:
            try:
                await p.keyboard.press("Control+A")
                await p.keyboard.press("Delete")
            except Exception:
                pass

        if text:
            await p.keyboard.type(text, delay=max(0, typing_delay_ms))

        if press_enter:
            await p.keyboard.press("Enter")

        await self.wait_until_stable()
        return await self.screenshot(screenshot_path, full_page=full_page)

    async def scroll_and_screenshot(
        self,
        delta_x: int = 0,
        delta_y: int = 800,
        screenshot_path: Optional[str | os.PathLike] = None,
        full_page: bool = False,
    ) -> Path:
        """Скроллит страницу и делает скриншот."""
        p = self.page
        await p.mouse.wheel(delta_x, delta_y)
        await self.wait_until_stable()
        return await self.screenshot(screenshot_path, full_page=full_page)

    async def wait(
        self,
        ms: int = 1000,
        screenshot_path: Optional[str | os.PathLike] = None,
        full_page: bool = False,
    ) -> Path:
        """Ожидание и скриншот."""
        p = self.page
        await p.wait_for_timeout(ms)
        return await self.screenshot(screenshot_path, full_page=full_page)

    async def go_back_and_screenshot(
        self,
        screenshot_path: Optional[str | os.PathLike] = None,
        full_page: bool = False,
    ) -> Path:
        """Возвращается на предыдущую страницу браузера и делает скриншот.

        - если вышли за пределы исходного домена — возвращается на self.url
        """
        p = self.page
        await p.go_back()

        if self.url not in p.url:
            await p.goto(self.url)

        await self.wait_until_stable()
        return await self.screenshot(screenshot_path, full_page=full_page)

    def get_current_url(self) -> str:
        """Возвращает текущий URL страницы."""
        return self.page.url

    async def zoom_bbox_and_screenshot(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        screenshot_path: Optional[str | os.PathLike] = None,
    ) -> Path:
        """
        Приближает область (bbox) так, чтобы она заполняла весь viewport, и делает скриншот.
        Координаты bbox — в рамках текущего viewport.
        """
        p = self.page

        viewport = p.viewport_size
        if viewport is None:
            vpw = await p.evaluate("() => window.innerWidth")
            vph = await p.evaluate("() => window.innerHeight")
        else:
            vpw = viewport["width"]
            vph = viewport["height"]

        scale = min(vpw / width, vph / height)
        translate_x = -x
        translate_y = -y

        await p.evaluate(
            """({scale, tx, ty}) => {
                const body = document.body;
                body.style.transformOrigin = '0 0';
                body.style.transform = `translate(${tx}px, ${ty}px) scale(${scale})`;
            }""",
            {"scale": scale, "tx": translate_x, "ty": translate_y},
        )

        await self.wait_until_stable()
        path = await self.screenshot(screenshot_path, full_page=False)

        await p.evaluate("() => { document.body.style.transform = 'none'; }")
        return path

    async def close(self) -> None:
        """Закрыть страницу/контекст/браузер и Playwright."""
        try:
            if self._page:
                await self._page.close()
        except Exception:
            pass
        try:
            if self._context:
                await self._context.close()
        except Exception:
            pass
        try:
            if self._browser:
                await self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright_cm:
                await self._playwright_cm.stop()
        except Exception:
            pass
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._pw = None

    async def _wait_for_dom_quiet(self, quiet_ms: int = 800, timeout_ms: int = 10000) -> None:
        """Ожидание «тишины» DOM — отсутствия мутаций в течение quiet_ms подряд.

        Реализовано через MutationObserver внутри страницы.
        """
        if timeout_ms <= 0:
            return
        try:
            await self.page.evaluate(
                """
                (quietMs, timeoutMs) => {
                  return new Promise((resolve) => {
                    let done = false;
                    const cleanup = () => { if (!done) { done = true; observer.disconnect(); clearTimeout(timeout); resolve(true); } };
                    const observer = new MutationObserver(() => {
                      clearTimeout(quietTimer);
                      quietTimer = setTimeout(cleanup, quietMs);
                    });
                    observer.observe(document, { subtree: true, childList: true, attributes: true, characterData: true });
                    // Если мутаций нет — всё равно сработает через quietMs
                    let quietTimer = setTimeout(cleanup, quietMs);
                    const timeout = setTimeout(cleanup, timeoutMs);
                  });
                }
                """,
                quiet_ms,
            )
        except Exception:
            pass

    def _ensure_path(self, screenshot_path: Optional[str | os.PathLike]) -> Path:
        if screenshot_path:
            p = Path(screenshot_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
                p = p.with_suffix(".png")
            return p
        else:
            self.screenshot_path.mkdir(parents=True, exist_ok=True)
            ts = time.strftime("%Y%m%d-%H%M%S")
            return self.screenshot_path / f"wb-{ts}.png"


# --------------------------- Асинхронный синглтон ---------------------------
_agent_singleton_async: Optional[WebAgent] = None


async def get_agent_async(
    headless: bool = False,
    url: str = "https://www.wildberries.ru/",
    slow_mo_ms: int = 0,
    viewport: Optional[tuple[int, int]] = (1000, 1000),
    user_agent: Optional[str] = None,
    screenshot_path: Path = Path("web-tools/screenshots"),
) -> WebAgent:
    """Возвращает единый экземпляр агента (создаётся при первом вызове).

    Повторные вызовы возвращают уже созданный экземпляр, тем самым браузер/страница
    используются повторно в рамках процесса Python.
    """
    global _agent_singleton_async
    if _agent_singleton_async is None:
        _agent_singleton_async = await WebAgent.create(
            headless=headless,
            url=url,
            slow_mo_ms=slow_mo_ms,
            viewport=viewport,
            user_agent=user_agent,
            screenshot_path=screenshot_path,
        )
    return _agent_singleton_async


async def close_agent_async() -> None:
    """Явно закрыть singleton-агента и освободить ресурсы."""
    global _agent_singleton_async
    if _agent_singleton_async is not None:
        try:
            await _agent_singleton_async.close()
        finally:
            _agent_singleton_async = None


# Утилиты для удобства — фабрика-обёртки
async def init_session(
        headless: bool = False,
        url: str = "https://www.wildberries.ru/",
        slow_mo_ms: int = 0,
        viewport: Optional[tuple[int, int]] = (1000, 1000),
        user_agent: Optional[str] = None,
        screenshot_path: Path = Path("web-tools/screenshots"),
) -> WebAgent:

    agent = await get_agent_async(
        headless=headless, url=url, slow_mo_ms=slow_mo_ms, viewport=viewport, user_agent=user_agent,
        screenshot_path=screenshot_path
    )

    return agent


async def close_session() -> None:
    await close_agent_async()
