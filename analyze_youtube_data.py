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

class YouTubeAnalyzer:
    def __init__(self, csv_file: str):
        """Initialize analyzer with CSV file path"""
        self.df = pd.read_csv(csv_file)
        self.preprocess_data()
        
    def preprocess_data(self):
        """Clean and prepare data for analysis"""
        # Convert views to numeric
        self.df['views'] = pd.to_numeric(self.df['views'])
        
        # Convert age to days for better analysis
        def convert_age_to_days(age: str) -> int:
            if 'year' in age:
                return int(re.findall(r'\d+', age)[0]) * 365
            elif 'month' in age:
                return int(re.findall(r'\d+', age)[0]) * 30
            elif 'week' in age:
                return int(re.findall(r'\d+', age)[0]) * 7
            elif 'day' in age:
                return int(re.findall(r'\d+', age)[0])
            elif 'hour' in age:
                return 0
            return 0
            
        self.df['days_ago'] = self.df['age'].apply(convert_age_to_days)
        
        # Extract keywords from titles
        self.df['keywords'] = self.df['title'].apply(lambda x: re.findall(r'\w+', x.lower()))
        
    def create_views_analysis(self) -> go.Figure:
        """Create views distribution analysis"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Top 10 Most Viewed Videos',
                'Views Distribution',
                'Views by Video Age',
                'Average Views by Channel'
            )
        )
        
        # Top 10 most viewed videos
        top_10 = self.df.nlargest(10, 'views')
        fig.add_trace(
            go.Bar(
                x=top_10['views'],
                y=top_10['title'].str[:50] + '...',
                orientation='h',
                name='Views'
            ),
            row=1, col=1
        )
        
        # Views distribution
        fig.add_trace(
            go.Histogram(
                x=self.df['views'],
                name='Distribution'
            ),
            row=1, col=2
        )
        
        # Views by video age
        fig.add_trace(
            go.Scatter(
                x=self.df['days_ago'],
                y=self.df['views'],
                mode='markers',
                name='Age vs Views'
            ),
            row=2, col=1
        )
        
        # Average views by channel
        channel_views = self.df.groupby('channel_id', observed=True)['views'].mean().sort_values(ascending=False).head(10)
        fig.add_trace(
            go.Bar(
                x=channel_views.index,
                y=channel_views.values,
                name='Avg Views'
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=1000,
            title_text="YouTube Video Views Analysis",
            showlegend=False
        )
        
        return fig
        
    def create_title_analysis(self) -> Dict[str, Any]:
        """Analyze video titles"""
        # Create word cloud
        all_words = ' '.join([' '.join(keywords) for keywords in self.df['keywords']])
        wordcloud = WordCloud(
            width=800, height=400,
            background_color='white',
            colormap='viridis'
        ).generate(all_words)
        
        # Common words analysis
        word_freq = {}
        for keywords in self.df['keywords']:
            for word in keywords:
                if len(word) > 3:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1
                    
        top_words = pd.Series(word_freq).sort_values(ascending=False).head(20)
        
        word_fig = go.Figure(data=[
            go.Bar(
                x=top_words.values,
                y=top_words.index,
                orientation='h'
            )
        ])
        
        word_fig.update_layout(
            title="Top 20 Words in Video Titles",
            xaxis_title="Frequency",
            yaxis_title="Word",
            height=600
        )
        
        return {
            'wordcloud': wordcloud,
            'word_frequency': word_fig
        }
        
    def create_age_analysis(self) -> go.Figure:
        """Analyze video age distribution"""
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                'Video Age Distribution',
                'Average Views by Video Age'
            )
        )
        
        # Age distribution
        fig.add_trace(
            go.Histogram(
                x=self.df['days_ago'],
                name='Age Distribution'
            ),
            row=1, col=1
        )
        
        # Average views by age group
        self.df['age_group'] = pd.cut(
            self.df['days_ago'],
            bins=[0, 30, 90, 180, 365, float('inf')],
            labels=['< 1 month', '1-3 months', '3-6 months', '6-12 months', '> 1 year']
        )
        
        age_views = self.df.groupby('age_group')['views'].mean()
        fig.add_trace(
            go.Bar(
                x=age_views.index,
                y=age_views.values,
                name='Avg Views'
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            height=500,
            title_text="Video Age Analysis"
        )
        
        return fig
        
    def generate_report(self, output_dir: str = 'youtube_analysis'):
        """Generate complete analysis report"""
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Views analysis
        views_fig = self.create_views_analysis()
        views_fig.write_html(f"{output_dir}/views_analysis.html")
        
        # Title analysis
        title_analysis = self.create_title_analysis()
        plt.figure(figsize=(10, 5))
        plt.imshow(title_analysis['wordcloud'])
        plt.axis('off')
        plt.savefig(f"{output_dir}/wordcloud.png", bbox_inches='tight', pad_inches=0)
        plt.close()
        title_analysis['word_frequency'].write_html(f"{output_dir}/word_frequency.html")
        
        # Age analysis
        age_fig = self.create_age_analysis()
        age_fig.write_html(f"{output_dir}/age_analysis.html")
        
        # Generate detailed summary statistics
        summary = {
            'Dataset Overview': {
                'Total Videos Analyzed': len(self.df),
                'Unique Content Creators': self.df['channel_id'].nunique(),
                'Data Collection Period': f"Videos from {self.df['days_ago'].max()} days ago to {self.df['days_ago'].min()} days ago"
            },
            'Engagement Metrics': {
                'Total Views': self.df['views'].sum(),
                'Average Views per Video': int(self.df['views'].mean()),
                'Median Views': int(self.df['views'].median()),
                'Most Popular Video': {
                    'Title': self.df.loc[self.df['views'].idxmax(), 'title'],
                    'Views': int(self.df['views'].max()),
                    'Channel': self.df.loc[self.df['views'].idxmax(), 'channel_id']
                }
            },
            'Content Analysis': {
                'Most Recent Video': {
                    'Title': self.df.loc[self.df['days_ago'].idxmin(), 'title'],
                    'Age': self.df.loc[self.df['days_ago'].idxmin(), 'age'],
                    'Views': int(self.df.loc[self.df['days_ago'].idxmin(), 'views'])
                },
                'Video Age Distribution': {
                    'Less than 1 month': len(self.df[self.df['days_ago'] <= 30]),
                    '1-3 months': len(self.df[(self.df['days_ago'] > 30) & (self.df['days_ago'] <= 90)]),
                    '3-6 months': len(self.df[(self.df['days_ago'] > 90) & (self.df['days_ago'] <= 180)]),
                    'Over 6 months': len(self.df[self.df['days_ago'] > 180])
                }
            },
            'Top Performing Channels': {
                'By Average Views': self.df.groupby('channel_id', observed=True)['views']
                    .agg(['mean', 'count'])
                    .sort_values('mean', ascending=False)
                    .head(5)
                    .to_dict('index')
            }
        }
        
        with open(f"{output_dir}/summary.txt", 'w') as f:
            f.write("YouTube Data Science Content Analysis Report\n")
            f.write("=========================================\n\n")
            f.write(f"Report Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=========================================\n\n")
            
            # Dataset Overview
            f.write("📊 DATASET OVERVIEW\n")
            f.write("------------------\n")
            for key, value in summary['Dataset Overview'].items():
                if isinstance(value, (int, np.integer)):
                    f.write(f"• {key}: {value:,}\n")
                else:
                    f.write(f"• {key}: {value}\n")
            f.write("\n")
            
            # Engagement Metrics
            f.write("👥 ENGAGEMENT METRICS\n")
            f.write("--------------------\n")
            for key, value in summary['Engagement Metrics'].items():
                if key == 'Most Popular Video':
                    f.write(f"• {key}:\n")
                    f.write(f"  - Title: {value['Title']}\n")
                    f.write(f"  - Views: {value['Views']:,}\n")
                    f.write(f"  - Channel: {value['Channel']}\n")
                else:
                    f.write(f"• {key}: {value:,}\n")
            f.write("\n")
            
            # Content Analysis
            f.write("📈 CONTENT ANALYSIS\n")
            f.write("-------------------\n")
            f.write("• Most Recent Video:\n")
            f.write(f"  - Title: {summary['Content Analysis']['Most Recent Video']['Title']}\n")
            f.write(f"  - Age: {summary['Content Analysis']['Most Recent Video']['Age']}\n")
            f.write(f"  - Views: {summary['Content Analysis']['Most Recent Video']['Views']:,}\n\n")
            
            f.write("• Video Age Distribution:\n")
            for period, count in summary['Content Analysis']['Video Age Distribution'].items():
                percentage = (count / len(self.df)) * 100
                f.write(f"  - {period}: {count:,} videos ({percentage:.1f}%)\n")
            f.write("\n")
            
            # Top Performing Channels
            f.write("🏆 TOP PERFORMING CHANNELS\n")
            f.write("------------------------\n")
            f.write("Based on average views per video:\n")
            for channel, stats in summary['Top Performing Channels']['By Average Views'].items():
                f.write(f"\n• Channel: {channel}\n")
                f.write(f"  - Average Views: {int(stats['mean']):,}\n")
                f.write(f"  - Total Videos: {int(stats['count']):,}\n")
            
            f.write("\n=========================================\n")
            f.write("📝 Note: This analysis is based on the current dataset and may not represent the complete YouTube landscape.\n")
            f.write("For interactive visualizations, please refer to the HTML files in this directory.\n")
        
        print(f"Analysis complete! Reports saved to '{output_dir}' directory")
        print("\nGenerated files:")
        print("1. views_analysis.html - Interactive views analysis")
        print("2. wordcloud.png - Word cloud of video titles")
        print("3. word_frequency.html - Common words analysis")
        print("4. age_analysis.html - Video age analysis")
        print("5. summary.txt - Comprehensive statistics and insights")

def main():
    # Find the most recent CSV file
    csv_files = [f for f in os.listdir() if f.startswith('youtube_videos_') and f.endswith('.csv')]
    if not csv_files:
        print("No YouTube video CSV files found!")
        return
        
    latest_csv = max(csv_files)
    print(f"Analyzing {latest_csv}...")
    
    analyzer = YouTubeAnalyzer(latest_csv)
    analyzer.generate_report()

if __name__ == "__main__":
    main()
