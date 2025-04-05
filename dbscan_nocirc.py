import pandas as pd
import numpy as np
import sqlite3
from sklearn.cluster import DBSCAN
import folium
from folium.plugins import MarkerCluster
import seaborn as sns
import geopandas as gpd
import pyproj
import webbrowser

# Function to load data from the database
def load_data(db_path):
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM crimes"
    data = pd.read_sql_query(query, conn)
    conn.close()
    data['datetime'] = pd.to_datetime(data['date'] + ' ' + data['time'])
    return data

# Function to convert latitude and longitude to UTM coordinates
def convert_to_utm(data):
    data['latitude'] = pd.to_numeric(data['latitude'], errors='coerce')
    data['longitude'] = pd.to_numeric(data['longitude'], errors='coerce')
    data = data.dropna(subset=['latitude', 'longitude'])
    
    proj_utm = pyproj.Proj(proj='utm', zone=16, ellps='WGS84', south=False)
    data['utm_x'], data['utm_y'] = proj_utm(data['longitude'].values, data['latitude'].values)
    return data

# Function to apply DBSCAN clustering
def apply_dbscan(data, eps, min_samples):
    cluster_results = pd.DataFrame()
    for district in data['district'].unique():
        subset = data[data['district'] == district]
        coordinates = subset[['utm_x', 'utm_y']].values
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        subset['cluster'] = dbscan.fit_predict(coordinates)
        cluster_results = pd.concat([cluster_results, subset])
    return cluster_results

# Updated function to create map with constant size clusters
def create_map_with_cluster_size(data, cluster_results, beat_boundaries):
    map = folium.Map(location=[data['latitude'].mean(), data['longitude'].mean()], zoom_start=11)
    district_colors = sns.color_palette('hsv', len(data['district'].unique())).as_hex()
    
    # Calculate cluster sizes
    cluster_sizes = cluster_results['cluster'].value_counts().to_dict()
    
    marker_cluster = MarkerCluster().add_to(map)
    
    for idx, row in cluster_results.iterrows():
        if row['cluster'] != -1:
            district_index = list(data['district'].unique()).index(row['district'])
            cluster_color = district_colors[district_index]
            cluster_size = cluster_sizes[row['cluster']]
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                icon=folium.DivIcon(html=f"""
                    <div style="background-color:{cluster_color};width:20px;height:20px;border-radius:50%;
                    opacity:0.4;border:3px solid {cluster_color};">
                    </div>"""
                )
            ).add_to(marker_cluster)
    
    for idx, row in beat_boundaries.iterrows():
        folium.GeoJson(row['geometry']).add_to(map)
    
    map.save('Chicago_crime_clusters_with_constant_size.html')
    webbrowser.open('Chicago_crime_clusters_with_constant_size.html')

