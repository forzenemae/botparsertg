import asyncio
import random
from playwright.async_api import async_playwright

async def fetch_ads_with_check(url: str, check_words: list, send_callback=None) -> list[dict]:
    """Парсит объявления и сразу отправляет через callback"""
    browser = None
    found_ads = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,  # <-- ИСПРАВЛЕНО
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale='ru-RU',
                timezone_id='Europe/Moscow'
            )
            
            page = await context.new_page()
            
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            print(f"🌐 Открываю страницу...")
            
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(random.randint(2000, 4000))
            await page.evaluate("window.scrollBy(0, 500)")
            await page.wait_for_timeout(random.randint(1000, 2000))
            
            try:
                await page.wait_for_selector("[data-marker='item']", timeout=30000)
                print("✅ Найдены объявления")
            except:
                print("⚠️ Объявления не найдены")
                return []
            
            items = await page.locator("[data-marker='item']").all()
            print(f"📦 Найдено объявлений: {len(items)}")
            
            for i, item in enumerate(items):
                try:
                    # Получаем заголовок
                    try:
                        title_element = item.locator("[data-marker='item-title']")
                        title = await title_element.text_content() or ""
                    except:
                        title_element = item.locator("h3")
                        title = await title_element.text_content() or ""
                    
                    if not title:
                        continue
                    
                    # Получаем ссылку
                    try:
                        link = await title_element.get_attribute("href")
                        if not link:
                            continue
                        full_link = f"https://www.avito.ru{link}" if link.startswith('/') else link
                    except:
                        continue
                    
                    # Получаем весь текст объявления
                    full_text = await item.text_content() or ""
                    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                    
                    # Ищем описание
                    description = ""
                    try:
                        desc_element = item.locator("[data-marker='item-description']")
                        description = await desc_element.text_content() or ""
                    except:
                        pass
                    
                    if not description and len(lines) > 2:
                        description = ' '.join(lines[2:min(5, len(lines))])
                    
                    # Проверяем наличие чек-слов
                    text_to_check = (title + " " + description + " " + full_text).lower()
                    has_check = any(word.lower() in text_to_check for word in check_words)
                    
                    if has_check:
                        try:
                            price_element = item.locator("[data-marker='item-price']")
                            price_text = await price_element.text_content() or "Цена не указана"
                        except:
                            price_text = "Цена не указана"
                        
                        ad_data = {
                            'url': full_link,
                            'title': title.strip()[:100],
                            'description': description.strip()[:200] if description else "Описание не указано",
                            'price': price_text.strip()
                        }
                        
                        found_ads.append(ad_data)
                        print(f"✅ Найдено объявление с чеком: {title[:30]}...")
                        
                        if send_callback:
                            print(f"📤 ВЫЗЫВАЮ ОТПРАВКУ: {title[:30]}...")
                            send_callback(ad_data)
                        
                except Exception as e:
                    continue
            
            print(f"\n📊 ИТОГО: найдено с чеком: {len(found_ads)}")
            
            try:
                await browser.close()
            except:
                pass
            
            return found_ads

    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")
        try:
            if browser:
                await browser.close()
        except:
            pass
        return []
