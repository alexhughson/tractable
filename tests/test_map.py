"""
Test map functionality for updating ranges
"""

import pytest
from pydantic import BaseModel, Field
from tractable import Spreadsheet
from tests.helpers import get_test_credentials, get_test_sheet_id, get_gspread_client


class User(BaseModel):
    name: str
    email: str
    score: float


def test_map_dict_basic_update():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()

    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)

    worksheet = sheet.sheet1
    worksheet.clear()

    test_data = [
        ["name", "email", "status"],
        ["Alice", "alice@example.com", "pending"],
        ["Bob", "bob@example.com", "pending"],
        ["Charlie", "charlie@example.com", "pending"],
    ]
    worksheet.update(test_data, "A1:C4")

    spreadsheet = Spreadsheet(service_account_dict, sheet_id)

    def mark_processed(row: dict) -> dict:
        row["status"] = "processed"
        return row

    spreadsheet.range("Sheet1!A1:C4").map(mark_processed)

    updated_values = worksheet.get("A1:C4")
    assert updated_values[1][2] == "processed"
    assert updated_values[2][2] == "processed"
    assert updated_values[3][2] == "processed"


def test_map_pydantic_model_update():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()

    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)

    worksheet = sheet.sheet1
    worksheet.clear()

    test_data = [
        ["name", "email", "score"],
        ["Alice", "alice@example.com", "95.5"],
        ["Bob", "bob@example.com", "87.0"],
        ["Charlie", "charlie@example.com", "92.3"],
    ]
    worksheet.update(test_data, "A1:C4")

    spreadsheet = Spreadsheet(service_account_dict, sheet_id)

    def boost_score(user: User) -> User:
        user.score = user.score * 1.1
        return user

    spreadsheet.range("Sheet1!A1:C4").map(boost_score, model=User)

    updated_values = worksheet.get("A1:C4")
    assert float(updated_values[1][2]) == pytest.approx(105.05)
    assert float(updated_values[2][2]) == pytest.approx(95.7)
    assert float(updated_values[3][2]) == pytest.approx(101.53)


def test_map_with_none_skips_update():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()

    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)

    worksheet = sheet.sheet1
    worksheet.clear()

    test_data = [
        ["name", "email", "score"],
        ["Alice", "alice@example.com", "95.5"],
        ["Bob", "bob@example.com", "87.0"],
        ["Charlie", "charlie@example.com", "92.3"],
    ]
    worksheet.update(test_data, "A1:C4")

    spreadsheet = Spreadsheet(service_account_dict, sheet_id)

    def selective_boost(user: User) -> User:
        if user.score > 90:
            user.score = user.score * 1.1
            return user
        return None

    spreadsheet.range("Sheet1!A1:C4").map(selective_boost, model=User)

    updated_values = worksheet.get("A1:C4")
    assert float(updated_values[1][2]) == pytest.approx(105.05)
    assert updated_values[2][2] == "87.0"
    assert float(updated_values[3][2]) == pytest.approx(101.53)


def test_map_dict_selective_field_update():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()

    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)

    worksheet = sheet.sheet1
    worksheet.clear()

    test_data = [
        ["name", "email", "score", "status"],
        ["Alice", "alice@example.com", "95.5", "active"],
        ["Bob", "bob@example.com", "87.0", "inactive"],
        ["Charlie", "charlie@example.com", "92.3", "active"],
    ]
    worksheet.update(test_data, "A1:D4")

    spreadsheet = Spreadsheet(service_account_dict, sheet_id)

    def process_active_users(row: dict) -> dict:
        if row["status"] == "active":
            row["email"] = row["email"].replace("@example.com", "@newdomain.com")
            return row
        return None

    spreadsheet.range("Sheet1!A1:D4").map(process_active_users)

    updated_values = worksheet.get("A1:D4")
    assert updated_values[1][1] == "alice@newdomain.com"
    assert updated_values[2][1] == "bob@example.com"
    assert updated_values[3][1] == "charlie@newdomain.com"


def test_map_empty_range_does_nothing():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()

    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)

    worksheet = sheet.sheet1
    worksheet.clear()

    test_data = [["name", "email", "score"]]
    worksheet.update(test_data, "A1:C1")

    spreadsheet = Spreadsheet(service_account_dict, sheet_id)

    transform_called = False

    def transform(row: dict) -> dict:
        nonlocal transform_called
        transform_called = True
        return row

    spreadsheet.range("Sheet1!A1:C1").map(transform)

    assert not transform_called


def test_map_unbounded_column_range_with_pydantic():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()

    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)

    worksheet = sheet.sheet1
    worksheet.clear()

    test_data = [
        ["name", "email", "score"],
        ["Alice", "alice@example.com", "95.5"],
        ["Bob", "bob@example.com", "87.0"],
        ["Charlie", "charlie@example.com", "92.3"],
        ["", "", ""],  # Empty row - should stop processing here
        ["David", "david@example.com", "88.5"],  # This should NOT be processed
    ]
    worksheet.update(test_data, "A1:C6")

    spreadsheet = Spreadsheet(service_account_dict, sheet_id)

    def boost_score(user: User) -> User:
        user.score = user.score * 1.1
        return user

    # Using unbounded column range A:C
    # This SHOULD work without errors and stop at the empty row
    spreadsheet.range("Sheet1!A:C").map(boost_score, model=User)

    # Verify that only the first 3 data rows were updated
    updated_values = worksheet.get("A1:C6")
    print(f"Updated values: {updated_values}")
    print(f"Number of rows returned: {len(updated_values)}")

    assert float(updated_values[1][2]) == pytest.approx(105.05)
    assert float(updated_values[2][2]) == pytest.approx(95.7)
    assert float(updated_values[3][2]) == pytest.approx(101.53)

    assert updated_values[4] == []
    # David's row should NOT have been processed (no 1.1x multiplier applied)

    assert updated_values[5][2] == "88.5"


def test_another_map_case():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()

    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)

    worksheet = sheet.sheet1
    worksheet.clear()

    test_data = [
        ["Company Name", "Size", "Last funding round"],
        ["Google", "", ""],
        ["Apple", "", ""],
        ["Microsoft", "", ""],
    ]
    worksheet.update(test_data, "A1:D4")

    spreadsheet = Spreadsheet(service_account_dict, sheet_id)

    class Company(BaseModel):
        name: str = Field(
            validation_alias="Company Name", description="The name of the company"
        )
        size: str | None = Field(
            validation_alias="Size", default=None, description="The size of the company"
        )
        last_funding_round: str | None = Field(
            validation_alias="Last funding round",
            default=None,
            description="The last funding round of the company",
        )

    def set_size(company: Company) -> Company:
        company.size = "10000"
        return company

    spreadsheet.range("Sheet1!A:C").map(set_size, model=Company)

    updated_values = worksheet.get("A1:C4")
    assert updated_values[1][1] == "10000"
    assert updated_values[2][1] == "10000"
    assert updated_values[3][1] == "10000"
