# FROM python:3.11-slim

# # System dependencies for Playwright headless browser
# RUN apt-get update && apt-get install -y \
#     wget gnupg libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
#     libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
#     libpangocairo-1.0-0 libgtk-3-0 libxss1 libxtst6 fonts-liberation \
#     && apt-get clean

# # Create app directory
# WORKDIR /app

# # Copy code
# COPY app /app

# # Install Python deps
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Install Playwright and its browser binaries
# RUN playwright install --with-deps

# # Expose port
# EXPOSE 5000

# CMD ["python", "main.py"]
FROM python:3.12-slim

# Install only essential deps for Chromium
RUN apt-get update && apt-get install -y \
    wget libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    libpangocairo-1.0-0 libgtk-3-0 libxss1 libxtst6 fonts-liberation \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install ONLY Chromium (not Firefox/WebKit)
RUN playwright install chromium

EXPOSE 5000
CMD ["python", "main.py"]