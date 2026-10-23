import json
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

URL = "https://quotes.toscrape.com/scroll"
OUT_FILE = Path("out/result.json")
# Сколько ждать новую порцию цитат после прокрутки, мс
LOAD_TIMEOUT = 3000
# Картинки, шрифты и медиа скраперу не нужны — не загружаем их
BLOCKED_RESOURCES = {"image", "font", "media"}


def block_resources(route):
    if route.request.resource_type in BLOCKED_RESOURCES:
        route.abort()
    else:
        route.continue_()


def scroll_to_end(page):
    # Цитаты подгружаются JS при прокрутке: крутим вниз, пока появляются новые
    count = page.locator(".quote").count()
    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        try:
            page.wait_for_function(
                f"document.querySelectorAll('.quote').length > {count}",
                timeout=LOAD_TIMEOUT,
            )
        except PlaywrightTimeoutError:
            return
        count = page.locator(".quote").count()


def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.route("**/*", block_resources)
        page.goto(URL)
        page.wait_for_selector(".quote")
        scroll_to_end(page)

        # Все цитаты достаём одним вызовом в браузере
        quotes = page.locator(".quote").evaluate_all("""
            quotes => quotes.map(quote => ({
                text: quote.querySelector(".text").innerText,
                author: quote.querySelector(".author").innerText,
                tags: [...quote.querySelectorAll(".tag")].map(tag => tag.innerText),
            }))
        """)

        browser.close()
        return quotes


def main():
    quotes = scrape()
    if not quotes:
        raise SystemExit("Цитаты не найдены")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(quotes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Сохранено {len(quotes)} цитат в {OUT_FILE}")


if __name__ == "__main__":
    main()
