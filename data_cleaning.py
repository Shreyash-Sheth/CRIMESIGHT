import os
import requests
from sodapy import Socrata
import pandas as pd
import sqlite3
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

class DataCleaningPipeline:
    def __init__(self, db_name='crime_data.db'):
        self.app_token = os.getenv('9qtnj62620uvn8aqz1p7kjlte')
        self.username = os.getenv('123104372@umail.ucc.ie')
        self.password = os.getenv('daqkoh-9rydby-xepSep')
        self.db_name = db_name
        self.client = Socrata("data.cityofchicago.org", self.app_token, username=self.username, password=self.password)
        
    def fetch_records_in_date_range(self, dataset_identifier, start_date, end_date, page_size=100000):
        records_fetched = 0
        start_offset = 0
        all_records = []
        while True:
            results = self.client.get(
                dataset_identifier, 
                limit=page_size, 
                offset=start_offset, 
                where=f"date between '{start_date}' and '{end_date}'",
                order='date DESC'
            )
            if not results:
                break
            all_records.extend(results)
            records_fetched += len(results)
            start_offset += page_size
        return all_records
    
    def clean_data(self, df):
        columns_to_keep = ['id', 'date', 'primary_type', 'description', 'location_description', 'beat', 'arrest', 'domestic', 'district', 'latitude', 'longitude']
        df = df[columns_to_keep].copy()  # Create a copy of the DataFrame

        df.loc[:, 'arrest'] = df['arrest'].astype(int)
        df.loc[:, 'domestic'] = df['domestic'].astype(int)
        df.loc[:, 'district'] = df['district'].astype(int)
        df[['date', 'time']] = df['date'].str.split('T', expand=True)

        district_to_area = {
            2: 'Area Central', 3: 'Area Central', 7: 'Area Central', 8: 'Area Central', 9: 'Area Central',
            4: 'Area South', 5: 'Area South', 6: 'Area South',
            1: 'Area North', 10: 'Area North', 11: 'Area North', 12: 'Area North', 14: 'Area North', 15: 'Area North', 16: 'Area North', 17: 'Area North', 18: 'Area North', 19: 'Area North', 20: 'Area North', 22: 'Area North', 24: 'Area North', 25: 'Area North'
        }
        df['area'] = df['district'].map(district_to_area)
        return df
    
    def save_to_database(self, df):
        conn = sqlite3.connect(self.db_name)
        df.to_sql('crimes', conn, if_exists='replace', index=False)
        conn.close()
    
    def update_database(self, new_data):
        conn = sqlite3.connect(self.db_name)
        existing_data = pd.read_sql_query("SELECT * FROM crimes", conn)
        combined_data = pd.concat([existing_data, new_data]).drop_duplicates(subset=['id'])
        combined_data.to_sql('crimes', conn, if_exists='replace', index=False)
        conn.close()
    
    def fetch_initial_data(self, dataset_identifier, start_date, end_date):
        records = self.fetch_records_in_date_range(dataset_identifier, start_date, end_date)
        df = pd.DataFrame(records)
        cleaned_df = self.clean_data(df)
        self.save_to_database(cleaned_df)
    
    def add_new_data(self, dataset_identifier, start_date, end_date):
        records = self.fetch_records_in_date_range(dataset_identifier, start_date, end_date)
        df = pd.DataFrame(records)
        cleaned_df = self.clean_data(df)
        self.update_database(cleaned_df)
