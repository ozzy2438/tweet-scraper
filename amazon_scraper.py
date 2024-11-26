from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
import csv
import logging
import random
import pandas as pd
from fake_useragent import UserAgent
import sys
import platform
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('amazon_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AmazonScraper:
    def __init__(self):
        self.driver = None
        self.base_url = "https://www.amazon.com"
        self.products = []
        self.max_retries = 3
        self.timeout = 10

    def get_chrome_version(self):
        try:
            if platform.system() == "Darwin":  # macOS
                process = subprocess.Popen(
                    ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                version = process.communicate()[0].decode('UTF-8').replace('Google Chrome ', '').strip()
                return version
            return None
        except:
            return None

    def setup_driver(self):
        try:
            logger.info("Setting up Chrome driver...")
            options = webdriver.ChromeOptions()
            
            # Anti-detection measures
            ua = UserAgent()
            options.add_argument(f'user-agent={ua.random}')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--start-maximized')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Additional preferences
            prefs = {
                "profile.default_content_setting_values.notifications": 2,
                "profile.managed_default_content_settings.images": 1,
                "profile.default_content_setting_values.cookies": 1
            }
            options.add_experimental_option("prefs", prefs)

            # Get Chrome version
            chrome_version = self.get_chrome_version()
            if chrome_version:
                logger.info(f"Detected Chrome version: {chrome_version}")
            
            try:
                service = Service()
                self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                logger.error(f"Failed to create driver with default service: {str(e)}")
                # Try alternative method
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": ua.random})
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Chrome driver successfully initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to setup driver: {str(e)}")
            return False

    def random_sleep(self, min_seconds=2, max_seconds=5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def wait_for_element(self, by, selector, timeout=None):
        if timeout is None:
            timeout = self.timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            return None

    def extract_price(self, product_element):
        try:
            price_whole = product_element.find_element(By.CSS_SELECTOR, 'span.a-price-whole').text
            price_fraction = product_element.find_element(By.CSS_SELECTOR, 'span.a-price-fraction').text
            return float(f"{price_whole.replace(',', '')}.{price_fraction}")
        except:
            try:
                price = product_element.find_element(By.CSS_SELECTOR, 'span.a-price').get_attribute('data-a-price')
                return float(price) / 100 if price else None
            except:
                return None

    def extract_product_info(self, product_element):
        try:
            info = {}
            
            # Title
            title_element = product_element.find_element(By.CSS_SELECTOR, 'h2 span.a-text-normal')
            info['title'] = title_element.text.strip()
            
            # Price
            info['price'] = self.extract_price(product_element)
            
            # Rating
            try:
                rating_element = product_element.find_element(By.CSS_SELECTOR, 'span.a-icon-alt')
                info['rating'] = float(rating_element.get_attribute('innerHTML').split(' ')[0])
            except:
                info['rating'] = None
            
            # Number of reviews
            try:
                reviews_element = product_element.find_element(By.CSS_SELECTOR, 'span.a-size-base.s-underline-text')
                info['reviews'] = int(reviews_element.text.replace(',', ''))
            except:
                info['reviews'] = 0
            
            # Product URL
            try:
                url_element = product_element.find_element(By.CSS_SELECTOR, 'h2 a')
                info['url'] = self.base_url + url_element.get_attribute('href')
            except:
                info['url'] = None
            
            # Availability
            try:
                availability = product_element.find_element(By.CSS_SELECTOR, 'span.a-color-price').text
                info['availability'] = availability.strip()
            except:
                info['availability'] = "In Stock"
            
            info['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return info
            
        except Exception as e:
            logger.error(f"Error extracting product info: {str(e)}")
            return None

    def search_products(self, query):
        try:
            search_url = f"{self.base_url}/s?k={query.replace(' ', '+')}&ref=nb_sb_noss"
            self.driver.get(search_url)
            self.random_sleep(3, 6)
            
            page_num = 1
            while page_num <= 5:  # Limit to 5 pages to avoid blocking
                logger.info(f"Scraping page {page_num}")
                
                # Wait for products to load
                products_selector = "div.s-result-item[data-component-type='s-search-result']"
                products = self.wait_for_element(By.CSS_SELECTOR, products_selector, timeout=15)
                
                if not products:
                    logger.warning("No products found on page")
                    break
                
                # Extract product information
                product_elements = self.driver.find_elements(By.CSS_SELECTOR, products_selector)
                
                for product in product_elements:
                    product_info = self.extract_product_info(product)
                    if product_info:
                        self.products.append(product_info)
                
                # Random delay between pages
                self.random_sleep(4, 7)
                
                # Try to go to next page
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, 'a.s-pagination-next:not(.s-pagination-disabled)')
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    self.random_sleep(1, 2)
                    next_button.click()
                    page_num += 1
                except:
                    logger.info("No more pages available")
                    break
                
        except Exception as e:
            logger.error(f"Error during product search: {str(e)}")

    def save_to_csv(self, filename):
        try:
            df = pd.DataFrame(self.products)
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"Successfully saved {len(self.products)} products to {filename}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")

    def run(self, search_query):
        try:
            if not self.setup_driver():
                return
            
            logger.info(f"Starting search for: {search_query}")
            self.search_products(search_query)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"amazon_products_{search_query.replace(' ', '_')}_{timestamp}.csv"
            self.save_to_csv(filename)
            
        except Exception as e:
            logger.error(f"Error in run method: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    scraper = AmazonScraper()
    search_query = input("Enter product to search (e.g. 'laptop', 'smartphone'): ")
    scraper.run(search_query)