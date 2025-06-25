"""
Test map functionality for updating ranges
"""

import pytest
from pydantic import BaseModel
from tractable import Spreadsheet
from tests.helpers import get_test_credentials, get_test_sheet_id, get_gspread_client


class User(BaseModel):
    name: str
    email: str
    score: float


@pytest.mark.asyncio
async def test_map_dict_basic_update():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()

    gspread_client = get_gspread_client()
    sheet = gspread_client.open_by_key(sheet_id)

    worksheet = sheet.sheet1
    worksheet.clear()

    test_data = [
        ["name", "email", "status"],
        ["Alice", "alice@example.com", "pending"],
        ["Bob", "bob@example.com", "pending"],
        ["Charlie", "charlie@example.com", "pending"],
    ]
    worksheet.update("A1:C4", test_data)

    spreadsheet = await Spreadsheet(service_account_dict, sheet_id)

    async def mark_processed(row: dict) -> dict:
        row["status"] = "processed"
        return row

    await spreadsheet.range("Sheet1!A1:C4").map(mark_processed)

    updated_values = worksheet.get("A1:C4")
    assert updated_values[1][2] == "processed"
    assert updated_values[2][2] == "processed"
    assert updated_values[3][2] == "processed"


@pytest.mark.asyncio
async def test_map_pydantic_model_update():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()

    gspread_client = get_gspread_client()
    sheet = gspread_client.open_by_key(sheet_id)

    worksheet = sheet.sheet1
    worksheet.clear()

    test_data = [
        ["name", "email", "score"],
        ["Alice", "alice@example.com", "95.5"],
        ["Bob", "bob@example.com", "87.0"],
        ["Charlie", "charlie@example.com", "92.3"],
    ]
    worksheet.update("A1:C4", test_data)

    spreadsheet = await Spreadsheet(service_account_dict, sheet_id)

    async def boost_score(user: User) -> User:
        user.score = user.score * 1.1
        return user

    await spreadsheet.range("Sheet1!A1:C4").map(boost_score, model=User)

    updated_values = worksheet.get("A1:C4")
    assert float(updated_values[1][2]) == pytest.approx(105.05)
    assert float(updated_values[2][2]) == pytest.approx(95.7)
    assert float(updated_values[3][2]) == pytest.approx(101.53)


@pytest.mark.asyncio
async def test_map_with_none_skips_update():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()

    gspread_client = get_gspread_client()
    sheet = gspread_client.open_by_key(sheet_id)

    worksheet = sheet.sheet1
    worksheet.clear()

    test_data = [
        ["name", "email", "score"],
        ["Alice", "alice@example.com", "95.5"],
        ["Bob", "bob@example.com", "87.0"],
        ["Charlie", "charlie@example.com", "92.3"],
    ]
    worksheet.update("A1:C4", test_data)

    spreadsheet = await Spreadsheet(service_account_dict, sheet_id)

    async def selective_boost(user: User) -> User:
        if user.score > 90:
            user.score = user.score * 1.1
            return user
        return None

    await spreadsheet.range("Sheet1!A1:C4").map(selective_boost, model=User)

    updated_values = worksheet.get("A1:C4")
    assert float(updated_values[1][2]) == pytest.approx(105.05)
    assert updated_values[2][2] == "87.0"
    assert float(updated_values[3][2]) == pytest.approx(101.53)


@pytest.mark.asyncio
async def test_map_dict_selective_field_update():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()

    gspread_client = get_gspread_client()
    sheet = gspread_client.open_by_key(sheet_id)

    worksheet = sheet.sheet1
    worksheet.clear()

    test_data = [
        ["name", "email", "score", "status"],
        ["Alice", "alice@example.com", "95.5", "active"],
        ["Bob", "bob@example.com", "87.0", "inactive"],
        ["Charlie", "charlie@example.com", "92.3", "active"],
    ]
    worksheet.update("A1:D4", test_data)

    spreadsheet = await Spreadsheet(service_account_dict, sheet_id)

    async def process_active_users(row: dict) -> dict:
        if row["status"] == "active":
            row["email"] = row["email"].replace("@example.com", "@newdomain.com")
            return row
        return None

    await spreadsheet.range("Sheet1!A1:D4").map(process_active_users)

    updated_values = worksheet.get("A1:D4")
    assert updated_values[1][1] == "alice@newdomain.com"
    assert updated_values[2][1] == "bob@example.com"
    assert updated_values[3][1] == "charlie@newdomain.com"


@pytest.mark.asyncio
async def test_map_empty_range_does_nothing():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()

    gspread_client = get_gspread_client()
    sheet = gspread_client.open_by_key(sheet_id)

    worksheet = sheet.sheet1
    worksheet.clear()

    test_data = [["name", "email", "score"]]
    worksheet.update("A1:C1", test_data)

    spreadsheet = await Spreadsheet(service_account_dict, sheet_id)

    transform_called = False

    async def transform(row: dict) -> dict:
        nonlocal transform_called
        transform_called = True
        return row

    await spreadsheet.range("Sheet1!A1:C1").map(transform)

    assert not transform_called
