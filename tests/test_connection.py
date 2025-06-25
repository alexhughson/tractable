"""Test Google Sheets connection."""

import json
import os
from dotenv import load_dotenv
from tractable.connection_pool import get_connection_pool


def test_connection():
    load_dotenv()

    creds_json = os.getenv("GOOGLE_SHEETS_CREDS_JSON")
    sheet_id = os.getenv("TEST_SHEET_ID")

    assert creds_json, "GOOGLE_SHEETS_CREDS_JSON env var required"
    assert sheet_id, "TEST_SHEET_ID env var required"

    creds_data = json.loads(creds_json)
    pool = get_connection_pool(creds_data)
    sheet = pool.open_spreadsheet(sheet_id)

    worksheet = sheet.sheet1
    worksheet.clear()

    test_data = [
        ["name", "email", "score"],
        ["Alice", "alice@example.com", "95"],
        ["Bob", "bob@example.com", "87"],
        ["Charlie", "charlie@example.com", "92"],
    ]

    worksheet.update(test_data, "A1:C4")

    result = worksheet.get_all_values()

    assert result == test_data
    assert result[0] == ["name", "email", "score"]
    assert result[1][0] == "Alice"
