"""
Test iterating over ranges with Pydantic models
"""
import pytest
from pydantic import BaseModel
from typing import Optional
from tractable import Spreadsheet
from tests.helpers import get_test_credentials, get_test_sheet_id, get_gspread_client


class User(BaseModel):
    name: str
    email: str
    score: float
    
    
class UserWithDefaults(BaseModel):
    name: str
    email: str
    score: float = 0.0
    status: str = "pending"
    

class UserWithOptional(BaseModel):
    name: str
    email: str
    score: Optional[float] = None
    status: Optional[str] = None


class UserWithExtras(BaseModel):
    model_config = {"extra": "allow"}
    
    name: str
    email: str


@pytest.mark.asyncio
async def test_iterate_with_pydantic_model():
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
        ["Charlie", "charlie@example.com", "92.3"]
    ]
    worksheet.update("A1:C4", test_data)
    
    spreadsheet = await Spreadsheet(service_account_dict, sheet_id)
    
    users = []
    async for user in spreadsheet.range("Sheet1!A1:C4").iter(User):
        users.append(user)
    
    assert len(users) == 3
    assert isinstance(users[0], User)
    assert users[0].name == "Alice"
    assert users[0].email == "alice@example.com"
    assert users[0].score == 95.5
    assert users[1].name == "Bob"
    assert users[1].score == 87.0
    assert users[2].name == "Charlie"
    assert users[2].score == 92.3


@pytest.mark.asyncio
async def test_iterate_with_pydantic_model_defaults():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()
    
    gspread_client = get_gspread_client()
    sheet = gspread_client.open_by_key(sheet_id)
    
    worksheet = sheet.sheet1
    worksheet.clear()
    
    test_data = [
        ["name", "email", "score", "status"],
        ["Alice", "alice@example.com", "95.5", "active"],
        ["Bob", "bob@example.com", "", ""],
        ["Charlie", "charlie@example.com", "92.3", ""]
    ]
    worksheet.update("A1:D4", test_data)
    
    spreadsheet = await Spreadsheet(service_account_dict, sheet_id)
    
    users = []
    async for user in spreadsheet.range("Sheet1!A1:D4").iter(UserWithDefaults):
        users.append(user)
    
    assert len(users) == 3
    assert isinstance(users[0], UserWithDefaults)
    assert users[0].name == "Alice"
    assert users[0].status == "active"
    assert users[1].name == "Bob"
    assert users[1].score == 0.0
    assert users[1].status == "pending"
    assert users[2].name == "Charlie"
    assert users[2].score == 92.3
    assert users[2].status == "pending"


@pytest.mark.asyncio
async def test_iterate_with_pydantic_model_optional_fields():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()
    
    gspread_client = get_gspread_client()
    sheet = gspread_client.open_by_key(sheet_id)
    
    worksheet = sheet.sheet1
    worksheet.clear()
    
    test_data = [
        ["name", "email", "score", "status"],
        ["Alice", "alice@example.com", "95.5", "active"],
        ["Bob", "bob@example.com", "", ""],
        ["Charlie", "charlie@example.com", "", "inactive"]
    ]
    worksheet.update("A1:D4", test_data)
    
    spreadsheet = await Spreadsheet(service_account_dict, sheet_id)
    
    users = []
    async for user in spreadsheet.range("Sheet1!A1:D4").iter(UserWithOptional):
        users.append(user)
    
    assert len(users) == 3
    assert isinstance(users[0], UserWithOptional)
    assert users[0].name == "Alice"
    assert users[0].score == 95.5
    assert users[0].status == "active"
    assert users[1].name == "Bob"
    assert users[1].score is None
    assert users[1].status is None
    assert users[2].name == "Charlie"
    assert users[2].score is None
    assert users[2].status == "inactive"


@pytest.mark.asyncio
async def test_iterate_unbounded_range_with_pydantic():
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
        ["", "", ""],
        ["Charlie", "charlie@example.com", "92.3"]
    ]
    worksheet.update("A1:C5", test_data)
    
    spreadsheet = await Spreadsheet(service_account_dict, sheet_id)
    
    users = []
    async for user in spreadsheet.range("Sheet1!A:C").iter(User):
        users.append(user)
    
    assert len(users) == 2
    assert users[0].name == "Alice"
    assert users[1].name == "Bob"
    assert all(user.name != "Charlie" for user in users)


@pytest.mark.asyncio
async def test_iterate_with_pydantic_model_extras():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()
    
    gspread_client = get_gspread_client()
    sheet = gspread_client.open_by_key(sheet_id)
    
    worksheet = sheet.sheet1
    worksheet.clear()
    
    test_data = [
        ["name", "email", "score", "status", "department"],
        ["Alice", "alice@example.com", "95.5", "active", "Engineering"],
        ["Bob", "bob@example.com", "87.0", "inactive", "Sales"],
        ["Charlie", "charlie@example.com", "92.3", "active", "Marketing"]
    ]
    worksheet.update("A1:E4", test_data)
    
    spreadsheet = await Spreadsheet(service_account_dict, sheet_id)
    
    users = []
    async for user in spreadsheet.range("Sheet1!A1:E4").iter(UserWithExtras):
        users.append(user)
    
    assert len(users) == 3
    assert isinstance(users[0], UserWithExtras)
    assert users[0].name == "Alice"
    assert users[0].email == "alice@example.com"
    assert users[0].score == "95.5"
    assert users[0].status == "active"
    assert users[0].department == "Engineering"
    assert users[1].department == "Sales"
    assert users[2].department == "Marketing"