import time
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

class FacebookScraperImproved:
    def __init__(self):
        # CẢI TIẾN QUAN TRỌNG: Thêm cookie và headers giống trình duyệt thật hơn
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        # Khởi tạo session với cookie cơ bản
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        # Thêm một số cookie phổ biến để trông giống lượt truy cập đầu tiên
        self.session.cookies.update({
            'locale': 'en_US',
            'sb': 'placeholder_cookie_for_initial_request',
        })
    
    def scrape_fast(self, username):
        """
        Phiên bản đã sửa: Cố gắng vượt qua chặn cơ bản của Facebook.
        """
        # CẢI TIẾN: Thử với URL rút gọn 'fb.com' và đường dẫn 'profile' trước
        urls_to_try = [
            f"https://www.facebook.com/{username}",
            f"https://fb.com/{username}",
            f"https://www.facebook.com/profile.php?id={username}" if username.isdigit() else None,
        ]
        
        for url in filter(None, urls_to_try):
            print(f"🔍 Đang thử với URL: {url}")
            result = self._try_scrape_url(url, username)
            if result.get('success'):
                return result
            # Nếu thất bại và bị chuyển hướng đến login, dừng thử các URL khác
            if "login" in result.get('error', ''):
                return self._error_response(f"Truy cập bị chặn. Facebook yêu cầu đăng nhập để xem trang này.")
        
        # Nếu tất cả đều thất bại
        return self._error_response("Không thể truy cập trang. Có thể trang không tồn tại hoặc yêu cầu đăng nhập.")
    
    def _try_scrape_url(self, url, username):
        """Thử thu thập từ một URL cụ thể."""
        try:
            start_time = time.time()
            # QUAN TRỌNG: Tắt tự động redirect để kiểm tra nếu Facebook chuyển hướng sang login
            response = self.session.get(url, timeout=15, allow_redirects=False)
            get_time = time.time() - start_time
            
            # Kiểm tra mã trạng thái HTTP
            if response.status_code == 302 or response.status_code == 301:
                location = response.headers.get('Location', '')
                if 'login' in location:
                    # Bị chuyển hướng đến trang đăng nhập -> bị chặn
                    return self._error_response(f"Bị chuyển hướng tới login ({location})")
                else:
                    # Chuyển hướng khác, có thể thử theo dõi
                    pass
            elif response.status_code != 200:
                return self._error_response(f"Mã lỗi HTTP: {response.status_code}")
            
            # Nếu không bị chặn, tiếp tục phân tích HTML
            html_content = response.text
            
            # KIỂM TRA QUAN TRỌNG: Xem HTML có chứa từ khóa "login" không
            if 'login' in html_content.lower() and 'password' in html_content.lower():
                return self._error_response("Trang trả về là trang đăng nhập (bị chặn).")
            
            print(f"✅ Tải HTML thành công từ {url} trong {get_time:.2f}s")
            soup = BeautifulSoup(html_content, 'lxml')
            
            info = self._extract_from_meta(soup, username, url)
            self._extract_detailed_info(soup, info)
            
            if info.get('uid') and info['uid'].isdigit():
                info['estimated_join_date'] = self._estimate_join_date(info['uid'])
            
            info.update({
                'scraped_in': f"{get_time:.2f}s",
                'success': True,
                'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            })
            return info
            
        except requests.exceptions.Timeout:
            return self._error_response("Timeout: Facebook phản hồi quá chậm")
        except requests.exceptions.RequestException as e:
            # CẢI TIẾN: Phân tích lỗi chi tiết hơn
            error_msg = str(e)
            if '400' in error_msg or '403' in error_msg:
                return self._error_response(f"Truy cập bị từ chối (Lỗi {error_msg}). Facebook có thể đã chặn IP của server.")
            return self._error_response(f"Lỗi kết nối: {error_msg}")
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
        """Tạo response thông báo lỗi"""
        return {
            'success': False,
            'error': message,
            'timestamp': datetime.now().strftime("%d/%m/Y %H:%M:%S")
        }

# Hàm wrapper để bot.py gọi
def get_facebook_info_improved(username):
    scraper = FacebookScraperImproved()
    return scraper.scrape_fast(username)
