import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

class NewsAnalyzer:
    def __init__(self, csv_file):
        print(f"Analyzing {csv_file}...")
        self.df = pd.read_csv(csv_file)
        print(f"Loaded {len(self.df)} articles")
        
        # Renk paleti tanımla
        self.colors = px.colors.qualitative.Set3
        
    def create_crime_distribution(self):
        """Enhanced crime type distribution visualization"""
        crime_stats = self.df['Crime_Type'].value_counts()
        
        fig = go.Figure()
        
        # Ana pasta grafik
        fig.add_trace(go.Pie(
            labels=crime_stats.index,
            values=crime_stats.values,
            hole=0.6,
            textinfo='label+percent',
            textfont=dict(size=14),
            marker=dict(colors=self.colors, line=dict(color='white', width=2))
        ))
        
        # Merkeze toplam sayıyı ekle
        fig.add_annotation(
            text=f'Total<br>{len(self.df)}<br>Articles',
            x=0.5, y=0.5,
            font=dict(size=20, color='black', family='Arial Black'),
            showarrow=False
        )
        
        fig.update_layout(
            title={
                'text': 'Crime Type Distribution Analysis',
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=24, color='black')
            },
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            width=1000,
            height=800,
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        
        return fig

    def create_country_analysis(self):
        """Enhanced country distribution visualization"""
        country_stats = self.df['Country'].value_counts()
        
        fig = go.Figure()
        
        # Bar grafik
        fig.add_trace(go.Bar(
            x=country_stats.index,
            y=country_stats.values,
            text=country_stats.values,
            textposition='auto',
            marker=dict(
                color=self.colors,
                line=dict(color='white', width=1.5)
            )
        ))
        
        # Trend çizgisi
        fig.add_trace(go.Scatter(
            x=country_stats.index,
            y=country_stats.values,
            mode='lines',
            line=dict(color='red', width=2),
            name='Trend'
        ))
        
        fig.update_layout(
            title={
                'text': 'Geographical Distribution of Crime News',
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=24, color='black')
            },
            xaxis_title="Country",
            yaxis_title="Number of Articles",
            xaxis={'categoryorder':'total descending'},
            width=1200,
            height=700,
            paper_bgcolor='white',
            plot_bgcolor='rgba(240,240,240,0.5)',
            showlegend=True
        )
        
        return fig

    def create_publisher_analysis(self):
        """Enhanced publisher vs crime type analysis"""
        # Top 15 publisher'ı al
        top_publishers = self.df['Publisher'].value_counts().head(15).index
        filtered_df = self.df[self.df['Publisher'].isin(top_publishers)]
        
        publisher_crime = pd.crosstab(filtered_df['Publisher'], filtered_df['Crime_Type'])
        
        fig = go.Figure()
        
        # Heatmap
        fig.add_trace(go.Heatmap(
            z=publisher_crime.values,
            x=publisher_crime.columns,
            y=publisher_crime.index,
            colorscale='Viridis',
            text=publisher_crime.values,
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title={
                'text': 'Publisher vs Crime Type Analysis',
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=24, color='black')
            },
            width=1200,
            height=800,
            xaxis_title="Crime Type",
            yaxis_title="Publisher",
            paper_bgcolor='white'
        )
        
        return fig

    def analyze(self):
        """Create enhanced analysis and save reports"""
        # Klasörü oluştur
        if not os.path.exists('analysis_results'):
            os.makedirs('analysis_results')
        
        # Create and save enhanced visualizations
        self.create_crime_distribution().write_html(f"analysis_results/crime_distribution.html")
        self.create_country_analysis().write_html(f"analysis_results/country_distribution.html")
        self.create_publisher_analysis().write_html(f"analysis_results/publisher_analysis.html")

        # Create detailed executive summary
        with open(f"analysis_results/executive_summary.txt", 'w') as f:
            f.write("CRIME NEWS ANALYSIS EXECUTIVE SUMMARY\n")
            f.write("====================================\n\n")
            
            # Overview Section
            f.write("📊 EXECUTIVE OVERVIEW\n")
            f.write("--------------------\n")
            total_articles = len(self.df)
            f.write(f"Total Articles Analyzed: {total_articles:,}\n")
            f.write(f"Analysis Period: {self.df['Published_Date'].min()} to {self.df['Published_Date'].max()}\n")
            f.write(f"Coverage: {self.df['Country'].nunique()} countries, {self.df['Publisher'].nunique()} publishers\n\n")
            
            # Key Findings
            f.write("🔍 KEY FINDINGS\n")
            f.write("-------------\n")
            
            # Crime Type Analysis
            crime_stats = self.df['Crime_Type'].value_counts()
            f.write("\n1. Crime Type Distribution:\n")
            for crime_type, count in crime_stats.items():
                percentage = (count / total_articles) * 100
                f.write(f"   • {crime_type}: {count:,} articles ({percentage:.1f}%)\n")
            
            # Most Active Publishers
            f.write("\n2. Top 5 Most Active Publishers:\n")
            publisher_stats = self.df['Publisher'].value_counts().head(5)
            for publisher, count in publisher_stats.items():
                percentage = (count / total_articles) * 100
                f.write(f"   • {publisher}: {count:,} articles ({percentage:.1f}%)\n")
            
            # Geographical Distribution
            f.write("\n3. Geographical Coverage:\n")
            country_stats = self.df['Country'].value_counts()
            for country, count in country_stats.items():
                percentage = (count / total_articles) * 100
                f.write(f"   • {country}: {count:,} articles ({percentage:.1f}%)\n")
            
            # Recommendations
            f.write("\n📋 RECOMMENDATIONS\n")
            f.write("-----------------\n")
            f.write("1. Focus Areas: Based on the analysis, consider increasing coverage of:\n")
            f.write("   • Underrepresented crime types\n")
            f.write("   • Geographical areas with lower coverage\n\n")
            
            f.write("2. Publisher Diversity: Consider expanding sources to include:\n")
            f.write("   • More local news outlets\n")
            f.write("   • International perspectives\n\n")
            
            # Interactive Reports
            f.write("\n📊 INTERACTIVE VISUALIZATIONS\n")
            f.write("---------------------------\n")
            f.write("1. crime_distribution.html - Detailed breakdown of crime types\n")
            f.write("2. country_distribution.html - Geographical distribution analysis\n")
            f.write("3. publisher_analysis.html - Publisher coverage patterns\n")

        print("\nAnalysis complete! Enhanced reports saved in 'analysis_results' directory:")
        print("1. crime_distribution.html - Interactive crime type visualization")
        print("2. country_distribution.html - Enhanced geographical analysis")
        print("3. publisher_analysis.html - Publisher coverage patterns")
        print("4. executive_summary.txt - Detailed analysis report")

if __name__ == "__main__":
    analyzer = NewsAnalyzer('crime_news_20240729_20241126.csv')
    analyzer.analyze() 