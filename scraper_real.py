import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import re

class FacebookScraper:
    def __init__(self, headless=True):
        """Khởi tạo trình duyệt Chrome với cấu hình headless"""
        self.options = Options()
        
        if headless:
            self.options.add_argument("--headless=new")
        
        # Các cấu hình quan trọng cho server
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1920,1080")
        
        # Giả mạo user-agent
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Tắt thông báo Chrome
        self.options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        self.driver = None
        self.wait_timeout = 30
    
    def start_browser(self):
        """Khởi động trình duyệt"""
        try:
            self.driver = webdriver.Chrome(options=self.options)
            return True
        except WebDriverException as e:
            print(f"❌ Lỗi khởi động Chrome: {e}")
            return False
    
    def scrape_basic_info(self, username):
        """
        Thu thập thông tin CƠ BẢN từ trang cá nhân Facebook
        CHỈ HOẠT ĐỘNG VỚI TRANG CÔNG KHAI
        """
        if not self.driver:
            if not self.start_browser():
                return self._create_error_response("Không thể khởi động trình duyệt")
        
        try:
            # Mở trang Facebook (KHÔNG đăng nhập)
            url = f"https://www.facebook.com/{username}"
            print(f"🔍 Đang truy cập: {url}")
            
            self.driver.get(url)
            
            # Chờ trang tải - QUAN TRỌNG: Facebook có nhiều redirect
            time.sleep(5)
            
            # Kiểm tra xem có phải trang lỗi không
            if "trang này không khả dụng" in self.driver.page_source.lower():
                return self._create_error_response("Trang không tồn tại hoặc không công khai")
            
            # Lấy HTML để phân tích
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            
            # ========== TRÍCH XUẤT THÔNG TIN ==========
            info = {
                'success': True,
                'username': username,
                'url': url
            }
            
            # 1. Tìm tên (thẻ meta og:title)
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                info['name'] = meta_title.get('content', '').split('|')[0].strip()
            else:
                # Fallback: tìm trong title
                title_tag = soup.find('title')
                if title_tag:
                    info['name'] = title_tag.text.split('|')[0].strip()
            
            # 2. Tìm ảnh đại diện (meta og:image)
            meta_image = soup.find('meta', property='og:image')
            if meta_image:
                info['avatar_url'] = meta_image.get('content', '')
            
            # 3. Tìm UID từ source (nếu có)
            uid_match = re.search(r'"userID":"(\d+)"', page_source)
            if uid_match:
                info['uid'] = uid_match.group(1)
            else:
                info['uid'] = 'Không xác định'
            
            # 4. Tìm mô tả (meta og:description)
            meta_desc = soup.find('meta', property='og:description')
            if meta_desc:
                desc = meta_desc.get('content', '')
                info['bio'] = desc[:200] + '...' if len(desc) > 200 else desc
            
            # 5. Tìm thông tin cơ bản từ các div
            # LƯU Ý: Cấu trúc HTML của Facebook THAY ĐỔI THƯỜNG XUYÊN
            # Bạn cần tự cập nhật các selector này
            
            # Ví dụ tìm số người theo dõi (nếu là trang công khai)
            followers_text = ''
            for span in soup.find_all('span'):
                text = span.get_text()
                if 'người theo dõi' in text.lower() or 'followers' in text.lower():
                    followers_text = text
                    break
            
            info['followers'] = followers_text if followers_text else 'Không công khai'
            
            # 6. Xác định verified (tick xanh)
            verified = soup.find('i', {'aria-label': True})
            info['verified'] = 'Có' if verified and 'đã xác minh' in verified.get('aria-label', '').lower() else 'Không'
            
            # Thêm timestamp
            info['scraped_at'] = time.strftime("%d/%m/%Y %H:%M:%S")
            
            return info
            
        except TimeoutException:
            return self._create_error_response("Timeout khi tải trang")
        except Exception as e:
            print(f"❌ Lỗi không xác định: {e}")
            return self._create_error_response(f"Lỗi: {str(e)}")
    
    def scrape_via_graph_api(self, user_id):
        """
        Thử lấy thông tin qua Facebook Graph API
        YÊU CẦU: Access Token và quyền truy cập
        """
        # BẠN CẦN TỰ TẠO APP TRÊN DEVELOPERS.FACEBOOK.COM
        access_token = os.environ.get('FB_ACCESS_TOKEN', '')
        
        if not access_token:
            return {'error': 'Chưa cấu hình Facebook Access Token'}
        
        try:
            url = f"https://graph.facebook.com/v18.0/{user_id}"
            params = {
                'fields': 'id,name,first_name,last_name',
                'access_token': access_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'error' in data:
                return {'error': data['error']['message']}
            
            return {
                'success': True,
                'source': 'graph_api',
                'data': data
            }
            
        except Exception as e:
            return {'error': f"API Error: {str(e)}"}
    
    def _create_error_response(self, message):
        """Tạo response thông báo lỗi"""
        return {
            'success': False,
            'error': message,
            'timestamp': time.strftime("%d/%m/%Y %H:%M:%S")
        }
    
    def close(self):
        """Đóng trình duyệt"""
        if self.driver:
            self.driver.quit()
            self.driver = None

# Hàm wrapper đơn giản để bot.py gọi
def get_facebook_info_real(input_data):
    """
    Hàm chính để lấy thông tin Facebook
    Có thể nhận username hoặc UID
    """
    scraper = FacebookScraper(headless=True)
    
    try:
        # Xác định loại input
        if input_data.isdigit():
            # Nếu là số, thử dùng Graph API trước
            result = scraper.scrape_via_graph_api(input_data)
            if result.get('success'):
                return result
        
        # Mặc định dùng web scraping với username
        result = scraper.scrape_basic_info(input_data)
        return result
        
    finally:
        scraper.close()