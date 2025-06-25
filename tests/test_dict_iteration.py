"""
Test iterating over ranges in dict mode
"""
import pytest
from tractable import Spreadsheet
from tests.helpers import get_test_credentials, get_test_sheet_id, get_gspread_client


def test_iterate_a1_range_dict_mode():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()
    
    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)
    
    worksheet = sheet.sheet1
    worksheet.clear()
    
    test_data = [
        ["name", "email", "score"],
        ["Alice", "alice@example.com", "95"],
        ["Bob", "bob@example.com", "87"],
        ["Charlie", "charlie@example.com", "92"]
    ]
    worksheet.update(test_data, "A1:C4")
    
    spreadsheet = Spreadsheet(service_account_dict, sheet_id)
    
    rows = []
    for row in spreadsheet.range("Sheet1!A1:C4").iter():
        rows.append(row)
    
    assert len(rows) == 3
    assert rows[0]["name"] == "Alice"
    assert rows[0]["email"] == "alice@example.com"
    assert rows[0]["score"] == "95"
    assert rows[1]["name"] == "Bob"
    assert rows[2]["name"] == "Charlie"


def test_iterate_unbounded_range_dict_mode():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()
    
    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)
    
    worksheet = sheet.sheet1
    worksheet.clear()
    
    test_data = [
        ["name", "email", "score", "status"],
        ["Alice", "alice@example.com", "95", "active"],
        ["Bob", "bob@example.com", "87", "active"],
        ["Charlie", "charlie@example.com", "92", "inactive"],
        ["", "", "", ""],
        ["David", "david@example.com", "88", "active"]
    ]
    worksheet.update(test_data, "A1:D6")
    
    spreadsheet = Spreadsheet(service_account_dict, sheet_id)
    
    rows = []
    for row in spreadsheet.range("Sheet1!A:D").iter():
        rows.append(row)
    
    assert len(rows) == 3
    assert rows[0]["name"] == "Alice"
    assert rows[1]["name"] == "Bob"
    assert rows[2]["name"] == "Charlie"
    assert "David" not in [row.get("name") for row in rows]


def test_iterate_header_only_dict_mode():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()
    
    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)
    
    worksheet = sheet.sheet1
    worksheet.clear()
    
    test_data = [
        ["name", "email", "score", "status"]
    ]
    worksheet.update(test_data, "A1:D1")
    
    spreadsheet = Spreadsheet(service_account_dict, sheet_id)
    
    rows = []
    for row in spreadsheet.range("Sheet1!A1:D1").iter():
        rows.append(row)
    
    assert len(rows) == 0


def test_iterate_empty_range_returns_empty():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()
    
    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)
    
    worksheet = sheet.sheet1
    worksheet.clear()
    
    spreadsheet = Spreadsheet(service_account_dict, sheet_id)
    
    collected_rows = []
    for row in spreadsheet.range("Sheet1!A1:D1").iter():
        collected_rows.append(row)
    
    assert len(collected_rows) == 0