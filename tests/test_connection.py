"""Test Google Sheets connection."""

import json
import os
import gspread
from dotenv import load_dotenv


def test_connection():
    load_dotenv()

    creds_json = os.getenv("GOOGLE_SHEETS_CREDS_JSON")
    sheet_id = os.getenv("TEST_SHEET_ID")

    assert creds_json, "GOOGLE_SHEETS_CREDS_JSON env var required"
    assert sheet_id, "TEST_SHEET_ID env var required"

    creds_data = json.loads(creds_json)
    gc = gspread.service_account_from_dict(creds_data)
    sheet = gc.open_by_key(sheet_id)

    worksheet = sheet.sheet1
    worksheet.clear()

    test_data = [
        ["name", "email", "score"],
        ["Alice", "alice@example.com", "95"],
        ["Bob", "bob@example.com", "87"],
        ["Charlie", "charlie@example.com", "92"],
    ]

    worksheet.update("A1:C4", test_data)

    result = worksheet.get_all_values()

    assert result == test_data
    assert result[0] == ["name", "email", "score"]
    assert result[1][0] == "Alice"
