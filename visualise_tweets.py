import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import glob
import os

class TweetVisualizer:
    def __init__(self):
        self.latest_csv = None
        self.df = None
        self.output_dir = "tweet_analytics"
        
        # Create analytics folder if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def load_latest_data(self):
        """Load the most recently created CSV file"""
        # Find the latest CSV file
        csv_files = glob.glob("tweets_data_science_*.csv")
        if not csv_files:
            raise Exception("No CSV file found!")
            
        self.latest_csv = max(csv_files, key=os.path.getctime)
        print(f"Loaded file: {self.latest_csv}")
        
        # Load CSV into DataFrame
        self.df = pd.read_csv(self.latest_csv)
        
        # Fix numeric columns
        numeric_cols = ['replies', 'reposts', 'likes', 'views']
        for col in numeric_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0).astype(int)

    def create_engagement_scatter(self):
        """Likes vs Reposts Scatter Plot with Plotly"""
        fig = px.scatter(
            self.df,
            x='likes',
            y='reposts',
            size='views',
            hover_data=['username', 'text'],
            title='Tweet Engagement Analysis: Likes vs Reposts',
            labels={'likes': 'Likes Count', 'reposts': 'Repost Count', 'views': 'View Count'},
            color='replies',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            template='plotly_dark',
            title_x=0.5,
            title_font_size=24
        )
        
        fig.write_html(f"{self.output_dir}/engagement_scatter.html")
        print("Engagement scatter plot created!")

    def create_top_users_bar(self):
        """Top 20 Users by Total Engagement"""
        # Calculate total engagement
        self.df['total_engagement'] = self.df['likes'] + self.df['reposts'] + self.df['replies']
        
        # Get top 20 users
        top_users = self.df.nlargest(20, 'total_engagement')
        
        # Create bar chart with Plotly
        fig = go.Figure()
        
        # Separate bars for Likes, Reposts and Replies
        fig.add_trace(go.Bar(
            name='Likes',
            x=top_users['username'],
            y=top_users['likes'],
            marker_color='#1DA1F2'
        ))
        
        fig.add_trace(go.Bar(
            name='Reposts',
            x=top_users['username'],
            y=top_users['reposts'],
            marker_color='#17BF63'
        ))
        
        fig.add_trace(go.Bar(
            name='Replies',
            x=top_users['username'],
            y=top_users['replies'],
            marker_color='#F45D22'
        ))
        
        fig.update_layout(
            title='Top 20 Users by Engagement',
            title_x=0.5,
            barmode='stack',
            template='plotly_dark',
            xaxis_tickangle=-45,
            height=800
        )
        
        fig.write_html(f"{self.output_dir}/top_users.html")
        print("Top users bar chart created!")

    def create_time_distribution(self):
        """Tweet Time Distribution Heatmap"""
        # Convert time and date columns to datetime
        self.df['datetime'] = pd.to_datetime(self.df['date'] + ' ' + self.df['time'], format='%d %b %Y %I:%M %p')
        
        # Extract hour and day information
        self.df['hour'] = self.df['datetime'].dt.hour
        self.df['day'] = self.df['datetime'].dt.day_name()
        
        # Create pivot table for heatmap
        pivot_table = pd.crosstab(self.df['day'], self.df['hour'])
        
        # Create heatmap with Plotly
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale='Viridis'
        ))
        
        fig.update_layout(
            title='Tweet Time Distribution Heatmap',
            title_x=0.5,
            xaxis_title='Hour of Day',
            yaxis_title='Day of Week',
            template='plotly_dark'
        )
        
        fig.write_html(f"{self.output_dir}/time_distribution.html")
        print("Time distribution heatmap created!")

    def create_special_svg(self):
        """Top 20 Most Engaging Tweets Network Graph"""
        # Create special network graph with NetworkX and Plotly
        top_tweets = self.df.nlargest(20, ['likes', 'reposts']).copy()
        
        # Normalize the values for better visualization
        top_tweets['size'] = (top_tweets['likes'] + top_tweets['reposts']) / 1000
        
        fig = go.Figure()
        
        # Add scatter plot for tweets
        fig.add_trace(go.Scatter(
            x=top_tweets['likes'],
            y=top_tweets['reposts'],
            mode='markers+text',
            marker=dict(
                size=top_tweets['size'],
                color=top_tweets['views'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Views')
            ),
            text=top_tweets['username'],
            hovertext=top_tweets['text'],
            textposition="top center"
        ))
        
        fig.update_layout(
            title='Top 20 Most Engaging Tweets',
            title_x=0.5,
            xaxis_title='Likes',
            yaxis_title='Reposts',
            template='plotly_dark',
            showlegend=False,
            height=800
        )
        
        fig.write_html(f"{self.output_dir}/special_network.html")
        print("Special network graph created!")

    def generate_all_visualizations(self):
        """Generate all visualizations"""
        print("Starting data visualization...")
        self.load_latest_data()
        self.create_engagement_scatter()
        self.create_top_users_bar()
        self.create_time_distribution()
        self.create_special_svg()
        print(f"\nAll graphs have been saved to {self.output_dir} directory!")
        print("You can open the graphs in your web browser to examine them.")

if __name__ == "__main__":
    visualizer = TweetVisualizer()
    visualizer.generate_all_visualizations()
