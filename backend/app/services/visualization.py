"""
WeatherWise Data Visualization Utilities
Creates charts and graphs for weather data analysis
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure matplotlib for better plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class WeatherVisualization:
    """Create visualization for weather data analysis."""

    def __init__(self):
        """Initialize visualization service."""
        # Database connection
        self.DATABASE_URL = os.getenv('DATABASE_URL')
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required for production")
        self.engine = create_engine(self.DATABASE_URL)

        # Create output directory for charts
        self.output_dir = "charts"
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info("Weather visualization service initialized")

    def create_temperature_trend(self, location: str, days: int = 7) -> str:
        """Create temperature trend chart for a location.
        
        Args:
            location: Location to analyze
            days: Number of days to include

        Returns:
            Path to saved chart file
        """
        # Query recent temperature data
        query = f"""
        SELECT timestamp, temperature, weather_condition
        FROM current_weather 
        WHERE location = '{location}'
        AND timestamp >= NOW() - INTERVAL '{days} days'
        ORDER BY timestamp
        """

        try:
            df = pd.read_sql(query, self.engine)
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return None
        
        if df.empty:
            logger.warning(f"No temperature data found for {location}")
            return None
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 6))

        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Plot temperature line
        ax.plot(df['timestamp'], df['temperature'],
                linewidth=2, marker='o', markersize=4, label='Temperature')
        
        # Add trend line
        z = np.polyfit(range(len(df)), df['temperature'], 1)
        p = np.poly1d(z)
        ax.plot(df['timestamp'], p(range(len(df))), 
                "--", alpha=0.7, color='red', label='Trend')
        
        # Formatting
        ax.set_title(f'Temperature Trend - {location} (Last {days} days)', 
                    fontsize=16, fontweight='bold')
        ax.set_xlabel('Date & Time', fontsize=12)
        ax.set_ylabel('Temperature (°C)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        plt.xticks(rotation=45)
        
        # Add statistics box
        temp_stats = f"Min: {df['temperature'].min():.1f}°C\n" \
                    f"Max: {df['temperature'].max():.1f}°C\n" \
                    f"Avg: {df['temperature'].mean():.1f}°C"
        
        ax.text(0.02, 0.98, temp_stats, transform=ax.transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        # Save chart
        filename = f"{self.output_dir}/temperature_trend_{location.replace(',', '_')}_{days}d.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✅ Temperature trend chart saved: {filename}")
        return filename
    
    def create_weather_conditions_pie(self, location: str, days: int = 7) -> str:
        """Create pie chart of weather conditions distribution.
        
        Args:
            location: Location to analyze
            days: Number of days to include
            
        Returns:
            Path to saved chart file
        """
        query = f"""
        SELECT weather_condition, COUNT(*) as count
        FROM current_weather 
        WHERE location = '{location}'
        AND timestamp >= NOW() - INTERVAL '{days} days'
        GROUP BY weather_condition
        ORDER BY count DESC
        """
        
        try:
            df = pd.read_sql(query, self.engine)
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return None
        
        if df.empty:
            logger.warning(f"No weather condition data found for {location}")
            return None
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create pie chart with custom colors
        colors = sns.color_palette("Set3", len(df))
        wedges, texts, autotexts = ax.pie(df['count'], labels=df['weather_condition'], 
                                         autopct='%1.1f%%', startangle=90, colors=colors)
        
        # Enhance text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(f'Weather Conditions Distribution - {location} (Last {days} days)', 
                    fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        # Save chart
        filename = f"{self.output_dir}/weather_conditions_{location.replace(',', '_')}_{days}d.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✅ Weather conditions chart saved: {filename}")
        return filename
    
    def create_multi_location_comparison(self, locations: List[str], days: int = 3) -> str:
        """Create comparison chart for multiple locations.
        
        Args:
            locations: List of locations to compare
            days: Number of days to include
            
        Returns:
            Path to saved chart file
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        location_data = {}
        
        for location in locations:
            query = f"""
            SELECT timestamp, temperature, humidity, pressure, wind_speed
            FROM current_weather 
            WHERE location = '{location}'
            AND timestamp >= NOW() - INTERVAL '{days} days'
            ORDER BY timestamp
            """
            
            df = pd.read_sql(query, self.engine)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                location_data[location] = df
        
        if not location_data:
            logger.warning("No data found for any location")
            return None
        
        # Temperature comparison
        for location, df in location_data.items():
            ax1.plot(df['timestamp'], df['temperature'], 
                    marker='o', label=location, linewidth=2)
        ax1.set_title('Temperature Comparison', fontweight='bold')
        ax1.set_ylabel('Temperature (°C)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Humidity comparison
        for location, df in location_data.items():
            ax2.plot(df['timestamp'], df['humidity'], 
                    marker='s', label=location, linewidth=2)
        ax2.set_title('Humidity Comparison', fontweight='bold')
        ax2.set_ylabel('Humidity (%)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Pressure comparison
        for location, df in location_data.items():
            ax3.plot(df['timestamp'], df['pressure'], 
                    marker='^', label=location, linewidth=2)
        ax3.set_title('Pressure Comparison', fontweight='bold')
        ax3.set_ylabel('Pressure (hPa)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.set_xlabel('Date & Time')
        
        # Wind speed comparison
        for location, df in location_data.items():
            ax4.plot(df['timestamp'], df['wind_speed'], 
                    marker='d', label=location, linewidth=2)
        ax4.set_title('Wind Speed Comparison', fontweight='bold')
        ax4.set_ylabel('Wind Speed (km/h)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_xlabel('Date & Time')
        
        # Format dates on x-axes
        for ax in [ax1, ax2, ax3, ax4]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            ax.tick_params(axis='x', rotation=45)
        
        plt.suptitle(f'Multi-Location Weather Comparison (Last {days} days)', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # Save chart
        locations_str = "_".join([loc.replace(',', '_') for loc in locations])
        filename = f"{self.output_dir}/multi_location_comparison_{locations_str}_{days}d.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✅ Multi-location comparison chart saved: {filename}")
        return filename
    
    def create_risk_indicators_dashboard(self, location: str, days: int = 2) -> str:
        """Create dashboard showing risk indicators for DRRM.
        
        Args:
            location: Location to analyze
            days: Number of days to include
            
        Returns:
            Path to saved dashboard file
        """
        query = f"""
        SELECT timestamp, temperature, humidity, pressure, wind_speed, 
               weather_condition, weather_description
        FROM current_weather 
        WHERE location = '{location}'
        AND timestamp >= NOW() - INTERVAL '{days} days'
        ORDER BY timestamp
        """
        
        df = pd.read_sql(query, self.engine)
        
        if df.empty:
            logger.warning(f"No data found for {location}")
            return None
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create dashboard
        fig = plt.figure(figsize=(16, 12))
        
        # Temperature risk (extreme temperatures)
        ax1 = plt.subplot(3, 2, 1)
        temp_colors = ['red' if t > 35 or t < 15 else 'orange' if t > 32 or t < 18 else 'green' 
                      for t in df['temperature']]
        ax1.scatter(df['timestamp'], df['temperature'], c=temp_colors, s=50, alpha=0.7)
        ax1.axhline(y=35, color='red', linestyle='--', alpha=0.7, label='High Risk (>35°C)')
        ax1.axhline(y=15, color='red', linestyle='--', alpha=0.7, label='Low Risk (<15°C)')
        ax1.set_title('Temperature Risk Assessment', fontweight='bold')
        ax1.set_ylabel('Temperature (°C)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Pressure risk (rapid changes indicate storms)
        ax2 = plt.subplot(3, 2, 2)
        pressure_risk = df['pressure'].diff().abs() > 5  # Rapid pressure change
        colors = ['red' if risk else 'green' for risk in pressure_risk]
        ax2.scatter(df['timestamp'], df['pressure'], c=colors, s=50, alpha=0.7)
        ax2.set_title('Pressure Change Risk (Rapid changes = Storm risk)', fontweight='bold')
        ax2.set_ylabel('Pressure (hPa)')
        ax2.grid(True, alpha=0.3)
        
        # Humidity risk
        ax3 = plt.subplot(3, 2, 3)
        humidity_colors = ['red' if h > 85 else 'orange' if h > 75 else 'green' 
                          for h in df['humidity']]
        ax3.scatter(df['timestamp'], df['humidity'], c=humidity_colors, s=50, alpha=0.7)
        ax3.axhline(y=85, color='red', linestyle='--', alpha=0.7, label='High Risk (>85%)')
        ax3.set_title('Humidity Risk Assessment', fontweight='bold')
        ax3.set_ylabel('Humidity (%)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Wind risk
        ax4 = plt.subplot(3, 2, 4)
        wind_colors = ['red' if w > 60 else 'orange' if w > 40 else 'yellow' if w > 25 else 'green' 
                      for w in df['wind_speed']]
        ax4.scatter(df['timestamp'], df['wind_speed'], c=wind_colors, s=50, alpha=0.7)
        ax4.axhline(y=60, color='red', linestyle='--', alpha=0.7, label='Typhoon Risk (>60 km/h)')
        ax4.axhline(y=40, color='orange', linestyle='--', alpha=0.7, label='Strong Wind (>40 km/h)')
        ax4.set_title('Wind Speed Risk Assessment', fontweight='bold')
        ax4.set_ylabel('Wind Speed (km/h)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Risk summary table
        ax5 = plt.subplot(3, 1, 3)
        ax5.axis('off')
        
        # Calculate risk indicators
        temp_risk_count = sum(1 for t in df['temperature'] if t > 35 or t < 15)
        pressure_risk_count = sum(pressure_risk)
        humidity_risk_count = sum(1 for h in df['humidity'] if h > 85)
        wind_risk_count = sum(1 for w in df['wind_speed'] if w > 40)
        
        risk_summary = [
            ['Risk Factor', 'High Risk Count', 'Latest Value', 'Status'],
            ['Temperature Extremes', temp_risk_count, f"{df['temperature'].iloc[-1]:.1f}°C", 
             '🔴 HIGH' if df['temperature'].iloc[-1] > 35 or df['temperature'].iloc[-1] < 15 else '🟢 NORMAL'],
            ['Pressure Changes', pressure_risk_count, f"{df['pressure'].iloc[-1]:.1f} hPa", 
             '🔴 HIGH' if pressure_risk.iloc[-1] else '🟢 NORMAL'],
            ['High Humidity', humidity_risk_count, f"{df['humidity'].iloc[-1]}%", 
             '🔴 HIGH' if df['humidity'].iloc[-1] > 85 else '🟢 NORMAL'],
            ['Strong Winds', wind_risk_count, f"{df['wind_speed'].iloc[-1]:.1f} km/h", 
             '🔴 HIGH' if df['wind_speed'].iloc[-1] > 40 else '🟢 NORMAL']
        ]
        
        table = ax5.table(cellText=risk_summary[1:], colLabels=risk_summary[0],
                         cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        
        # Color code the status column
        for i in range(1, len(risk_summary)):
            if '🔴' in risk_summary[i][3]:
                table[(i, 3)].set_facecolor('#ffcccc')
            else:
                table[(i, 3)].set_facecolor('#ccffcc')
        
        plt.suptitle(f'DRRM Risk Indicators Dashboard - {location} (Last {days} days)', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # Save dashboard
        filename = f"{self.output_dir}/risk_dashboard_{location.replace(',', '_')}_{days}d.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✅ Risk dashboard saved: {filename}")
        return filename
    
    def generate_all_charts(self, locations: List[str] = None, days: int = 3) -> Dict[str, str]:
        """Generate all available charts for given locations.
        
        Args:
            locations: List of locations (default: Manila, Cebu, Davao)
            days: Number of days to include
            
        Returns:
            Dictionary of chart types and their file paths
        """
        if locations is None:
            locations = ["Manila,PH", "Cebu,PH", "Davao,PH"]
        
        charts = {}
        
        logger.info(f"📊 Generating all charts for {len(locations)} locations...")
        
        # Generate charts for each location
        for location in locations:
            # Temperature trends
            temp_chart = self.create_temperature_trend(location, days)
            if temp_chart:
                charts[f"temperature_trend_{location}"] = temp_chart
            
            # Weather conditions
            conditions_chart = self.create_weather_conditions_pie(location, days)
            if conditions_chart:
                charts[f"weather_conditions_{location}"] = conditions_chart
            
            # Risk dashboard
            risk_chart = self.create_risk_indicators_dashboard(location, days)
            if risk_chart:
                charts[f"risk_dashboard_{location}"] = risk_chart
        
        # Multi-location comparison
        comparison_chart = self.create_multi_location_comparison(locations, days)
        if comparison_chart:
            charts["multi_location_comparison"] = comparison_chart
        
        logger.info(f"✅ Generated {len(charts)} charts successfully!")
        
        return charts


# Example usage and testing
if __name__ == "__main__":
    # Test visualization service
    viz = WeatherVisualization()
    
    print("📊 Testing WeatherWise Visualization Service")
    print("=" * 50)
    
    # Generate all charts
    charts = viz.generate_all_charts(days=2)
    
    print(f"\n🎨 Generated Charts:")
    for chart_type, filepath in charts.items():
        print(f"   📈 {chart_type}: {filepath}")
    
    print(f"\n✅ All charts saved to '{viz.output_dir}/' directory")