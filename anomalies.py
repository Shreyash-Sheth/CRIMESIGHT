# anomalies.py

import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
import folium
from folium.plugins import MarkerCluster
import geopandas as gpd
import webbrowser
import os

# Connect to the SQLite database
db_path = 'crime_data.db'  # Replace with your actual path
conn = sqlite3.connect(db_path)

# Load the data from the 'crimes' table
crimes_df = pd.read_sql_query("SELECT * FROM crimes", conn)

# Feature Engineering: Extract date components and aggregate data by date
crimes_df['date'] = pd.to_datetime(crimes_df['date'])
crime_counts = crimes_df.groupby('date').size().reset_index(name='count')

# Train Isolation Forest Model
model = IsolationForest(contamination=0.01, random_state=42)
crime_counts['anomaly'] = model.fit_predict(crime_counts[['count']])

# Separate high anomalies
high_anomalies = crime_counts[(crime_counts['anomaly'] == -1) & (crime_counts['count'] > crime_counts['count'].mean())]

# Functions to plot each subplot
def plot_high_anomalies(ax):
    ax.plot(crime_counts['date'], crime_counts['count'], label='Daily Crime Counts', color='blue')
    ax.scatter(high_anomalies['date'], high_anomalies['count'], color='red', label='High Anomalies')
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Crimes')
    ax.set_title('High Anomalies in Daily Crime Counts')
    ax.legend()

def plot_monthly_anomalies(ax):
    anomalies_df = pd.merge(crimes_df, crime_counts, on='date')
    high_anomalies_df = anomalies_df[(anomalies_df['anomaly'] == -1) & (anomalies_df['count'] > anomalies_df['count'].mean())]
    high_anomalies_df['month'] = high_anomalies_df['date'].dt.month
    monthly_anomalies = high_anomalies_df['month'].value_counts().sort_index().reset_index()
    monthly_anomalies.columns = ['month', 'count']
    ax.bar(monthly_anomalies['month'], monthly_anomalies['count'], color='skyblue')
    ax.set_xlabel('Month')
    ax.set_ylabel('Number of Anomalies')
    ax.set_title('Monthly Anomalies')
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])

def plot_weekly_anomalies(ax):
    anomalies_df = pd.merge(crimes_df, crime_counts, on='date')
    high_anomalies_df = anomalies_df[(anomalies_df['anomaly'] == -1) & (anomalies_df['count'] > anomalies_df['count'].mean())]
    high_anomalies_df['day_of_week'] = high_anomalies_df['date'].dt.dayofweek
    weekly_anomalies = high_anomalies_df['day_of_week'].value_counts().sort_index().reset_index()
    weekly_anomalies.columns = ['day_of_week', 'count']
    ax.bar(weekly_anomalies['day_of_week'], weekly_anomalies['count'], color='salmon')
    ax.set_xlabel('Day of the Week')
    ax.set_ylabel('Number of Anomalies')
    ax.set_title('Weekly Anomalies')
    ax.set_xticks(range(7))
    ax.set_xticklabels(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

def plot_crime_type_anomalies(ax):
    anomalies_df = pd.merge(crimes_df, crime_counts, on='date')
    high_anomalies_df = anomalies_df[(anomalies_df['anomaly'] == -1) & (anomalies_df['count'] > anomalies_df['count'].mean())]
    crime_type_anomalies = high_anomalies_df['primary_type'].value_counts().reset_index()
    crime_type_anomalies.columns = ['Crime Type', 'Count']
    ax.bar(crime_type_anomalies['Crime Type'], crime_type_anomalies['Count'], color='purple', alpha=0.7)
    ax.set_xlabel('Crime Type')
    ax.set_ylabel('Number of Anomalies')
    ax.set_title('Anomalies by Crime Type')
    ax.set_xticklabels(crime_type_anomalies['Crime Type'], rotation=90)

# Function to detect anomalies and plot them
def detect_anomalies():
    # Visualize high anomalies
    fig, axs = plt.subplots(2, 2, figsize=(21, 14))  # Adjusted size

    plot_high_anomalies(axs[0, 0])
    plot_monthly_anomalies(axs[0, 1])
    plot_weekly_anomalies(axs[1, 0])
    plot_crime_type_anomalies(axs[1, 1])

    plt.tight_layout()
    plt.savefig('anomalies_analysis.png')
    plt.show()

    anomalies_df = pd.merge(crimes_df, crime_counts, on='date')
    high_anomalies_df = anomalies_df[(anomalies_df['anomaly'] == -1) & (anomalies_df['count'] > anomalies_df['count'].mean())]
    high_anomalies_locations = high_anomalies_df[['latitude', 'longitude', 'primary_type', 'date', 'location_description', 'time']]

    # Convert latitude and longitude to numeric, handling errors
    high_anomalies_locations['latitude'] = pd.to_numeric(high_anomalies_locations['latitude'], errors='coerce')
    high_anomalies_locations['longitude'] = pd.to_numeric(high_anomalies_locations['longitude'], errors='coerce')

    # Drop rows with invalid latitude or longitude values
    high_anomalies_locations.dropna(subset=['latitude', 'longitude'], inplace=True)

    # Load the shape files for beat boundaries
    shapefile_path = 'boundaries/geo_export_0b908a58-99fc-452e-866d-07ad3860c3ca.shp'
    gdf = gpd.read_file(shapefile_path)

    # Create a base map
    map_center = [high_anomalies_locations['latitude'].mean(), high_anomalies_locations['longitude'].mean()]
    crime_map = folium.Map(location=map_center, zoom_start=11)

    # Add beat boundaries to the map
    folium.GeoJson(gdf).add_to(crime_map)

    # Add a marker cluster to the map
    marker_cluster = MarkerCluster().add_to(crime_map)

    # Add markers to the map with popups showing relevant details
    for idx, row in high_anomalies_locations.iterrows():
        popup_text = f"""
        <b>Crime Type:</b> {row['primary_type']}<br>
        <b>Date:</b> {row['date'].date()}<br>
        <b>Location:</b> {row['location_description']}<br>
        <b>Time:</b> {row['time']}
        """
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=popup_text
        ).add_to(marker_cluster)

    # Save the map to an HTML file
    map_path = 'crime_anomalies_map.html'  # Replace with your desired path
    crime_map.save(map_path)

    # Automatically open the HTML file in the default web browser
    webbrowser.open('file://' + os.path.realpath(map_path))

    print(f"Crime anomalies map saved to {map_path}")

    # Additional Data Distribution Analysis
    plt.figure(figsize=(14, 7))

    # Plot daily crime counts distribution
    plt.hist(crime_counts['count'], bins=50, color='blue', alpha=0.7)
    plt.xlabel('Number of Crimes')
    plt.ylabel('Frequency')
    plt.title('Distribution of Daily Crime Counts')

    plt.tight_layout()
    plt.savefig('data_distribution_analysis.png')
    plt.show()

# Run the anomaly detection when this script is executed
if __name__ == "__main__":
    detect_anomalies()
