from datetime import datetime, timedelta
from gnews import GNews
import pandas as pd
import json
import logging
import time
import os
from news_analyzer import NewsAnalyzer

def categorize_crime(title):
    """Determine specific crime category based on title keywords"""
    title = title.lower()
    if any(word in title for word in ['murder', 'killed', 'fatal', 'death', 'homicide']):
        return 'Murder'
    elif any(word in title for word in ['shooting', 'shot', 'gunfire']):
        return 'Shooting'
    elif any(word in title for word in ['robbery', 'robber', 'theft', 'stolen']):
        return 'Robbery'
    elif any(word in title for word in ['assault', 'attack', 'violence']):
        return 'Assault'
    return 'Other Crime'

def clean_text(text):
    """Clean special characters and encoding issues"""
    import unicodedata
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    # Replace common encoding issues
    text = text.encode('ascii', 'ignore').decode()
    return text.strip()

def scrape_news(query, start_date, end_date, language='en', country='US', max_results=200):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    print(f"Requesting news from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Tarihi periyotlara böl
    date_ranges = []
    current_date = start_date
    while current_date < end_date:
        range_end = min(current_date + timedelta(days=30), end_date)
        date_ranges.append((current_date, range_end))
        current_date = range_end + timedelta(days=1)
    
    all_news = []
    total_articles = 0
    
    # Her periyot için ayrı arama yap
    for period_start, period_end in date_ranges:
        google_news = GNews(
            language=language,
            country=country,
            max_results=max_results // len(date_ranges),  # Sonuçları periyotlara böl
            start_date=period_start,
            end_date=period_end
        )
        
        print(f"\nSearching period: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}")
        news_results = google_news.get_news(query)
        
        if news_results:
            for item in news_results:
                if total_articles >= max_results:
                    break
                    
                news_item = {
                    'Title': clean_text(item['title']),
                    'Description': clean_text(item['description']),
                    'Published_Date': item['published date'],
                    'Publisher': clean_text(item['publisher']['title']),
                    'Crime_Type': categorize_crime(item['title']),
                    'Country': country,
                    'Source_URL': item['url'],
                    'Search_Query': query
                }
                
                # Tekrarlanan haberleri önle
                if not any(existing['Source_URL'] == news_item['Source_URL'] for existing in all_news):
                    all_news.append(news_item)
                    total_articles += 1
                    
                    # Her 10 makalede bir güncelleme göster
                    if total_articles % 10 == 0:
                        print(f"Collected {total_articles} articles so far...")
        
        time.sleep(2)  # API rate limiting'i önlemek için bekle
    
    df = pd.DataFrame(all_news)
    return df

# Genç nesil suçları için anahtar kelimeler - daha basit ve net sorgu
QUERY = "teen OR teenager OR youth OR student crime OR juvenile delinquency OR school shooting OR campus violence"

# Tarih aralıklarını belirle
date_ranges = [
    ("2024-01-01", "2024-01-31"),
    ("2024-02-01", "2024-02-29"),
    ("2024-03-01", "2024-03-31"),
    ("2024-04-01", "2024-04-30"),
    ("2024-05-01", "2024-05-31"),
    ("2024-06-01", "2024-06-30"),
    ("2024-07-01", "2024-07-31"),
    ("2024-08-01", "2024-08-31"),
    ("2024-09-01", "2024-09-30"),
    ("2024-10-01", "2024-10-31"),
    ("2024-11-01", "2024-11-30")
]

total_articles = 0
articles_per_month = 400 // len(date_ranges)  # Her ay için yaklaşık 36-37 makale

# Tüm haberleri tek bir CSV'de topla
all_articles_df = pd.DataFrame()

for start_date, end_date in date_ranges:
    print(f"\nScraping news for period: {start_date} to {end_date}")
    
    try:
        df = scrape_news(
            query=QUERY,
            start_date=start_date,
            end_date=end_date,
            language='en',
            country='US',
            max_results=articles_per_month
        )
        
        # Dataframe'leri birleştir
        all_articles_df = pd.concat([all_articles_df, df], ignore_index=True)
        
        total_articles = len(all_articles_df)
        print(f"Articles collected for this period: {len(df)}")
        print(f"Total articles so far: {total_articles}")
        
        # API limitlerini aşmamak için bekle
        time.sleep(5)
        
    except Exception as e:
        print(f"Error collecting articles for {start_date} to {end_date}: {str(e)}")
        continue

print(f"\nScraping completed! Total articles collected: {total_articles}")

# Tüm verileri tek bir CSV'ye kaydet
output_filename = "youth_crime_news_202401_202411.csv"
all_articles_df.to_csv(output_filename, index=False)
print(f"\nAll articles saved to: {output_filename}")

# Analiz yap
try:
    analyzer = NewsAnalyzer('youth_crime_news_202401_202411.csv')
    analyzer.analyze()
except Exception as e:
    print(f"Analysis error: {str(e)}")