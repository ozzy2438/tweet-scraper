from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import logging
from datetime import datetime
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeScraper:
    def __init__(self):
        self.driver = None
        self.search_query = "data science projects for intermediates"
        self.videos = []
        self.target_count = 50
        
    def convert_to_number(self, text):
        """Convert YouTube number format to integer"""
        if not text:
            return 0
            
        text = text.lower().replace(',', '')
        multiplier = 1
        
        if 'k' in text:
            multiplier = 1000
            text = text.replace('k', '')
        elif 'm' in text:
            multiplier = 1000000
            text = text.replace('m', '')
            
        try:
            return int(float(text) * multiplier)
        except:
            return 0
            
    def setup_driver(self):
        logger.info("Opening YouTube...")
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        self.driver = webdriver.Chrome(options=options)
        logger.info("Chrome driver successfully initialized")
        
    def scroll_to_load_more(self):
        """Scroll down to load more videos"""
        last_height = self.driver.execute_script("return document.documentElement.scrollHeight")
        
        # Scroll down 3 times with small delays
        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(1)
        
        # Check if we've reached the bottom
        new_height = self.driver.execute_script("return document.documentElement.scrollHeight")
        return new_height != last_height
        
    def perform_search(self):
        try:
            logger.info(f"Starting search for: {self.search_query}")
            
            # Go to search URL directly and sort by view count
            search_url = f"https://www.youtube.com/results?search_query={self.search_query.replace(' ', '+')}&sp=CAMSAhAB"
            self.driver.get(search_url)
            time.sleep(3)
            
            # Wait for videos to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "ytd-video-renderer"))
            )
            
            logger.info("Search completed, collecting videos...")
            
            with tqdm(total=self.target_count, desc="Collecting videos", unit="video") as pbar:
                while len(self.videos) < self.target_count:
                    # Get all video elements
                    video_elements = self.driver.find_elements(By.TAG_NAME, "ytd-video-renderer")
                    
                    # Process new videos
                    new_videos = []
                    for video in video_elements[len(self.videos):]:
                        if len(self.videos) >= self.target_count:
                            break
                            
                        try:
                            # Get video title and URL
                            title_element = video.find_element(By.CSS_SELECTOR, '#video-title')
                            title = title_element.text.strip()
                            video_url = title_element.get_attribute('href')
                            
                            # Get channel info
                            try:
                                channel_element = video.find_element(By.CSS_SELECTOR, 'ytd-channel-name a')
                                channel_url = channel_element.get_attribute('href')
                                channel_id = channel_url.split('/')[-1] if channel_url else "Unknown"
                            except:
                                channel_id = "Unknown"
                            
                            # Get view count and age
                            meta_elements = video.find_elements(By.CSS_SELECTOR, '#metadata-line span')
                            view_count = 0
                            video_age = "Unknown"
                            
                            if len(meta_elements) >= 2:
                                for element in meta_elements:
                                    text = element.text.lower()
                                    if 'views' in text:
                                        view_count = self.convert_to_number(text.split(' ')[0])
                                    elif any(time_unit in text for time_unit in ['year', 'month', 'week', 'day', 'hour']):
                                        video_age = element.text
                            
                            # Skip duplicates
                            if not any(v["url"] == video_url for v in self.videos):
                                new_videos.append({
                                    "title": title,
                                    "url": video_url,
                                    "channel_id": channel_id,
                                    "views": view_count,
                                    "age": video_age
                                })
                            
                        except Exception as e:
                            logger.error(f"Error processing video: {str(e)}")
                            continue
                    
                    # Update progress
                    if new_videos:
                        self.videos.extend(new_videos)
                        pbar.update(len(new_videos))
                        logger.info(f"Added {len(new_videos)} new videos. Total: {len(self.videos)}")
                    
                    # Try to load more videos if needed
                    if len(self.videos) < self.target_count:
                        if not self.scroll_to_load_more():
                            logger.info("No more videos to load")
                            break
                        time.sleep(2)  # Wait for new videos to load
            
            self.save_videos()
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            
    def save_videos(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"youtube_videos_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "title", "url", "channel_id", "views", "age"
            ])
            writer.writeheader()
            writer.writerows(self.videos)
        
        logger.info(f"{len(self.videos)} videos saved to {filename}")
        logger.info("Scraping completed successfully!")
        
    def run(self):
        try:
            self.setup_driver()
            self.perform_search()
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    scraper = YouTubeScraper()
    scraper.run()
