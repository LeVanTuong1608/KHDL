import csv
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin
# Thay thế webdriver tiêu chuẩn bằng undetected_chromedriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    
    # === THÊM DÒNG NÀY VÀO ===
    # Buộc thư viện tải driver cho phiên bản 128
    driver = uc.Chrome(options=chrome_options, version_main=128) 
    
    return driver

def crawl_bds_links(base_url, max_pages=10):
    """
    Crawl links từ batdongsan.com.vn sử dụng undetected_chromedriver
    
    Args:
        base_url: URL gốc
        max_pages: Số trang tối đa để crawl
    """
    all_links = []
    driver = None
    
    try:
        print("🚀 Khởi tạo undetected-chromedriver...")
        driver = create_driver()
        
        for page in range(1, max_pages + 1):
            url = f"{base_url}/p{page}" if page > 1 else base_url
            
            print(f"📄 Đang crawl trang {page}: {url}")
            
            try:
                driver.get(url)
                
                # Chờ cho trang vượt qua kiểm tra của Cloudflare và load nội dung chính
                # Tăng thời gian chờ và chờ một element cụ thể của trang sản phẩm
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.re__srp-list"))
                )
                
                # Chờ thêm một chút để đảm bảo tất cả JavaScript đã chạy
                time.sleep(random.uniform(2, 4))
                
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                title = soup.find('title').get_text(strip=True) if soup.find('title') else "Không có title"
                print(f"🔍 Trang {page} title: {title[:70]}...")

                if "Just a moment" in title:
                    print(f"❌ Vẫn bị Cloudflare chặn ở trang {page}. Thử lại hoặc dừng lại.")
                    continue

                product_links = soup.select('a.js__product-link-for-product-id')
                
                if not product_links:
                    print(f"⚠️ Không tìm thấy link sản phẩm nào ở trang {page}.")
                    continue
                
                page_links = []
                for link in product_links:
                    href = link.get('href')
                    if href:
                        # urljoin đảm bảo link được tạo chính xác
                        full_url = urljoin('https://batdongsan.com.vn', href)
                        page_links.append(full_url)
                
                all_links.extend(page_links)
                print(f"✅ Tìm thấy {len(page_links)} links ở trang {page}")
                
                # Delay ngẫu nhiên dài hơn một chút để hành xử giống người hơn
                delay = random.uniform(3, 6)
                print(f"😴 Tạm nghỉ {delay:.2f} giây...")
                time.sleep(delay)
                
            except Exception as e:
                print(f"❌ Lỗi khi crawl trang {page}: {e}")
                # Chụp ảnh màn hình để debug nếu cần
                driver.save_screenshot(f'error_page_{page}.png')
                print(f"📸 Đã lưu ảnh màn hình lỗi vào 'error_page_{page}.png'")
                continue
                
    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng: {e}")
        
    finally:
        if driver:
            driver.quit()
            print("🔚 Đã đóng Chrome driver")
    
    return all_links

def save_links_to_csv(links, filename='link_bds.csv'):
    """Lưu danh sách links vào file CSV"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['STT', 'Link'])
            
            for i, link in enumerate(links, 1):
                writer.writerow([i, link])
        
        print(f"💾 Đã lưu {len(links)} links vào file {filename}")
        
    except Exception as e:
        print(f"❌ Lỗi khi lưu file CSV: {e}")

def main():
    base_url = "https://batdongsan.com.vn/nha-dat-ban-ha-noi"
    
    print("🏠 Bắt đầu crawl links từ batdongsan.com.vn")
    print("=" * 50)
    
    links = crawl_bds_links(base_url, max_pages=100)
    
    if links:
        unique_links = sorted(list(set(links)))
        print(f"\n📊 Tổng cộng: {len(links)} links")
        print(f"📊 Sau khi loại bỏ duplicate: {len(unique_links)} links")
        
        save_links_to_csv(unique_links, 'link_bds.csv')
        
        print("\n🔗 Một vài link mẫu:")
        for i, link in enumerate(unique_links[:5], 1):
            print(f"{i}. {link}")
            
    else:
        print("❌ Không tìm thấy link nào!")

if __name__ == "__main__":
    main()