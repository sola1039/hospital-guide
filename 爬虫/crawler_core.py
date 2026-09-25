# 浏览器会话封装: 过瑞数WAF, 带重试的页面抓取
import time

from playwright.sync_api import sync_playwright

BASE = "https://sugh.szu.edu.cn"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
)


class SiteSession:
    def __init__(self) -> None:
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._ctx = self._browser.new_context(
            user_agent=UA,
            viewport={"width": 1366, "height": 900},
            locale="zh-CN",
        )
        self._page = self._ctx.new_page()
        self._warm = False

    def close(self) -> None:
        self._browser.close()
        self._pw.stop()

    def get_html(self, url: str, min_len: int = 3000) -> str:
        """抓取页面HTML, 过WAF后校验长度; 最多重试3次"""
        for attempt in range(3):
            try:
                self._page.goto(url, wait_until="domcontentloaded", timeout=45000)
                html = self._wait_content(min_len)
                if len(html) >= min_len:
                    self._warm = True
                    return html
            except Exception as e:
                if attempt == 2:
                    raise RuntimeError(f"抓取失败 {url}: {e}")
            time.sleep(2 + attempt * 2)
        raise RuntimeError(f"内容过短 {url}")

    def _wait_content(self, min_len: int) -> str:
        html = ""
        for _ in range(25):
            time.sleep(0.8)
            html = self._page.content()
            if len(html) >= min_len:
                return html
        return html
