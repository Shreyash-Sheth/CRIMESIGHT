import tkinter as tk
from tkinter import ttk, filedialog, messagebox, PhotoImage
import sqlite3
import os
import webbrowser
import geopandas as gpd
from clustering_analysis import run_analysis
from decision_tree_analysis import run_decision_tree_analysis
from data_cleaning import DataCleaningPipeline
from dbscan_nocirc import create_map_with_cluster_size, load_data, convert_to_utm, apply_dbscan
import subprocess
import time_series_analysis  # Import the time series analysis module
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Default database path
default_db_path = '/Users/mttgoodwin/Desktop/Program/crime_data.db'
test_db_path = 'TEST.db'  # Path for the time series analysis database

# Initialize data cleaning pipeline
dataset_identifier = 'ijzp-q8t2'
data_cleaning_pipeline = DataCleaningPipeline(default_db_path)

def browse_file():
    filename = filedialog.askopenfilename(filetypes=[("SQLite Database", "*.db")])
    if filename:
        db_path_var.set(filename)

def open_html(file_name='Chicago_crime_clusters_with_cluster_size.html'):
    if os.path.exists(file_name):
        webbrowser.open('file://' + os.path.realpath(file_name))
    else:
        messagebox.showerror("Error", "The HTML file does not exist.")

def log_message(message):
    console_text.config(state=tk.NORMAL)
    console_text.insert(tk.END, message + '\n')
    console_text.config(state=tk.DISABLED)
    console_text.see(tk.END)

def run_analysis_and_show():
    db_path = db_path_var.get()
    
    try:
        log_message("Running clustering analysis...")
        run_analysis(db_path)
        open_html()
        messagebox.showinfo("Success", "Clustering analysis completed and map generated.")
        log_message("Clustering analysis completed successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        log_message(f"Error during clustering analysis: {e}")

def run_decision_tree_and_show():
    db_path = db_path_var.get()
    selected_vars = [var[0] for var in input_vars if var[1].get()]
    
    try:
        log_message("Running decision tree analysis...")
        buf_feature_importance, buf_decision_tree, stats = run_decision_tree_analysis(db_path, selected_vars)
        
        # Display the feature importances in the GUI
        img_feature_importance = PhotoImage(data=buf_feature_importance.getvalue())
        feature_importance_label.config(image=img_feature_importance)
        feature_importance_label.image = img_feature_importance
        
        # Display the simplified decision tree in the GUI
        img_decision_tree = PhotoImage(data=buf_decision_tree.getvalue())
        decision_tree_label.config(image=img_decision_tree)
        decision_tree_label.image = img_decision_tree
        
        # Display the statistics in the GUI
        stats_text.delete(1.0, tk.END)
        stats_text.insert(tk.END, stats)
        
        messagebox.showinfo("Success", "Decision tree analysis completed.")
        log_message("Decision tree analysis completed successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        log_message(f"Error during decision tree analysis: {e}")

def fetch_initial_data():
    try:
        start_date = start_date_var.get()
        end_date = end_date_var.get()
        log_message("Fetching initial data...")
        data_cleaning_pipeline.fetch_initial_data(dataset_identifier, start_date, end_date)
        messagebox.showinfo("Success", "Initial data fetch completed and saved to the database.")
        log_message("Initial data fetch completed successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        log_message(f"Error fetching initial data: {e}")

def update_database():
    try:
        start_date = start_date_var.get()
        end_date = end_date_var.get()
        log_message("Updating database...")
        data_cleaning_pipeline.add_new_data(dataset_identifier, start_date, end_date)
        messagebox.showinfo("Success", "Database updated with new data.")
        log_message("Database updated successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        log_message(f"Error updating database: {e}")

def run_sql_command():
    db_path = db_path_var.get()
    sql_command = sql_command_text.get("1.0", tk.END).strip()
    
    if not sql_command:
        messagebox.showerror("Error", "SQL command cannot be empty.")
        return
    
    # Log the SQL command for debugging
    log_message(f"Executing SQL command: {sql_command}")
    
    # Clear the Treeview
    for i in result_tree.get_children():
        result_tree.delete(i)
    result_tree["columns"] = ()
    result_tree["show"] = "headings"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql_command)
        results = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        result_tree["columns"] = column_names
        
        for col in column_names:
            result_tree.heading(col, text=col)
            result_tree.column(col, width=100, stretch=tk.NO)
        
        for row in results:
            result_tree.insert("", tk.END, values=row)
        
        conn.close()
        log_message("SQL command executed successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        log_message(f"Error executing SQL command: {e}")



# Function to run anomaly detection
def run_anomaly_detection():
    try:
        import anomalies  # Import the anomalies module
        log_message("Running anomaly detection...")
        anomalies.detect_anomalies()  # Run the anomaly detection

        # Create a new window for displaying the plots
        plot_window = tk.Toplevel(root)
        plot_window.title("Anomaly Detection Results")

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(21, 7))  # Create subplots

        # Plot each subplot
        anomalies.plot_high_anomalies(ax1)
        anomalies.plot_monthly_anomalies(ax2)
        anomalies.plot_weekly_anomalies(ax3)

        # Integrate the figure with Tkinter
        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Open the anomaly map in the default web browser
        webbrowser.open("crime_anomalies_map.html")
        
        messagebox.showinfo("Success", "Anomaly detection completed and map generated.")
        log_message("Anomaly detection completed successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        log_message(f"Error during anomaly detection: {e}")

# Function to run time series analysis and display the plots in the GUI
def run_time_series_and_show():
    try:
        log_message("Running time series analysis...")
        
        # Clear previous plots
        for widget in time_series_frame.winfo_children():
            if isinstance(widget, FigureCanvasTkAgg):
                widget.get_tk_widget().destroy()
        
        figures = time_series_analysis.run_time_series_analysis(test_db_path)
        
        for fig in figures:
            canvas = FigureCanvasTkAgg(fig, master=time_series_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        messagebox.showinfo("Success", "Time series analysis completed.")
        log_message("Time series analysis completed successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        log_message(f"Error during time series analysis: {e}")

# GUI setup
root = tk.Tk()
root.title("CrimeSight")
root.state('zoomed')  # Maximize window on startup

# Create a Notebook (tabbed interface)
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both')

# Create frames for each tab
db_frame = ttk.Frame(notebook, padding="10")
ml_frame = ttk.Frame(notebook, padding="10")

# Add tabs to the Notebook
notebook.add(db_frame, text="Database Operations")
notebook.add(ml_frame, text="ML Analyses")

# Nested Notebook for ML Analyses
ml_notebook = ttk.Notebook(ml_frame)
ml_notebook.pack(expand=True, fill='both')

# Create frames for each ML analysis
clustering_frame = ttk.Frame(ml_notebook, padding="10")
decision_tree_frame = ttk.Frame(ml_notebook, padding="10")

anomaly_frame = ttk.Frame(ml_notebook, padding="10")  # Add this line to create the Anomaly Detection frame
time_series_frame = ttk.Frame(ml_notebook, padding="10")  # Frame for Time Series Analysis

# Add nested tabs to the ML Analyses notebook
ml_notebook.add(clustering_frame, text="Clustering Analysis")
ml_notebook.add(decision_tree_frame, text="Random Analysis") #### CHECK THIS ##################################################################

ml_notebook.add(anomaly_frame, text="Anomaly Detection")  # Add this line to add the Anomaly Detection tab
ml_notebook.add(time_series_frame, text="Time Series Analysis")  # Add Time Series Analysis tab

# Database Operations Tab
ttk.Label(db_frame, text="Database Path:").pack(anchor='w')
db_path_var = tk.StringVar(value=default_db_path)
db_path_entry = ttk.Entry(db_frame, width=60, textvariable=db_path_var)
db_path_entry.pack(fill='x', padx=5, pady=5)
ttk.Button(db_frame, text="Browse", command=browse_file).pack(padx=5, pady=5)

ttk.Label(db_frame, text="Start Date (YYYY-MM-DD):").pack(anchor='w')
start_date_var = tk.StringVar(value='2023-01-01')
ttk.Entry(db_frame, width=20, textvariable=start_date_var).pack(fill='x', padx=5, pady=5)

ttk.Label(db_frame, text="End Date (YYYY-MM-DD):").pack(anchor='w')
end_date_var = tk.StringVar(value='2023-12-31')
ttk.Entry(db_frame, width=20, textvariable=end_date_var).pack(fill='x', padx=5, pady=5)

ttk.Button(db_frame, text="Fetch Initial Data", command=fetch_initial_data).pack(pady=10)
ttk.Button(db_frame, text="Update Database", command=update_database).pack(pady=10)

# SQL Command Section
ttk.Label(db_frame, text="SQL Command:").pack(anchor='w')
sql_command_text = tk.Text(db_frame, height=5)
sql_command_text.pack(fill='both', pady=5, padx=5, expand=True)

ttk.Button(db_frame, text="Run SQL Command", command=run_sql_command).pack(pady=10)

# SQL Result Output
ttk.Label(db_frame, text="SQL Result:").pack(anchor='w')
result_tree_frame = ttk.Frame(db_frame)
result_tree_frame.pack(fill='both', pady=5, padx=5, expand=True)

result_tree = ttk.Treeview(result_tree_frame, show="headings")
result_tree.pack(side='left', fill='both', expand=True)

# Add vertical scrollbar to the Treeview
result_scrollbar_y = ttk.Scrollbar(result_tree_frame, orient=tk.VERTICAL, command=result_tree.yview)
result_scrollbar_y.pack(side='right', fill='y')
result_tree.configure(yscroll=result_scrollbar_y.set)

# Add horizontal scrollbar to the Treeview
result_scrollbar_x = ttk.Scrollbar(result_tree_frame, orient=tk.HORIZONTAL, command=result_tree.xview)
result_scrollbar_x.pack(side='bottom', fill='x')
result_tree.configure(xscroll=result_scrollbar_x.set)

# Console Output
ttk.Label(db_frame, text="Console:").pack(anchor='w')
console_frame = ttk.Frame(db_frame)
console_frame.pack(fill='both', pady=5, padx=5, expand=True)

console_text = tk.Text(console_frame, height=10, state=tk.DISABLED)
console_text.pack(side='left', fill='both', expand=True)

# Add vertical scrollbar to the console output
console_scrollbar = ttk.Scrollbar(console_frame, orient=tk.VERTICAL, command=console_text.yview)
console_text.configure(yscroll=console_scrollbar.set)
console_scrollbar.pack(side='right', fill='y')

# Clustering Analysis Tab
ttk.Button(clustering_frame, text="Run Clustering Analysis", command=run_analysis_and_show).pack(pady=10)

# Decision Tree Analysis Tab

input_vars = [
    ("primary_type", tk.BooleanVar(value=True)),
    ("description", tk.BooleanVar(value=True)),
    ("location_description", tk.BooleanVar(value=True)),
    ("beat", tk.BooleanVar(value=True)),
    ("district", tk.BooleanVar(value=True)),
    ("latitude", tk.BooleanVar(value=True)),
    ("longitude", tk.BooleanVar(value=True))
]

ttk.Button(decision_tree_frame, text="Run Random Forest Analysis", command=run_decision_tree_and_show).pack(pady=10)

# Frame for displaying visualizations side by side in Decision Tree Analysis
visualization_frame = ttk.Frame(decision_tree_frame)
visualization_frame.pack(fill='both', pady=10, expand=True)

# Placeholder for displaying the feature importances
feature_importance_label = ttk.Label(visualization_frame)
feature_importance_label.pack(side='left', padx=10)

# Placeholder for displaying the decision tree
decision_tree_label = ttk.Label(visualization_frame)
decision_tree_label.pack(side='left', padx=10)

# Text box for displaying decision tree statistics
stats_text = tk.Text(decision_tree_frame, height=10, width=80)
stats_text.pack(fill='both', pady=10, expand=True)



# Anomaly Detection Tab
ttk.Button(anomaly_frame, text="Run Anomaly Detection", command=run_anomaly_detection).pack(pady=10)

# Time Series Analysis Tab
ttk.Button(time_series_frame, text="Run Time Series Analysis", command=run_time_series_and_show).pack(pady=10)

root.mainloop()
