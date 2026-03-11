import gspread
import pandas as pd
import streamlit as st
from datetime import datetime

SPREADSHEET_KEY = "16-0dwjrNvDFjiYy0z9G6ldZUArJsNWL5mQFlxAPxdEE"


def connect_sheet():
    creds_dict = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"],
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
    }

    client = gspread.service_account_from_dict(creds_dict)
    spreadsheet = client.open_by_key(SPREADSHEET_KEY)

    attempts_sheet = spreadsheet.worksheet("attempts")
    answers_sheet = spreadsheet.worksheet("answers")
    return attempts_sheet, answers_sheet