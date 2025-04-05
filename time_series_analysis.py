import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
import holidays
import seaborn as sns
import matplotlib.dates as mdates

# Set the Seaborn theme
sns.set_theme(style="whitegrid")

def fetch_data_from_db(db_path, query):
    conn = sqlite3.connect(db_path)
    data = pd.read_sql_query(query, conn)
    conn.close()
    return data

def run_time_series_analysis(db_path):
    figures = []
    
    # Fetch the data for training (2014-2023)
    query_train = """
    SELECT *
    FROM crimes
    WHERE date BETWEEN '2014-01-01' AND '2023-12-31'
    """
    crime_data_train = fetch_data_from_db(db_path, query_train)

    # Fetch the data for validation (2024)
    query_validate = """
    SELECT *
    FROM crimes
    WHERE date BETWEEN '2024-01-01' AND '2024-06-28'
    """
    crime_data_validate = fetch_data_from_db(db_path, query_validate)

    # Ensure the date column is in datetime format
    crime_data_train['date'] = pd.to_datetime(crime_data_train['date'])
    crime_data_validate['date'] = pd.to_datetime(crime_data_validate['date'])

    # Generate US holidays
    us_holidays = holidays.US(state='IL')

    # Create a DataFrame for holidays
    holiday_dates = pd.DataFrame(list(us_holidays.items()), columns=['ds', 'holiday'])
    holiday_dates['ds'] = pd.to_datetime(holiday_dates['ds'])

    # Get the unique areas from the dataset and filter out the 'None' area
    unique_areas = [area for area in crime_data_train['area'].unique() if area]

    # Define colors for each area
    colors = sns.color_palette('husl', n_colors=len(unique_areas))
    forecast_color = 'black'  # Color for forecasted data

    # Initialize lists to store combined data
    combined_area_data = []
    combined_forecast_data = []

    # Loop through each area
    for i, area in enumerate(unique_areas):
        # Filter the data by area
        area_train_data = crime_data_train[crime_data_train['area'] == area]
        area_validate_data = crime_data_validate[crime_data_validate['area'] == area]

        # Prepare the data for Prophet
        area_train_daily = area_train_data.groupby(area_train_data['date'].dt.date).size().reset_index(name='count')
        area_train_daily.columns = ['ds', 'y']

        # Check if there is enough data to fit the model
        if area_train_daily.shape[0] < 2:
            print(f"Not enough data to train the model for area: {area}")
            continue

        # Convert ds column to datetime
        area_train_daily['ds'] = pd.to_datetime(area_train_daily['ds'])

        # Initialize and fit the Prophet model
        prophet_model = Prophet(holidays=holiday_dates)
        prophet_model.fit(area_train_daily)

        # Create future dataframe to hold the dates for which we want a forecast
        future_dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        future = pd.DataFrame(future_dates, columns=['ds'])

        # Make predictions
        forecast = prophet_model.predict(future)

        # Add area identifier
        area_train_daily['area'] = area
        forecast['area'] = area

        # Append to combined data
        combined_area_data.append(area_train_daily)
        combined_forecast_data.append(forecast)

    # Concatenate combined data
    combined_area_data = pd.concat(combined_area_data)
    combined_forecast_data = pd.concat(combined_forecast_data)

    # Plot the forecast with trend line from 2014 to 2024 for each area
    fig1, ax1 = plt.subplots(figsize=(10, 4))  # Reduced size

    # Plot historical and forecasted values with trend line for each area
    for i, area in enumerate(unique_areas):
        area_train_daily = combined_area_data[combined_area_data['area'] == area]
        forecast = combined_forecast_data[combined_forecast_data['area'] == area]

        ax1.plot(area_train_daily['ds'], area_train_daily['y'], label=f'Historical {area}', color=colors[i], marker='.')
        ax1.plot(forecast['ds'], forecast['yhat'], label=f'Forecast {area}', linestyle='--', color=forecast_color, marker='x')

    # Set x-ticks to a readable format
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_minor_locator(mdates.MonthLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)

    ax1.set_title('Historical and Forecasted Crimes by Area (2014-2024)')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Number of Crimes')
    ax1.legend()
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

    plt.tight_layout()
    figures.append(fig1)

    # Plot the actual monthly crime counts for each area
    fig2, ax2 = plt.subplots(figsize=(10, 4))  # Reduced size

    # Calculate month-over-month changes and aggregate monthly crime data for each area
    for i, area in enumerate(unique_areas):
        area_train_daily = combined_area_data[combined_area_data['area'] == area]
        forecast = combined_forecast_data[combined_forecast_data['area'] == area]

        area_train_daily['month'] = area_train_daily['ds'].dt.to_period('M')
        forecast['month'] = forecast['ds'].dt.to_period('M')

        monthly_crime_data = area_train_daily.groupby('month')['y'].sum().reset_index(name='monthly_count')
        monthly_forecast_data = forecast.groupby('month')['yhat'].sum().reset_index(name='monthly_count')

        monthly_data = pd.concat([monthly_crime_data, monthly_forecast_data[monthly_forecast_data['month'].dt.year == 2024]], ignore_index=True)

        # Convert 'month' to datetime for proper plotting
        monthly_data['month'] = monthly_data['month'].dt.to_timestamp()

        ax2.plot(monthly_data['month'], monthly_data['monthly_count'], label=f'{area} Historical', color=colors[i])
        ax2.plot(monthly_forecast_data['month'].dt.to_timestamp(), monthly_forecast_data['monthly_count'], label=f'{area} Forecast', linestyle='--', color=forecast_color)

    # Set x-ticks to a readable format
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_minor_locator(mdates.MonthLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)

    ax2.set_title('Monthly Crime Counts by Area (2014-2024)')
    ax2.set_xlabel('Month')
    ax2.set_ylabel('Number of Crimes')
    ax2.legend()
    ax2.grid(True, which='both', linestyle='--', linewidth=0.5)

    plt.tight_layout()
    figures.append(fig2)

    return figures

if __name__ == "__main__":
    db_path = 'TEST.db'  # Default database path
    figures = run_time_series_analysis(db_path)
    for fig in figures:
        fig.show()
