import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re
import os
from typing import List, Dict, Any
from textblob import TextBlob
import seaborn as sns
import io
import base64

class TweetAnalyzer:
    def __init__(self, csv_file: str):
        """Initialize analyzer with CSV file path"""
        self.df = pd.read_csv(csv_file)
        self.preprocess_data()
        
    def preprocess_data(self):
        """Clean and prepare data for analysis"""
        # Convert date and time to datetime
        self.df['created_at'] = pd.to_datetime(self.df['date'] + ' ' + self.df['time'], errors='coerce')
        
        # Convert numeric columns
        numeric_cols = ['replies', 'reposts', 'likes', 'views']
        for col in numeric_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0).astype(int)
        
        # Calculate engagement metrics (after numeric conversion)
        self.df['engagement'] = pd.to_numeric(self.df['likes'] + self.df['reposts'], errors='coerce').fillna(0).astype(float)
        
        # Perform sentiment analysis and ensure float type
        def get_sentiment(text):
            try:
                return float(TextBlob(str(text)).sentiment.polarity)
            except:
                return 0.0
        
        self.df['sentiment'] = self.df['text'].apply(get_sentiment).astype(float)
        
        # Extract hashtags
        self.df['hashtags'] = self.df['text'].apply(
            lambda x: re.findall(r'#(\w+)', str(x).lower())
        )
        
        # Finans konularına özel anahtar kelime analizi için yeni alan
        finance_keywords = ['interest rate', 'finance', 'loan', 'bank', 'investment', 
                          'market', 'stock', 'debt', 'credit', 'mortgage']
        
        def extract_finance_topics(text):
            text = str(text).lower()
            return [keyword for keyword in finance_keywords if keyword in text]
            
        self.df['finance_topics'] = self.df['text'].apply(extract_finance_topics)
        
        # Print data types for debugging
        print("\nColumn data types after preprocessing:")
        print(self.df.dtypes[['engagement', 'sentiment']])
        
    def get_date_range(self) -> str:
        """Get formatted date range string, handling NaT values"""
        valid_dates = self.df['created_at'].dropna()
        if len(valid_dates) == 0:
            return "No valid dates found"
        
        start_date = valid_dates.min()
        end_date = valid_dates.max()
        
        try:
            return f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        except:
            return "Error formatting dates"

    def create_engagement_analysis(self) -> go.Figure:
        """Create engagement distribution analysis"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Top 10 Most Engaged Tweets',
                'Engagement Distribution',
                'Engagement Over Time',
                'Average Engagement by Hour'
            )
        )
        
        # Top 10 most engaged tweets
        top_10 = self.df.nlargest(10, 'engagement')
        fig.add_trace(
            go.Bar(
                x=top_10['engagement'],
                y=top_10['text'].str[:50] + '...',
                orientation='h',
                name='Engagement'
            ),
            row=1, col=1
        )
        
        # Engagement distribution
        fig.add_trace(
            go.Histogram(
                x=self.df['engagement'],
                name='Distribution'
            ),
            row=1, col=2
        )
        
        # Engagement over time
        daily_engagement = self.df.groupby(self.df['created_at'].dt.date)['engagement'].mean()
        fig.add_trace(
            go.Scatter(
                x=daily_engagement.index,
                y=daily_engagement.values,
                mode='lines+markers',
                name='Daily Engagement'
            ),
            row=2, col=1
        )
        
        # Average engagement by hour
        hourly_engagement = self.df.groupby(self.df['created_at'].dt.hour)['engagement'].mean()
        fig.add_trace(
            go.Bar(
                x=hourly_engagement.index,
                y=hourly_engagement.values,
                name='Hourly Engagement'
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=1000,
            title_text="Tweet Engagement Analysis",
            showlegend=False
        )
        
        return fig
        
    def create_sentiment_analysis(self) -> go.Figure:
        """Analyze tweet sentiments"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Sentiment Distribution',
                'Sentiment vs Engagement',
                'Average Sentiment Over Time',
                'Top Positive vs Negative Tweets'
            )
        )
        
        # Sentiment distribution
        fig.add_trace(
            go.Histogram(
                x=self.df['sentiment'],
                name='Sentiment'
            ),
            row=1, col=1
        )
        
        # Sentiment vs Engagement
        fig.add_trace(
            go.Scatter(
                x=self.df['sentiment'],
                y=self.df['engagement'],
                mode='markers',
                name='Sentiment vs Engagement'
            ),
            row=1, col=2
        )
        
        # Average sentiment over time
        daily_sentiment = self.df.groupby(self.df['created_at'].dt.date)['sentiment'].mean()
        fig.add_trace(
            go.Scatter(
                x=daily_sentiment.index,
                y=daily_sentiment.values,
                mode='lines+markers',
                name='Daily Sentiment'
            ),
            row=2, col=1
        )
        
        # Top positive and negative tweets
        top_pos = self.df.nlargest(5, 'sentiment')
        top_neg = self.df.nsmallest(5, 'sentiment')
        combined = pd.concat([top_pos, top_neg])
        
        fig.add_trace(
            go.Bar(
                x=combined['sentiment'],
                y=combined['text'].str[:50] + '...',
                orientation='h',
                name='Extreme Sentiments'
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=1000,
            title_text="Tweet Sentiment Analysis",
            showlegend=False
        )
        
        return fig
        
    def create_hashtag_analysis(self) -> go.Figure:
        """Create hashtag analysis visualization"""
        # Flatten hashtag lists and count frequencies
        all_hashtags = [tag for tags in self.df['hashtags'] for tag in tags]
        
        if not all_hashtags:
            # Create empty figure with message if no hashtags
            fig = go.Figure()
            fig.add_annotation(
                text="No hashtags found in the dataset",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14)
            )
            return fig
            
        hashtag_freq = pd.Series(all_hashtags).value_counts()
        
        # Create word cloud
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap='viridis'
        ).generate(' '.join(all_hashtags))
        
        # Convert word cloud to image
        img = wordcloud.to_image()
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Create figure with word cloud
        fig = go.Figure()
        
        fig.add_layout_image(
            dict(
                source=f'data:image/png;base64,{base64.b64encode(img_byte_arr).decode()}',
                x=0,
                y=1,
                sizex=1,
                sizey=1,
                xref="paper",
                yref="paper",
                sizing="stretch"
            )
        )
        
        fig.update_layout(
            title="Hashtag Word Cloud",
            showlegend=False,
            width=800,
            height=400,
            margin=dict(t=30, b=0, l=0, r=0)
        )
        
        return fig
        
    def get_max_engagement_tweet(self) -> dict:
        """Get tweet with maximum engagement, with error handling"""
        if self.df['engagement'].empty or self.df['engagement'].isna().all():
            return {
                'Text': "No tweets with engagement data found",
                'Engagement': 0
            }
        
        try:
            max_idx = self.df['engagement'].idxmax()
            return {
                'Text': self.df.loc[max_idx, 'text'],
                'Engagement': int(self.df.loc[max_idx, 'engagement'])
            }
        except:
            return {
                'Text': "Error finding most engaged tweet",
                'Engagement': 0
            }

    def get_sentiment_extremes(self) -> tuple:
        """Get most positive and negative tweets, with error handling"""
        if self.df['sentiment'].empty or self.df['sentiment'].isna().all():
            empty_result = {
                'Text': "No tweets with sentiment data found",
                'Score': 0.0
            }
            return empty_result, empty_result
        
        try:
            max_idx = self.df['sentiment'].idxmax()
            min_idx = self.df['sentiment'].idxmin()
            
            return (
                {
                    'Text': self.df.loc[max_idx, 'text'],
                    'Score': round(float(self.df.loc[max_idx, 'sentiment']), 3)
                },
                {
                    'Text': self.df.loc[min_idx, 'text'],
                    'Score': round(float(self.df.loc[min_idx, 'sentiment']), 3)
                }
            )
        except:
            empty_result = {
                'Text': "Error finding sentiment extremes",
                'Score': 0.0
            }
            return empty_result, empty_result

    def format_number(self, value) -> str:
        """Format number with comma separators if numeric, otherwise return as is"""
        try:
            return f"{float(value):,.0f}" if isinstance(value, (int, float)) else str(value)
        except:
            return str(value)

    def analyze_finance_topics(self) -> go.Figure:
        """Finans konularının popülerlik ve etkileşim analizini yapar"""
        # Tüm finans konularını düzleştir
        all_topics = [topic for topics in self.df['finance_topics'] for topic in topics]
        topic_counts = pd.Series(all_topics).value_counts()
        
        # Konu başına ortalama etkileşimi hesapla
        topic_engagement = {}
        for topic in set(all_topics):
            tweets_with_topic = self.df[self.df['finance_topics'].apply(lambda x: topic in x)]
            avg_engagement = tweets_with_topic['engagement'].mean()
            topic_engagement[topic] = avg_engagement
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('En Çok Konuşulan Finans Konuları', 'Konulara Göre Ortalama Etkileşim')
        )
        
        # Konu frekansı grafiği
        fig.add_trace(
            go.Bar(
                x=topic_counts.index,
                y=topic_counts.values,
                name='Konu Frekansı'
            ),
            row=1, col=1
        )
        
        # Konu etkileşimi grafiği
        fig.add_trace(
            go.Bar(
                x=list(topic_engagement.keys()),
                y=list(topic_engagement.values()),
                name='Ortalama Etkileşim'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=800,
            title_text="Finans Konuları Analizi",
            showlegend=False
        )
        
        return fig

    def get_top_finance_tweets(self, n=5) -> dict:
        """En çok etkileşim alan finans tweetlerini getirir"""
        # Finans konuları içeren tweetleri filtrele
        finance_tweets = self.df[self.df['finance_topics'].apply(len) > 0]
        
        return {
            'En Çok Beğenilen': finance_tweets.nlargest(n, 'likes')[['text', 'likes', 'finance_topics']].to_dict('records'),
            'En Çok Repost Edilen': finance_tweets.nlargest(n, 'reposts')[['text', 'reposts', 'finance_topics']].to_dict('records'),
            'En Yüksek Etkileşimli': finance_tweets.nlargest(n, 'engagement')[['text', 'engagement', 'finance_topics']].to_dict('records')
        }

    def generate_report(self, output_dir: str = 'twitter_analysis'):
        """Generate complete analysis report"""
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Check if dataset is empty
        if len(self.df) == 0:
            with open(f"{output_dir}/summary.txt", 'w') as f:
                f.write("Twitter Data Analysis Report\n")
                f.write("==========================\n\n")
                f.write("⚠️ No tweets found in the dataset.\n")
            print(f"Analysis complete! Empty report saved to '{output_dir}/summary.txt'")
            return
        
        # Engagement analysis
        engagement_fig = self.create_engagement_analysis()
        engagement_fig.write_html(f"{output_dir}/engagement_analysis.html")
        
        # Sentiment analysis
        sentiment_fig = self.create_sentiment_analysis()
        sentiment_fig.write_html(f"{output_dir}/sentiment_analysis.html")
        
        # Hashtag analysis
        hashtag_fig = self.create_hashtag_analysis()
        hashtag_fig.write_html(f"{output_dir}/hashtag_analysis.html")
        
        # Finans analizi ekle
        finance_fig = self.analyze_finance_topics()
        finance_fig.write_html(f"{output_dir}/finance_analysis.html")
        
        top_finance_tweets = self.get_top_finance_tweets()
        
        with open(f"{output_dir}/finance_summary.txt", 'w', encoding='utf-8') as f:
            f.write("Finans Tweet Analizi\n")
            f.write("===================\n\n")
            
            # En çok beğenilen finans tweetleri
            f.write("🌟 EN ÇOK BEĞENİLEN FİNANS TWEETLERİ\n")
            f.write("--------------------------------\n")
            for tweet in top_finance_tweets['En Çok Beğenilen']:
                f.write(f"• Beğeni: {tweet['likes']}\n")
                f.write(f"• Konular: {', '.join(tweet['finance_topics'])}\n")
                f.write(f"• Tweet: {tweet['text']}\n\n")
            
            # En çok repost edilen finans tweetleri
            f.write("🔄 EN ÇOK REPOST EDİLEN FİNANS TWEETLERİ\n")
            f.write("-------------------------------------\n")
            for tweet in top_finance_tweets['En Çok Repost Edilen']:
                f.write(f"• Repost: {tweet['reposts']}\n")
                f.write(f"• Konular: {', '.join(tweet['finance_topics'])}\n")
                f.write(f"• Tweet: {tweet['text']}\n\n")
            
            # En yüksek etkileşimli finans tweetleri
            f.write("💫 EN YÜKSEK ETKİLEŞİMLİ FİNANS TWEETLERİ\n")
            f.write("---------------------------------------\n")
            for tweet in top_finance_tweets['En Yüksek Etkileşimli']:
                f.write(f"• Etkileşim: {tweet['engagement']}\n")
                f.write(f"• Konular: {', '.join(tweet['finance_topics'])}\n")
                f.write(f"• Tweet: {tweet['text']}\n\n")
        
        # Get valid temporal statistics
        valid_times = self.df['created_at'].dropna()
        most_active_hour = valid_times.dt.hour.mode().iloc[0] if len(valid_times) > 0 else "N/A"
        most_active_day = valid_times.dt.day_name().mode().iloc[0] if len(valid_times) > 0 else "N/A"
        peak_engagement_hour = (
            self.df.dropna(subset=['created_at', 'engagement'])
            .groupby(self.df['created_at'].dt.hour)['engagement']
            .mean()
            .idxmax()
        ) if len(valid_times) > 0 else "N/A"
        
        # Get extreme tweets
        most_engaged_tweet = self.get_max_engagement_tweet()
        most_positive_tweet, most_negative_tweet = self.get_sentiment_extremes()
        
        # Calculate sentiment distribution safely
        total_tweets = max(len(self.df), 1)  # Avoid division by zero
        sentiment_counts = {
            'Positive': len(self.df[self.df['sentiment'] > 0]),
            'Negative': len(self.df[self.df['sentiment'] < 0]),
            'Neutral': len(self.df[self.df['sentiment'] == 0])
        }
        
        # Generate detailed summary statistics
        summary = {
            'Dataset Overview': {
                'Total Tweets Analyzed': len(self.df),
                'Date Range': self.get_date_range(),
                'Unique Hashtags': sum(len(tags) for tags in self.df['hashtags'])
            },
            'Engagement Metrics': {
                'Total Likes': int(self.df['likes'].sum()),
                'Total Retweets': int(self.df['reposts'].sum()),
                'Total Replies': int(self.df['replies'].sum()),
                'Average Engagement': round(float(self.df['engagement'].mean()), 2),
                'Most Engaged Tweet': most_engaged_tweet
            },
            'Sentiment Analysis': {
                'Average Sentiment': round(float(self.df['sentiment'].mean()), 3),
                'Sentiment Distribution': sentiment_counts,
                'Most Positive Tweet': most_positive_tweet,
                'Most Negative Tweet': most_negative_tweet
            },
            'Temporal Patterns': {
                'Most Active Hour': most_active_hour,
                'Most Active Day': most_active_day,
                'Peak Engagement Hour': peak_engagement_hour
            },
            'Top Hashtags': pd.Series([tag for tags in self.df['hashtags'] for tag in tags]).value_counts().head(5).to_dict()
        }
        
        with open(f"{output_dir}/summary.txt", 'w') as f:
            f.write("Twitter Data Analysis Report\n")
            f.write("==========================\n\n")
            
            # Dataset Overview
            f.write("📊 DATASET OVERVIEW\n")
            f.write("-----------------\n")
            for key, value in summary['Dataset Overview'].items():
                f.write(f"• {key}: {self.format_number(value)}\n")
            f.write("\n")
            
            # Engagement Metrics
            f.write("💫 ENGAGEMENT METRICS\n")
            f.write("-------------------\n")
            for key, value in summary['Engagement Metrics'].items():
                if key == 'Most Engaged Tweet':
                    f.write(f"• {key}:\n")
                    f.write(f"  - Text: {value['Text']}\n")
                    f.write(f"  - Engagement: {self.format_number(value['Engagement'])}\n")
                else:
                    f.write(f"• {key}: {self.format_number(value)}\n")
            f.write("\n")
            
            # Sentiment Analysis
            f.write("❤️ SENTIMENT ANALYSIS\n")
            f.write("--------------------\n")
            f.write(f"• Average Sentiment: {summary['Sentiment Analysis']['Average Sentiment']:.3f}\n")
            f.write("• Sentiment Distribution:\n")
            
            # Safe percentage calculation
            sentiment_dist = summary['Sentiment Analysis']['Sentiment Distribution']
            for sentiment_type, count in sentiment_dist.items():
                percentage = (count / total_tweets * 100)
                f.write(f"  - {sentiment_type}: {self.format_number(count)} tweets ({percentage:.1f}%)\n")
            
            f.write("\n• Most Positive Tweet:\n")
            f.write(f"  - Text: {summary['Sentiment Analysis']['Most Positive Tweet']['Text']}\n")
            f.write(f"  - Sentiment Score: {summary['Sentiment Analysis']['Most Positive Tweet']['Score']:.3f}\n")
            
            f.write("\n• Most Negative Tweet:\n")
            f.write(f"  - Text: {summary['Sentiment Analysis']['Most Negative Tweet']['Text']}\n")
            f.write(f"  - Sentiment Score: {summary['Sentiment Analysis']['Most Negative Tweet']['Score']:.3f}\n")
            f.write("\n")
            
            # Temporal Patterns
            f.write("⏰ TEMPORAL PATTERNS\n")
            f.write("-------------------\n")
            f.write(f"• Most Active Hour: {summary['Temporal Patterns']['Most Active Hour']}\n")
            f.write(f"• Most Active Day: {summary['Temporal Patterns']['Most Active Day']}\n")
            f.write(f"• Peak Engagement Hour: {summary['Temporal Patterns']['Peak Engagement Hour']}\n")
            f.write("\n")
            
            # Top Hashtags
            f.write("🏷️ TOP HASHTAGS\n")
            f.write("--------------\n")
            if summary['Top Hashtags']:
                for tag, count in summary['Top Hashtags'].items():
                    f.write(f"• #{tag}: {self.format_number(count)}\n")
            else:
                f.write("• No hashtags found in the dataset\n")
            f.write("\n")
        
        print(f"Analysis complete! Reports saved to '{output_dir}' directory")
        print("\nGenerated files:")
        print("1. engagement_analysis.html - Interactive engagement analysis")
        print("2. sentiment_analysis.html - Interactive sentiment analysis")
        print("3. hashtag_analysis.html - Interactive hashtag analysis")
        print("4. finance_analysis.html - Interactive finance analysis")
        print("5. finance_summary.txt - Detailed finance tweet analysis")
        print("6. summary.txt - Comprehensive statistics and insights")

def main():
    # Find the most recent CSV file
    csv_files = [f for f in os.listdir() if f.startswith('tweets_') and f.endswith('.csv')]
    if not csv_files:
        print("No tweet CSV files found!")
        return
        
    latest_csv = max(csv_files)
    print(f"Analyzing {latest_csv}...")
    
    analyzer = TweetAnalyzer(latest_csv)
    analyzer.generate_report()

if __name__ == "__main__":
    main()
