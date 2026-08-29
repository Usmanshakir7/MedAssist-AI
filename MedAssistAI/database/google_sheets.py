import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _credentials():
    if "gcp_service_account" not in st.secrets:
        raise RuntimeError(
            "Google Sheets is not configured. Add [gcp_service_account] "
            "to .streamlit/secrets.toml."
        )

    info = dict(st.secrets["gcp_service_account"])
    return Credentials.from_service_account_info(info, scopes=SCOPES)


@st.cache_resource
def get_worksheet():
    client = gspread.authorize(_credentials())
    spreadsheet_name = st.secrets.get("google_sheet_name", "MedAssistAI Users")
    spreadsheet = client.open(spreadsheet_name)

    # Use a worksheet named Users when available; otherwise first sheet.
    try:
        worksheet = spreadsheet.worksheet("Users")
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.sheet1

    # Ensure headers exist.
    if not worksheet.row_values(1):
        worksheet.append_row(
            ["User ID", "Full Name", "Email", "Created At", "Last Login"],
            value_input_option="USER_ENTERED",
        )

    return worksheet


def save_new_user(user_id, full_name, email, created_at):
    """Append a newly registered user to Google Sheets."""
    try:
        ws = get_worksheet()
        ws.append_row(
            [str(user_id), full_name, email, str(created_at), ""],
            value_input_option="USER_ENTERED",
        )
        return True, ""
    except Exception as exc:
        return False, str(exc)


def update_last_login(email, login_time):
    """Update Last Login for an existing email. Does not store passwords."""
    try:
        ws = get_worksheet()
        values = ws.get_all_values()

        if not values:
            return False, "Google Sheet is empty."

        headers = values[0]
        try:
            email_col = headers.index("Email") + 1
            login_col = headers.index("Last Login") + 1
        except ValueError:
            return False, "Google Sheet headers are missing."

        for row_number, row in enumerate(values[1:], start=2):
            if len(row) >= email_col and row[email_col - 1].strip().lower() == email.lower():
                ws.update_cell(row_number, login_col, str(login_time))
                return True, ""

        return False, "User email was not found in Google Sheet."
    except Exception as exc:
        return False, str(exc)
