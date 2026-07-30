FROM python:3.11-slim

# Устанавливаем системные зависимости для Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Playwright
RUN pip install playwright

# Устанавливаем браузеры и зависимости
RUN playwright install chromium
RUN playwright install-deps

# Копируем проект
WORKDIR /app
COPY . .

# Устанавливаем Python зависимости
RUN pip install -r requirements.txt

# Запускаем бота
CMD ["python", "bot.py"]
