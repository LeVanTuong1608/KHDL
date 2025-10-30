import csv
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
# Thay thế webdriver tiêu chuẩn bằng undetected_chromedriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

def create_driver():
    """Tạo Chrome driver sử dụng undetected-chromedriver để tránh bị phát hiện"""
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--incognito')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Buộc thư viện tải driver cho phiên bản 128
    driver = uc.Chrome(options=chrome_options, version_main=128)
    return driver

def extract_property_info(driver, url):
    """Crawl thông tin chi tiết của một BĐS"""
    try:
        driver.get(url)
        time.sleep(3)  # Đợi trang load
        
        # Lấy HTML source
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Khởi tạo dictionary để lưu thông tin
        property_info = {
            'Link': url,
            'Ngày đăng': '',
            'Loại hình căn hộ': '',
            'Khoảng giá': '',
            'Diện tích': '',
            'Số phòng ngủ': '',
            'Số phòng tắm/vệ sinh': '',
            'Pháp lý': '',
            'Nội thất': ''
        }
        
        # 1. Crawl ngày đăng từ phần short-info
        try:
            short_info_items = soup.find_all('div', class_='re__pr-short-info-item js__pr-config-item')
            for item in short_info_items:
                title_span = item.find('span', class_='title')
                if title_span and 'Ngày đăng' in title_span.get_text():
                    value_span = item.find('span', class_='value')
                    if value_span:
                        property_info['Ngày đăng'] = value_span.get_text().strip()
                        break
        except Exception as e:
            print(f"Lỗi khi crawl ngày đăng: {e}")
        
        # 2. Crawl loại hình căn hộ
        try:
            # Tìm breadcrumb hoặc title chứa loại hình căn hộ
            breadcrumb = soup.find('div', class_='re__breadcrumb')
            if breadcrumb:
                # Lấy toàn bộ text từ breadcrumb và chỉ lấy phần cuối
                full_breadcrumb = breadcrumb.get_text().strip()
                # Tách theo dấu / và lấy phần cuối
                parts = full_breadcrumb.split('/')
                if len(parts) > 0:
                    property_info['Loại hình căn hộ'] = parts[-1].strip()
                else:
                    property_info['Loại hình căn hộ'] = full_breadcrumb
            else:
                # Fallback: tìm trong title
                title = soup.find('h1', class_='re__pr-title')
                if title:
                    property_info['Loại hình căn hộ'] = title.get_text().strip()
        except Exception as e:
            print(f"Lỗi khi crawl loại hình căn hộ: {e}")
        
        # 3. Crawl thông tin từ phần "Đặc điểm bất động sản"
        try:
            # Tìm trực tiếp các item đặc điểm
            spec_items = soup.find_all('div', class_='re__pr-specs-content-item')
            
            for item in spec_items:
                title_span = item.find('span', class_='re__pr-specs-content-item-title')
                value_span = item.find('span', class_='re__pr-specs-content-item-value')
                
                if title_span and value_span:
                    title_text = title_span.get_text().strip()
                    value_text = value_span.get_text().strip()
                    
                    # Map các trường thông tin
                    if 'Khoảng giá' in title_text:
                        property_info['Khoảng giá'] = value_text
                    elif 'Diện tích' in title_text:
                        property_info['Diện tích'] = value_text
                    elif 'Số phòng ngủ' in title_text:
                        property_info['Số phòng ngủ'] = value_text
                    elif 'Số phòng tắm' in title_text or 'Số phòng vệ sinh' in title_text:
                        property_info['Số phòng tắm/vệ sinh'] = value_text
                    elif 'Pháp lý' in title_text:
                        property_info['Pháp lý'] = value_text
                    elif 'Nội thất' in title_text:
                        property_info['Nội thất'] = value_text
                    
        except Exception as e:
            print(f"Lỗi khi crawl đặc điểm BĐS: {e}")
        
        return property_info
        
    except Exception as e:
        print(f"Lỗi khi crawl URL {url}: {e}")
        return None

def crawl_all_properties(csv_file='link_bds.csv', output_file='bds_crawl.csv', max_properties=None):
    """Crawl thông tin tất cả BĐS từ file CSV"""
    driver = create_driver()
    all_properties = []
    
    try:
        # Đọc file CSV chứa các link
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            links = list(reader)
        
        total_links = len(links)
        if max_properties:
            total_links = min(total_links, max_properties)
        
        print(f"Bắt đầu crawl {total_links} BĐS...")
        
        for i, row in enumerate(links[:total_links]):
            url = row['Link']
            print(f"Đang crawl {i+1}/{total_links}: {url}")
            
            property_info = extract_property_info(driver, url)
            if property_info:
                all_properties.append(property_info)
                print(f"✓ Thành công: {property_info.get('Khoảng giá', 'N/A')} - {property_info.get('Diện tích', 'N/A')}")
            else:
                print(f"✗ Thất bại: {url}")
            
            # Nghỉ giữa các request để tránh bị block
            time.sleep(2)
    
    except Exception as e:
        print(f"Lỗi trong quá trình crawl: {e}")
    
    finally:
        driver.quit()
    
    # Lưu kết quả vào file CSV
    if all_properties:
        df = pd.DataFrame(all_properties)
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\nĐã lưu {len(all_properties)} BĐS vào file {output_file}")
        
        # Hiển thị thống kê
        print("\nThống kê:")
        print(f"- Tổng số BĐS crawl được: {len(all_properties)}")
        print(f"- Có ngày đăng: {len([p for p in all_properties if p['Ngày đăng']])}")
        print(f"- Có giá: {len([p for p in all_properties if p['Khoảng giá']])}")
        print(f"- Có diện tích: {len([p for p in all_properties if p['Diện tích']])}")
    else:
        print("Không có dữ liệu nào được crawl!")

def main():
    """Hàm main để chạy chương trình"""
    print("=== CRAWL THÔNG TIN CHI TIẾT BĐS ===")
    
    # Crawl tất cả BĐS từ file CSV
    crawl_all_properties()

if __name__ == "__main__":
    main()
