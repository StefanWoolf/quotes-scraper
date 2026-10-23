import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://quotes.toscrape.com/scroll"
OUT_FILE = Path("out/result.json")


def scroll_to_end(page):
    # Цитаты подгружаются JS при прокрутке: крутим вниз, пока их число растёт
    count = 0
    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        new_count = page.locator(".quote").count()
        if new_count == count:
            return
        count = new_count


def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL)
        page.wait_for_selector(".quote")
        scroll_to_end(page)

        quotes = []
        for quote in page.locator(".quote").all():
            quotes.append({
                "text": quote.locator(".text").inner_text(),
                "author": quote.locator(".author").inner_text(),
                "tags": quote.locator(".tag").all_inner_texts(),
            })

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
