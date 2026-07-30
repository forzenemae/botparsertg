import requests
import time
import random
from bs4 import BeautifulSoup

def fetch_ads_with_check(url: str, check_words: list, send_callback=None) -> list[dict]:
    found_ads = []

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

        print(f"🌐 Открываю страницу через requests...")

        # Задержка перед запросом
        time.sleep(random.randint(3, 7))

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 429:
            print("⚠️ Слишком много запросов (429). Жду 60 секунд...")
            time.sleep(60)
            return fetch_ads_with_check(url, check_words, send_callback)  # retry

        if response.status_code == 403:
            print("⚠️ Доступ запрещён (403). Меняем IP или ждём.")
            time.sleep(120)
            return []

        if response.status_code != 200:
            print(f"⚠️ Ошибка: статус {response.status_code}")
            return []

        # Проверяем на капчу
        if "captcha" in response.text.lower() or "проверка" in response.text.lower():
            print("⚠️ Обнаружена капча! Страница заблокирована.")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', {'data-marker': 'item'})

        if not items:
            items = soup.find_all('div', class_='iva-item-content')

        print(f"📦 Найдено объявлений: {len(items)}")

        for i, item in enumerate(items):
            try:
                title_elem = item.find('a', {'data-marker': 'item-title'})
                if not title_elem:
                    continue
                title = title_elem.text.strip()

                link = title_elem.get('href')
                if link:
                    full_link = f"https://www.avito.ru{link}" if link.startswith('/') else link
                else:
                    continue

                desc_elem = item.find('div', {'data-marker': 'item-description'})
                description = desc_elem.text.strip() if desc_elem else ""

                price_elem = item.find('span', {'data-marker': 'item-price'})
                price = price_elem.text.strip() if price_elem else "Цена не указана"

                text_to_check = (title + " " + description).lower()
                has_check = any(word.lower() in text_to_check for word in check_words)

                if has_check:
                    ad_data = {
                        'url': full_link,
                        'title': title[:100],
                        'description': description[:200],
                        'price': price
                    }

                    found_ads.append(ad_data)
                    print(f"✅ Найдено объявление с чеком: {title[:30]}...")

                    if send_callback:
                        send_callback(ad_data)

            except Exception as e:
                print(f"⚠️ Ошибка обработки объявления {i}: {str(e)[:50]}")
                continue

        print(f"\n📊 ИТОГО: найдено с чеком: {len(found_ads)}")
        return found_ads

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return []
    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")
        return []
