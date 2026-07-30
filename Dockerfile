FROM python:3.11-slim

# Устанавливаем системные зависимости для Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Копируем проект
WORKDIR /app
COPY . .

# Устанавливаем Python зависимости
RUN pip install -r requirements.txt

# Устанавливаем Playwright и браузеры
RUN pip install playwright
RUN playwright install chromium
RUN playwright install-deps

# Запускаем бота
CMD ["python", "bot.py"]
