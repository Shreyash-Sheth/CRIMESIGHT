import pandas as pd
import sqlite3
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, roc_curve, auc
from imblearn.over_sampling import SMOTE
import matplotlib.pyplot as plt
import seaborn as sns
import io
from PIL import Image

def load_data(db_path):
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM crimes"
    data = pd.read_sql_query(query, conn)
    conn.close()
    return data

def run_decision_tree_analysis(db_path, selected_vars):
    data = load_data(db_path)
    
    # Ensure date column is in datetime format
    data['date'] = pd.to_datetime(data['date'], errors='coerce')
    
    # Filter data by date range if required
    data = data[(data["date"] >= '2023-01-01') & (data["date"] <= '2023-12-31')]
    
    # Drop rows with missing target values
    data = data.dropna(subset=['arrest', 'latitude', 'longitude'])
    
    # Combine latitude and longitude into a single column if included
    if 'latitude' in selected_vars and 'longitude' in selected_vars:
        data['coordinates'] = data.apply(lambda row: f"{row['latitude']},{row['longitude']}", axis=1)
        selected_vars.append('coordinates')
        selected_vars.remove('latitude')
        selected_vars.remove('longitude')
    
    # Encoding categorical features
    label_encoders = {}
    for column in selected_vars:
        label_encoders[column] = LabelEncoder()
        data[column] = label_encoders[column].fit_transform(data[column])
    
    # Define features and target
    X = data[selected_vars]
    y = data['arrest'].astype(int)
    
    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    
    # Address class imbalance using SMOTE
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
    
    # Train Random Forest Classifier
    clf = RandomForestClassifier()
    clf.fit(X_train_resampled, y_train_resampled)
    
    # Predictions and performance metrics
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    class_report = classification_report(y_test, y_pred)
    fpr, tpr, _ = roc_curve(y_test, clf.predict_proba(X_test)[:,1])
    roc_auc = auc(fpr, tpr)
    
    # Plot feature importances
    feature_importances = clf.feature_importances_
    feature_importance_df = pd.DataFrame({'feature': X.columns, 'importance': feature_importances})
    feature_importance_df = feature_importance_df.sort_values('importance', ascending=False)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x='importance', y='feature', data=feature_importance_df)
    plt.title('Feature Importances')
    plt.tight_layout()
    
    buf_feature_importance = io.BytesIO()
    plt.savefig(buf_feature_importance, format='png')
    buf_feature_importance.seek(0)
    
    # Plot ROC curve
    plt.figure(figsize=(10, 6))
    plt.plot(fpr, tpr, label=f'ROC curve (area = {roc_auc:0.2f})')
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic')
    plt.legend(loc='lower right')
    plt.tight_layout()
    
    buf_decision_tree = io.BytesIO()
    plt.savefig(buf_decision_tree, format='png')
    buf_decision_tree.seek(0)
    
    stats = (
        f"Accuracy: {accuracy:.2f}\n\n"
        f"Classification Report:\n{class_report}\n"
        f"AUC: {roc_auc:.2f}"
    )
    
    return buf_feature_importance, buf_decision_tree, stats
