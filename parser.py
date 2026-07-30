import asyncio
import random
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def fetch_ads_with_check(url: str, check_words: list, send_callback=None) -> list[dict]:
    """Парсит объявления с Avito с использованием stealth-режима"""
    browser = None
    found_ads = []
    
    try:
        async with async_playwright() as p:
            # Запускаем браузер в headless-режиме
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-gpu'
                ]
            )
            
            # Создаём контекст с реалистичными параметрами
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale='ru-RU',
                timezone_id='Europe/Moscow',
                permissions=['geolocation'],
                device_scale_factor=1,
                has_touch=False,
                extra_http_headers={
                    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            # Создаём страницу
            page = await context.new_page()
            
            # Применяем stealth-режим к странице
            await stealth_async(page)
            
            # Дополнительная маскировка
            await page.add_init_script("""
                // Скрываем webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Скрываем chrome
                window.chrome = {
                    runtime: {}
                };
                
                // Скрываем plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Скрываем languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['ru-RU', 'ru', 'en-US', 'en']
                });
            """)

            print(f"🌐 Открываю страницу с stealth-режимом...")
            
            # Переходим на страницу
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Случайные задержки для имитации человека
            await page.wait_for_timeout(random.randint(3000, 6000))
            
            # Прокручиваем страницу как человек
            for _ in range(random.randint(2, 4)):
                await page.evaluate(f"window.scrollBy(0, {random.randint(300, 700)})")
                await page.wait_for_timeout(random.randint(500, 1500))
            
            # Ждём появления объявлений
            try:
                await page.wait_for_selector("[data-marker='item']", timeout=30000)
                print("✅ Найдены объявления")
            except Exception as e:
                print(f"⚠️ Объявления не найдены: {e}")
                # Проверяем, не капча ли это
                page_content = await page.content()
                if "captcha" in page_content.lower() or "проверка" in page_content:
                    print("⚠️ Обнаружена капча! Нужно ручное вмешательство или смена прокси.")
                return []
            
            # Получаем все объявления
            items = await page.locator("[data-marker='item']").all()
            print(f"📦 Найдено объявлений: {len(items)}")
            
            for i, item in enumerate(items):
                try:
                    # Получаем заголовок
                    title_element = item.locator("[data-marker='item-title']")
                    title = await title_element.text_content() or ""
                    
                    if not title:
                        continue
                    
                    # Получаем ссылку
                    link = await title_element.get_attribute("href")
                    if not link:
                        continue
                    full_link = f"https://www.avito.ru{link}" if link.startswith('/') else link
                    
                    # Получаем описание
                    description = ""
                    try:
                        desc_element = item.locator("[data-marker='item-description']")
                        description = await desc_element.text_content() or ""
                    except:
                        pass
                    
                    if not description:
                        full_text = await item.text_content() or ""
                        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                        if len(lines) > 2:
                            description = ' '.join(lines[2:min(5, len(lines))])
                    
                    # Проверяем наличие чек-слов
                    text_to_check = (title + " " + description).lower()
                    has_check = any(word.lower() in text_to_check for word in check_words)
                    
                    if has_check:
                        # Получаем цену
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
                    print(f"⚠️ Ошибка обработки объявления {i}: {str(e)[:50]}")
                    continue
            
            print(f"\n📊 ИТОГО: найдено с чеком: {len(found_ads)}")
            
            # Даём время на отправку
            await asyncio.sleep(1)
            
            return found_ads

    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")
        return []
