import time
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

class FacebookScraperImproved:
    def __init__(self):
        # Headers giả mạo trình duyệt thật
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_fast(self, username):
        """
        Phiên bản cải tiến: NHANH HƠN và chính xác hơn.
        Dùng requests + BeautifulSoup thay vì Selenium khi có thể.
        """
        url = f"https://www.facebook.com/{username}"
        print(f"🚀 Đang thu thập nhanh: {username}")
        
        try:
            # 1. LẤY HTML BẰNG REQUESTS (SIÊU NHANH)
            start_time = time.time()
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            html_content = response.text
            
            get_time = time.time() - start_time
            print(f"⏱️  Tải HTML xong trong {get_time:.2f}s")
            
            # 2. PHÂN TÍCH VỚI BEAUTIFULSOUP
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 3. LẤY THÔNG TIN CƠ BẢN TỪ META TAGS
            info = self._extract_from_meta(soup, username, url)
            
            # 4. TÌM THÔNG TIN CHI TIẾT HƠN TRONG HTML
            self._extract_detailed_info(soup, info)
            
            # 5. ƯỚC LƯỢNG NGÀY TẠO TÀI KHOẢN (Nếu có UID)
            if info.get('uid') and info['uid'].isdigit():
                info['estimated_join_date'] = self._estimate_join_date(info['uid'])
            
            info['scraped_in'] = f"{get_time:.2f}s"
            info['success'] = True
            return info
            
        except requests.exceptions.Timeout:
            return self._error_response("Timeout: Facebook phản hồi quá chậm")
        except requests.exceptions.RequestException as e:
            return self._error_response(f"Lỗi kết nối: {str(e)}")
        except Exception as e:
            return self._error_response(f"Lỗi xử lý: {str(e)}")
    
    def _extract_from_meta(self, soup, username, url):
        """Trích xuất thông tin từ thẻ meta (nhanh và ổn định nhất)"""
        info = {
            'username': username,
            'url': url,
            'name': 'Không xác định',
            'avatar_url': '',
            'uid': 'Không xác định',
            'bio': '',
            'verified': 'Không'  # Mặc định là Không
        }
        
        # Tìm tên từ og:title
        meta_title = soup.find('meta', property='og:title')
        if meta_title:
            full_title = meta_title.get('content', '')
            # Tách tên thật từ title (loại bỏ " | Facebook")
            info['name'] = full_title.split('|')[0].strip()
        
        # Tìm ảnh đại diện từ og:image
        meta_image = soup.find('meta', property='og:image')
        if meta_image:
            info['avatar_url'] = meta_image.get('content', '')
        
        # Tìm UID từ nhiều nguồn khác nhau trong HTML
        uid = self._find_uid_in_html(str(soup))
        if uid:
            info['uid'] = uid
        
        # Tìm mô tả bio
        meta_desc = soup.find('meta', property='og:description')
        if meta_desc:
            info['bio'] = meta_desc.get('content', '')[:150]
        
        return info
    
    def _find_uid_in_html(self, html):
        """Tìm UID bằng nhiều regex pattern (tăng độ chính xác)"""
        patterns = [
            r'"userID":"(\d+)"',           # Pattern cũ
            r'"actor_id":(\d+)',           # Pattern mới
            r'profile_id=(\d+)',           # Trong URL
            r'/(\d+)/?$',                  # UID trong đường dẫn
            r'content="fb://profile/(\d+)"' # Trong meta
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None
    
    def _extract_detailed_info(self, soup, info):
        """Trích xuất thông tin chi tiết hơn từ HTML"""
        
        # CẢI TIẾN: Tìm tick xanh (verified) bằng nhiều cách
        verified = False
        
        # Cách 1: Tìm biểu tượng tick xanh qua SVG path
        svg_tags = soup.find_all('svg')
        for svg in svg_tags:
            if svg.find('path', {'d': True}):
                # Path data của tick xanh thường có chữ "M18" hoặc phức tạp
                path_data = str(svg.find('path'))
                if 'M18' in path_data and ('9.5' in path_data or '12' in path_data):
                    verified = True
                    break
        
        # Cách 2: Tìm trong alt text của ảnh
        img_tags = soup.find_all('img', alt=True)
        for img in img_tags:
            alt_text = img.get('alt', '').lower()
            if 'verified' in alt_text or 'đã xác minh' in alt_text:
                verified = True
                break
        
        info['verified'] = 'Có ✓' if verified else 'Không ✗'
        
        # Tìm số người theo dõi (followers)
        followers_text = 'Không công khai'
        
        # Tìm các span có text liên quan đến followers
        all_text = soup.get_text()
        followers_patterns = [
            r'(\d+[\.,]?\d*[KkM]?)\s*(người theo dõi|followers)',
            r'(\d+[\.,]?\d*[KkM]?)\s*(lượt theo dõi)',
            r'Followers:\s*(\d+[\.,]?\d*[KkM]?)'
        ]
        
        for pattern in followers_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                followers_text = f"{match.group(1)} người theo dõi"
                break
        
        info['followers'] = followers_text
    
    def _estimate_join_date(self, uid):
        """
        ƯỚC LƯỢNG ngày tạo tài khoản dựa trên UID.
        Đây là phương pháp gần đúng dựa trên quan sát.
        """
        try:
            uid_num = int(uid)
            
            # Facebook UID tăng dần theo thời gian
            # UID 4 (Mark Zuckerberg) ~ 2004
            # UID 100000xxx ~ 2008
            # Đây là công thức ƯỚC LƯỢNG, không chính xác 100%
            
            base_year = 2004
            base_uid = 4
            
            if uid_num <= base_uid:
                return "Khoảng 2004"
            
            # Tính năm ước lượng (mỗi 50 triệu UID ~ 1 năm)
            years_since_base = (uid_num - base_uid) / 50000000
            estimated_year = base_year + int(years_since_base)
            
            # Giới hạn năm trong khoảng hợp lý
            estimated_year = max(2004, min(estimated_year, datetime.now().year))
            
            return f"Khoảng năm {estimated_year}"
            
        except:
            return "Không thể ước lượng"
    
    def _error_response(self, message):
        return {
            'success': False,
            'error': message,
            'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }

# Hàm wrapper để bot.py gọi
def get_facebook_info_improved(username):
    scraper = FacebookScraperImproved()
    return scraper.scrape_fast(username)
