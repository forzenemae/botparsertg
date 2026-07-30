import requests
import time
import random
from bs4 import BeautifulSoup

# ============================================================
# НАСТРОЙКА ПРОКСИ (из переменных окружения)
# ============================================================
import os

# Читаем настройки прокси из переменных окружения
PROXY_HOST = os.getenv("PROXY_HOST", "46.8.56.87")  # Например: "45.123.45.67"
PROXY_PORT = os.getenv("PROXY_PORT", "5501")  # Например: "1080"
PROXY_USER = os.getenv("PROXY_USER", "6NeZMV")  # Логин от прокси
PROXY_PASS = os.getenv("PROXY_PASS", "iSxcP9mEj")  # Пароль от прокси
PROXY_TYPE = os.getenv("PROXY_TYPE", "socks5")  # socks5 или http

# Собираем прокси-строку
def get_proxy_dict():
    """Возвращает словарь с прокси для requests"""
    if PROXY_HOST and PROXY_PORT:
        if PROXY_USER and PROXY_PASS:
            proxy_url = f"{PROXY_TYPE}://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
        else:
            proxy_url = f"{PROXY_TYPE}://{PROXY_HOST}:{PROXY_PORT}"
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    return None

# ============================================================
# ОСНОВНАЯ ФУНКЦИЯ ПАРСИНГА
# ============================================================
def fetch_ads_with_check(url: str, check_words: list, send_callback=None) -> list[dict]:
    """
    Парсит объявления с Avito через requests + BeautifulSoup
    Поддерживает SOCKS5 и HTTP прокси
    Отправляет найденные объявления через callback
    """
    found_ads = []
    
    try:
        # Заголовки для имитации реального пользователя
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Получаем прокси
        proxies = get_proxy_dict()
        if proxies:
            print(f"🌐 Использую прокси: {PROXY_TYPE}://{PROXY_HOST}:{PROXY_PORT}")
        else:
            print("🌐 Без прокси (прямое подключение)")
        
        print(f"🌐 Открываю страницу...")
        
        # Случайная задержка перед запросом (3-7 секунд)
        delay = random.randint(3, 7)
        print(f"   ⏳ Задержка {delay} сек...")
        time.sleep(delay)
        
        # Выполняем запрос
        response = requests.get(
            url,
            headers=headers,
            proxies=proxies,
            timeout=30
        )
        
        # Обработка ошибок
        if response.status_code == 429:
            print("⚠️ Слишком много запросов (429). Жду 120 секунд...")
            time.sleep(120)
            return fetch_ads_with_check(url, check_words, send_callback)  # Повторяем
        
        if response.status_code == 403:
            print("⚠️ Доступ запрещён (403). Меняем IP или ждём.")
            time.sleep(180)
            return []
        
        if response.status_code != 200:
            print(f"⚠️ Ошибка: статус {response.status_code}")
            return []
        
        # Проверяем на капчу
        if "captcha" in response.text.lower() or "проверка" in response.text.lower():
            print("⚠️ Обнаружена капча! Страница заблокирована.")
            return []
        
        print(f"✅ Страница загружена, размер: {len(response.text)} символов")
        
        # Парсим HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем объявления
        items = soup.find_all('div', {'data-marker': 'item'})
        
        # Если не нашли, пробуем альтернативный селектор
        if not items:
            items = soup.find_all('div', class_='iva-item-content')
        
        print(f"📦 Найдено объявлений: {len(items)}")
        
        # Обрабатываем каждое объявление
        for i, item in enumerate(items):
            try:
                # Получаем заголовок
                title_elem = item.find('a', {'data-marker': 'item-title'})
                if not title_elem:
                    continue
                title = title_elem.text.strip()
                
                # Получаем ссылку
                link = title_elem.get('href')
                if link:
                    if link.startswith('/'):
                        full_link = f"https://www.avito.ru{link}"
                    else:
                        full_link = link
                else:
                    continue
                
                # Получаем описание
                desc_elem = item.find('div', {'data-marker': 'item-description'})
                description = desc_elem.text.strip() if desc_elem else ""
                
                # Получаем цену
                price_elem = item.find('span', {'data-marker': 'item-price'})
                price = price_elem.text.strip() if price_elem else "Цена не указана"
                
                # Проверяем наличие чек-слов
                text_to_check = (title + " " + description).lower()
                has_check = any(word.lower() in text_to_check for word in check_words)
                
                if has_check:
                    ad_data = {
                        'url': full_link,
                        'title': title[:100],
                        'description': description[:200] if description else "Описание не указано",
                        'price': price
                    }
                    
                    found_ads.append(ad_data)
                    print(f"✅ Найдено объявление с чеком: {title[:30]}...")
                    
                    # Отправляем через callback
                    if send_callback:
                        print(f"📤 ВЫЗЫВАЮ ОТПРАВКУ: {title[:30]}...")
                        send_callback(ad_data)
                        
            except Exception as e:
                print(f"⚠️ Ошибка обработки объявления {i}: {str(e)[:50]}")
                continue
        
        print(f"\n📊 ИТОГО: найдено с чеком: {len(found_ads)}")
        return found_ads
        
    except requests.exceptions.ProxyError as e:
        print(f"❌ Ошибка прокси: {e}")
        print("   Проверьте настройки прокси в переменных окружения")
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return []
    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")
        return []
