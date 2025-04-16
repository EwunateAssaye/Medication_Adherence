import streamlit as st
import pandas as pd
from tkinter import messagebox
import gspread
import joblib
import pickle
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.service_account import Credentials

# Load ML Model
model = joblib.load("SVC_model.pkl")

# # Load ML Model
# @st.cache_resource
# def load_model():
#     with open("Random Forest Classifier.pkl", "rb") as file:
#         model = pickle.load(file)
#     return model

# model = load_model()

# Google Sheets Authentication
def connect_gsheet(sheet_url):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_url(sheet_url).sheet1

SHEET_URL = "YOUR_GOOGLE_SHEET_URL"
sheet = connect_gsheet(SHEET_URL)

# Read Data from Google Sheet
def get_latest_input():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Predict Function
def predict(input_data):
    return model.predict(input_data)

# Update Google Sheet with Prediction
def update_google_sheet(row, prediction):
    row.append(prediction)
    sheet.append_row(row)

# Send Email with Prediction
def send_email(physician_email, patient_email, message_body):
    sender_email = "your_email@gmail.com"
    sender_password = "your_email_password"  # Use environment variables instead!
    
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["Subject"] = "Medical Prediction Results"
    msg.attach(MIMEText(message_body, "plain"))
    
    recipients = [physician_email, patient_email]
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())
        return "Email sent successfully!"
    except Exception as e:
        return f"Error sending email: {e}"

# Streamlit UI
st.title("Medical Diagnosis Prediction")

if st.button("Fetch Latest Data & Predict"):
    data = get_latest_input()
    
    if data.empty:
        st.warning("No new data received.")
    else:
        latest_row = data.iloc[-1].tolist()  # Get latest form submission
        input_features = pd.DataFrame([latest_row[:-2]])  # Exclude emails
        
        prediction = predict(input_features)[0]
        update_google_sheet(latest_row, prediction)
        
        physician_email = latest_row[-2]
        patient_email = latest_row[-1]
        message = f"Dear Doctor, \n\nThe AI prediction result is: {prediction}\n\nBest Regards, AI System"
        
        email_status = send_email(physician_email, patient_email, message)
        st.success(f"Prediction: {prediction}")
        st.info(email_status)
