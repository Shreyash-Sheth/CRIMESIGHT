# CRIMESIGHT

## Project Description
CrimeSight is a crime analytics platform designed to enhance law enforcement efficiency through predictive and descriptive analytics. By leveraging machine learning, clustering, and time series analysis, it identifies historical crime patterns and forecasts future hotspots, enabling proactive policing.

Key Features:
- Descriptive Analytics: Analyzes past crime data to detect trends.
- Predictive Analytics: Uses ML models to anticipate crime risks.
- Interactive Dashboards: User-friendly visualizations (built with Tableau) for easy interpretation.
- Technology Stack: Python, PostgreSQL, and cloud scalability ensure robust performance.

## Problem
Law enforcement agencies struggle to effectively predict and prevent crime due to reliance on reactive methods, fragmented data analysis, and outdated risk assessment models. Despite the availability of vast crime datasets, current solutions fail to integrate multiple data sources, account for dynamic urban factors, or provide real-time, actionable insights. Traditional approaches focus on historical crime patterns without leveraging advanced predictive analytics, resulting in inefficient resource allocation and delayed responses.
There is a critical need for a proactive, data-driven crime prediction system that combines machine learning, real-time analytics, and intuitive visualization to:
- Accurately forecast crime hotspots before incidents occur.
- Optimize police resource deployment for preventive policing.
- Enhance public safety through timely, evidence-based interventions.
- CrimeSight addresses these gaps by leveraging predictive analytics to transform raw crime data into actionable intelligence, enabling law enforcement to shift from reactive policing to proactive crime prevention—ultimately fostering safer communities.


## Dataset Description 
Source: Chicago Open Data Portal ("Crimes - 2001 to Present") (https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2/data_preview)

Time Period: January 1, 2013 – December 31, 2023 (11 years of crime records)

Key Columns Retained for Analysis:
- ID – Unique identifier for each crime incident.
- Date & Time – When the incident occurred.
- Primary Type – Crime category (e.g., theft, assault) based on Illinois Uniform Crime Reporting (IUCR) codes.
- Arrest – Binary indicator (yes/no) if an arrest was made.
- District – Police district where the incident occurred.
- Location – Latitude & longitude coordinates.
- Zip Code – Geographic area of the incident (auto-calculated).
- Domestic – Whether the incident was domestic-violence-related (per Illinois law).

Data Processing:
- Excluded Redundant Columns (e.g., year, X/Y coordinates) to streamline analysis.
- Focused on Spatial & Temporal Features (district, zip code, date/time) for hotspot modeling.
- Structured for Predictive Analytics – Cleaned and standardized for machine learning (e.g., Random Forest, time-series forecasting).

Purpose in CrimeSight:
- Trains predictive models to forecast crime trends.
- Powers descriptive dashboards (Tableau) for historical pattern analysis.
- Enables proactive policing by linking location, crime type, and time variables.

## ETL Pipeline

1. Extraction (Python + API)
- Source: Crime data fetched from Chicago Open Data Portal API (2001–present).

- Subset Used: Filtered to 2013–2023 for analysis.

- Initial Cleaning:

-      Removed null values and irrelevant columns (e.g., redundant coordinates).

-      Retained key fields (ID, Date/Time, Crime Type, Location, Arrest Status, etc.).

2. Transformation (Python + PostgreSQL)
- Data Enrichment:
-      Added calculated columns (e.g., time bins, geographic clusters).
-      Derived zip codes from latitude/longitude.

- Split Data: Created training/test sets for machine learning.

- Tools:
-      Python (Pandas) for manipulation.
-      PostgreSQL for intermediate storage and batch processing.

3. Loading (PostgreSQL + Python/Tableau)
- Storage: Cleaned data loaded into PostgreSQL as a centralized repository.
- Downstream Use:

- Machine Learning (Python):

-      Libraries: Scikit-Learn (Random Forest, DBSCAN), Prophet (time-series).
-      Tasks: Crime prediction, anomaly detection, hotspot mapping.
- Visualization (Tableau):
-      Interactive dashboards for historical trends (descriptive analytics).
-      Maps/charts for predictive insights (e.g., future hotspots).

4. Automation & Scalability
- API Integration: Auto-updates data periodically.

<img width="849" alt="image" src="https://github.com/user-attachments/assets/fec8a56a-03c4-45b2-a48b-efc6c8f7a8a6" />

Solution Architecture
![image](https://github.com/user-attachments/assets/024d96de-49b8-4168-8771-a2f554f40ad8)

## The Product
CrimeSight leverages machine learning, historical crime data, and real-time analytics to forecast crime trends and hotspots, enabling proactive policing. The core product is divided into two modules:
- Descriptive Analytics: CrimeSight utilizes historical crime data to identify patterns and trends. These insights are displayed through intuitive dashboards created with tools like Tableau. This module helps law enforcement agencies understand past and current crime dynamics to make informed decisions.

  The current product features three essential dashboards that cover both micro and macro aspects of crime analysis. The location-based analysis dashboard focuses on spatial analysis, the crime volume dashboard provides insights into the volume of crimes committed, and the incident analysis dashboard offers in-depth details of each crime.
  ![image](https://github.com/user-attachments/assets/d97ba561-b9fe-4ebb-82f4-6f34f2efd93b)

  ![image](https://github.com/user-attachments/assets/304b3d1c-6bea-4efc-9132-407d59e4bbd7)

  ![image](https://github.com/user-attachments/assets/f8b825d0-06cf-4808-8f77-a47df83e7efe)

- Predictive Analytics: CrimeSight employs machine learning algorithms to predict future crime hotspots and trends. By forecasting potential criminal activities, this module enables proactive resource deployment and crime prevention measures, enhancing the overall effectiveness of law enforcement strategies.
  - Clustering for Identifying Hotspots
  -     Clustering algorithms like DBSCAN are utilized to geographically group incidents that happen physically close to each other and identify hotspots. 
  - ![image](https://github.com/user-attachments/assets/aef66065-e887-49e3-b00b-d04bd7d8337b)
 
  - Time Series Analysis for Trend Detection
  -     Time series analysis using Prophet is employed to analyse crime data over time. The goal is to identify trends and patterns throughout the available historical data.
  - ![image](https://github.com/user-attachments/assets/82a6e663-5cc3-48df-8d81-71f4a76ea588)
 
  - Predictive Modelling for Forecasting Crime
  -     Supervised machine learning models, such as Random Forests and Isolation Forests, can predict the likelihood of crime in different areas or hotspots.
  - ![image](https://github.com/user-attachments/assets/0d474e4c-fae8-4162-a755-6638fd017fd9)
  - ![image](https://github.com/user-attachments/assets/a37379ca-6296-4b26-ae20-73633b1124d4)
 
  - Determining Arrest Factors with Random Forest
  -     The Random Forest algorithm is also employed to determine which criminal factors best predict whether or not an arrest is made. This analysis helps to understand the key elements influencing arrest decisions and can assist law enforcement in optimizing their strategies.
  - ![image](https://github.com/user-attachments/assets/6ec6abf5-b6ca-4e2b-b34e-ddd6914d2b51)

CrimeSight combines descriptive and predictive analytics into an all-in-one platform, enabling users to seamlessly transition between analysing historical data and forecasting future crime scenarios

