import pandas as pd
import numpy as np
import sqlite3
from sklearn.cluster import DBSCAN
import folium
import seaborn as sns
import geopandas as gpd
import pyproj
import matplotlib.pyplot as plt
from pandas.plotting import table
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

    # Calculate top crime type for each cluster
    top_crime_types = cluster_results.groupby('cluster')['primary_type'].agg(lambda x: x.mode()[0] if not x.mode().empty else 'N/A')
    cluster_results = cluster_results.merge(top_crime_types.rename('top_crime_type'), on='cluster', how='left')
    
    return cluster_results

# Updated function to create map with cluster sizes
def create_map_with_cluster_size(data, cluster_results, beat_boundaries):
    map = folium.Map(location=[data['latitude'].mean(), data['longitude'].mean()], zoom_start=11)
    district_colors = sns.color_palette('hsv', len(data['district'].unique())).as_hex()
    
    # Calculate cluster sizes
    cluster_sizes = cluster_results['cluster'].value_counts().to_dict()
    
    for idx, row in cluster_results.iterrows():
        if row['cluster'] != -1:
            district_index = list(data['district'].unique()).index(row['district'])
            cluster_color = district_colors[district_index]
            cluster_size = cluster_sizes[row['cluster']] / 3
            top_crime_type = row['top_crime_type']
            folium.CircleMarker(
                [row['latitude'], row['longitude']],
                radius=3 + cluster_size / 20,  # Adjust size based on cluster size
                color=cluster_color,
                fill=True,
                fill_color=cluster_color,
                fill_opacity=0.1,
                popup=f'District: {row["district"]}, Cluster: {row["cluster"]}, Size: {cluster_size}, Top Crime: {top_crime_type}'
            ).add_to(map)
    
    for idx, row in beat_boundaries.iterrows():
        folium.GeoJson(row['geometry']).add_to(map)
    
    map.save('Chicago_crime_clusters_with_cluster_size.html')
    webbrowser.open('Chicago_crime_clusters_with_cluster_size.html')

def run_analysis(db_path):
    eps = 0.5  # Adjust based on your data
    min_samples = 7  # Adjust based on your data
    data = load_data(db_path)
    data = convert_to_utm(data)
    cluster_results = apply_dbscan(data, eps, min_samples)
    beat_boundaries = gpd.read_file('boundaries/geo_export_0b908a58-99fc-452e-866d-07ad3860c3ca.shp')
    create_map_with_cluster_size(data, cluster_results, beat_boundaries)
