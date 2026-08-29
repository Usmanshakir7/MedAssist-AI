import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Google API permissions
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit secrets
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)

# Connect to Google
client = gspread.authorize(credentials)

# Open your Google Sheet
sheet = client.open("MedAssistAI Users").sheet1

print("SUCCESS!")
print("Connected to:", sheet.title)

# Test writing
sheet.update_cell(1, 1, "MedAssistAI Connection Test")

print("Test data written successfully!")