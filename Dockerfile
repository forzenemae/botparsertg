FROM python:3.11-slim

# Устанавливаем системные зависимости вручную для Debian
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libx11-6 \
    libxext6 \
    libxfixes3 \
    libexpat1 \
    libglib2.0-0 \
    libgobject-2.0-0 \
    libsm6 \
    libxrender1 \
    libfontconfig1 \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

# Копируем проект
WORKDIR /app
COPY . .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем Playwright и браузеры (без install-deps, так как зависимости уже установлены)
RUN pip install playwright
RUN playwright install chromium

# Запускаем бота
CMD ["python", "bot.py"]
