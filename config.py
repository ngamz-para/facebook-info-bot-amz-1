import os

# Lấy token từ biến môi trường
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("❌ LỖI: Chưa thiết lập BOT_TOKEN!")

# Cấu hình cho Selenium
SELENIUM_CONFIG = {
    'headless': True,  # Chạy ẩn trên server
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'timeout': 30  # Thời gian chờ tối đa
}