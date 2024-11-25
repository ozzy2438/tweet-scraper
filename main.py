from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import csv
import logging
from datetime import datetime
from tqdm import tqdm
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwitterScraper:
    def __init__(self):
        self.driver = None
        self.search_query = "Data Science Project lang:en"
        self.tweets = []
        self.base_url = "https://twitter.com"

    def setup_driver(self):
        logger.info("Opening Twitter homepage...")
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        self.driver = webdriver.Chrome(options=options)
        logger.info("Chrome driver successfully initialized")
        
        self.driver.get('https://twitter.com/login')
        logger.info("Please login manually...")
        input("Press Enter after logging in...")

    def convert_to_number(self, value):
        try:
            # Remove any commas first
            value = value.replace(',', '')
            
            if value.isdigit():
                return int(value)
                
            # Handle K (thousands)
            if 'K' in value.upper():
                number = float(value.upper().replace('K', ''))
                return int(number * 1000)
                
            # Handle M (millions)
            if 'M' in value.upper():
                number = float(value.upper().replace('M', ''))
                return int(number * 1000000)
                
            # Handle B (billions)
            if 'B' in value.upper():
                number = float(value.upper().replace('B', ''))
                return int(number * 1000000000)
                
            return 0
        except:
            return 0

    def get_tweet_stats(self, tweet):
        try:
            stats = tweet.find_elements(By.CSS_SELECTOR, '[role="group"] span[data-testid="app-text-transition-container"]')
            replies = self.convert_to_number(stats[0].text) if len(stats) > 0 else 0
            reposts = self.convert_to_number(stats[1].text) if len(stats) > 1 else 0
            likes = self.convert_to_number(stats[2].text) if len(stats) > 2 else 0
            views = self.convert_to_number(stats[3].text) if len(stats) > 3 else 0
            return str(replies), str(reposts), str(likes), str(views)
        except:
            return "0", "0", "0", "0"

    def perform_search(self):
        try:
            logger.info("Starting search...")
            logger.info(f"Search query: {self.search_query}")
            logger.info(f"Performing search: {self.search_query}")
            
            logger.info("Entering search term...")
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="SearchBox_Search_Input"]'))
            )
            search_box.click()
            search_box.send_keys(self.search_query)
            time.sleep(2)
            search_box.send_keys(Keys.RETURN)
            
            logger.info("Search completed, loading results...")
            time.sleep(3)
            logger.info("Switched to Top tab")

            last_position = 0
            no_new_tweets_count = 0
            
            with tqdm(total=500, desc="Collecting tweets", unit="tweet/s") as pbar:
                while len(self.tweets) < 500:
                    tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                    
                    # Increment counter if no new tweets
                    if len(tweet_elements) == len(self.tweets):
                        no_new_tweets_count += 1
                    else:
                        no_new_tweets_count = 0
                    
                    # Continue with current tweets if no new ones after 3 scrolls
                    if no_new_tweets_count >= 3:
                        logger.info(f"Found total of {len(self.tweets)} tweets. No more tweets available.")
                        break
                    
                    for tweet in tweet_elements[len(self.tweets):]:  # Process only new tweets
                        if len(self.tweets) >= 500:
                            break
                            
                        try:
                            username = tweet.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]').text.split('\n')[0]
                            text = tweet.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]').text
                            time_element = tweet.find_element(By.TAG_NAME, "time")
                            timestamp = time_element.get_attribute("datetime")
                            tweet_url = urljoin(self.base_url, tweet.find_element(By.CSS_SELECTOR, 'a[role="link"]').get_attribute("href"))
                            
                            # Convert timestamp to time and date
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = dt.strftime("%I:%M %p")
                            date_str = dt.strftime("%d %b %Y")
                            
                            replies, reposts, likes, views = self.get_tweet_stats(tweet)
                            
                            if any(t["text"] == text for t in self.tweets):
                                continue
                                
                            self.tweets.append({
                                "username": username,
                                "text": text,
                                "replies": replies,
                                "reposts": reposts,
                                "likes": likes,
                                "views": views,
                                "url": tweet_url,
                                "time": time_str,
                                "date": date_str
                            })
                            pbar.update(1)
                            
                        except Exception as e:
                            continue
                    
                    self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                    time.sleep(1)

            self.save_tweets()
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")

    def save_tweets(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tweets_data_science_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["username", "text", "replies", "reposts", "likes", "views", "url", "time", "date"])
            writer.writeheader()
            writer.writerows(self.tweets)
        
        logger.info(f"500 tweets saved to {filename}")
        logger.info("Scraping completed successfully!")
        logger.info("Process completed/error occurred, waiting 30 seconds...")
        time.sleep(30)

    def run(self):
        self.setup_driver()
        self.perform_search()
        if self.driver:
            self.driver.quit()

def main():
    scraper = TwitterScraper()
    scraper.run()

if __name__ == "__main__":
    main()