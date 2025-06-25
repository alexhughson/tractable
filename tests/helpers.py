"""
Test helper functions
"""
import os
import json
import gspread
from dotenv import load_dotenv
from tractable.connection_pool import get_connection_pool


def get_test_credentials():
    load_dotenv()
    creds_json = os.getenv("GOOGLE_SHEETS_CREDS_JSON")
    assert creds_json, "GOOGLE_SHEETS_CREDS_JSON env var required"
    return json.loads(creds_json)


def get_test_sheet_id():
    load_dotenv()
    sheet_id = os.getenv("TEST_SHEET_ID")
    assert sheet_id, "TEST_SHEET_ID env var required"
    return sheet_id


def get_gspread_client():
    # Legacy function - kept for compatibility but uses connection pool
    service_account_dict = get_test_credentials()
    pool = get_connection_pool(service_account_dict)
    return pool


def create_test_worksheet(sheet_name, rows=10, cols=5):
    pool = get_gspread_client()
    spreadsheet = pool.open_spreadsheet(get_test_sheet_id())
    
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        spreadsheet.del_worksheet(worksheet)
    except:
        pass
    
    return spreadsheet.add_worksheet(title=sheet_name, rows=rows, cols=cols)


def cleanup_test_worksheet(sheet_name):
    try:
        pool = get_gspread_client()
        spreadsheet = pool.open_spreadsheet(get_test_sheet_id())
        worksheet = spreadsheet.worksheet(sheet_name)
        spreadsheet.del_worksheet(worksheet)
    except:
        pass