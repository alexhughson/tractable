"""
Test using Pydantic validation aliases to map column names to field names
"""
import pytest
from pydantic import BaseModel, Field
from typing import Optional
from tractable import Spreadsheet
from tests.helpers import get_test_credentials, get_test_sheet_id, get_gspread_client


class Employee(BaseModel):
    first_name: str = Field(alias="First Name")
    last_name: str = Field(alias="Last Name")
    email_address: str = Field(alias="Email Address")
    monthly_salary: float = Field(alias="Monthly Salary")


class Product(BaseModel):
    product_id: str = Field(alias="Product ID")
    product_name: str = Field(alias="Product Name")
    unit_price: float = Field(alias="Unit Price")
    stock_quantity: int = Field(alias="Stock Quantity")
    is_active: bool = Field(alias="Is Active")


class CustomerWithMixed(BaseModel):
    customer_id: str = Field(alias="Customer ID")
    full_name: str = Field(alias="Full Name")
    email: str  # No alias - should match column name exactly
    phone_number: str = Field(alias="Phone Number")
    status: str  # No alias


class PersonWithOptional(BaseModel):
    first_name: str = Field(alias="First Name")
    middle_name: Optional[str] = Field(alias="Middle Name", default=None)
    last_name: str = Field(alias="Last Name")
    age: Optional[int] = Field(alias="Age", default=None)


class DataWithSpecialChars(BaseModel):
    company_name: str = Field(alias="Company (Name)")
    revenue_usd: float = Field(alias="Revenue ($USD)")
    growth_rate: float = Field(alias="Growth Rate %")
    contact_email: str = Field(alias="Contact@Email")


def test_iter_with_basic_validation_alias():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()
    
    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)
    
    worksheet = sheet.sheet1
    worksheet.clear()
    
    test_data = [
        ["First Name", "Last Name", "Email Address", "Monthly Salary"],
        ["John", "Doe", "john.doe@example.com", "5000.00"],
        ["Jane", "Smith", "jane.smith@example.com", "6000.00"],
        ["Bob", "Johnson", "bob.j@example.com", "5500.00"]
    ]
    worksheet.update(test_data, "A1:D4")
    
    spreadsheet = Spreadsheet(service_account_dict, sheet_id)
    
    employees = []
    for employee in spreadsheet.range("Sheet1!A1:D4").iter(Employee):
        employees.append(employee)
    
    assert len(employees) == 3
    assert isinstance(employees[0], Employee)
    assert employees[0].first_name == "John"
    assert employees[0].last_name == "Doe"
    assert employees[0].email_address == "john.doe@example.com"
    assert employees[0].monthly_salary == 5000.00
    assert employees[1].first_name == "Jane"
    assert employees[2].last_name == "Johnson"


def test_map_with_validation_alias():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()
    
    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)
    
    worksheet = sheet.sheet1
    worksheet.clear()
    
    test_data = [
        ["First Name", "Last Name", "Email Address", "Monthly Salary"],
        ["John", "Doe", "john.doe@example.com", "5000.00"],
        ["Jane", "Smith", "jane.smith@example.com", "6000.00"],
        ["Bob", "Johnson", "bob.j@example.com", "5500.00"]
    ]
    worksheet.update(test_data, "A1:D4")
    
    spreadsheet = Spreadsheet(service_account_dict, sheet_id)
    
    def give_raise(employee: Employee) -> Employee:
        employee.monthly_salary = employee.monthly_salary * 1.1
        return employee
    
    spreadsheet.range("Sheet1!A1:D4").map(give_raise, model=Employee)
    
    updated_values = worksheet.get("A1:D4")
    assert float(updated_values[1][3]) == pytest.approx(5500.00)
    assert float(updated_values[2][3]) == pytest.approx(6600.00)
    assert float(updated_values[3][3]) == pytest.approx(6050.00)


def test_multiple_fields_with_aliases():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()
    
    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)
    
    worksheet = sheet.sheet1
    worksheet.clear()
    
    test_data = [
        ["Product ID", "Product Name", "Unit Price", "Stock Quantity", "Is Active"],
        ["PRD001", "Widget A", "19.99", "100", "TRUE"],
        ["PRD002", "Gadget B", "29.99", "50", "TRUE"],
        ["PRD003", "Tool C", "49.99", "0", "FALSE"]
    ]
    worksheet.update(test_data, "A1:E4")
    
    spreadsheet = Spreadsheet(service_account_dict, sheet_id)
    
    products = []
    for product in spreadsheet.range("Sheet1!A1:E4").iter(Product):
        products.append(product)
    
    assert len(products) == 3
    assert products[0].product_id == "PRD001"
    assert products[0].product_name == "Widget A"
    assert products[0].unit_price == 19.99
    assert products[0].stock_quantity == 100
    assert products[0].is_active is True
    assert products[2].is_active is False


def test_mixed_fields_with_and_without_aliases():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()
    
    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)
    
    worksheet = sheet.sheet1
    worksheet.clear()
    
    test_data = [
        ["Customer ID", "Full Name", "email", "Phone Number", "status"],
        ["CUST001", "John Doe", "john@example.com", "+1-555-0101", "active"],
        ["CUST002", "Jane Smith", "jane@example.com", "+1-555-0102", "inactive"],
        ["CUST003", "Bob Wilson", "bob@example.com", "+1-555-0103", "active"]
    ]
    worksheet.update(test_data, "A1:E4")
    
    spreadsheet = Spreadsheet(service_account_dict, sheet_id)
    
    customers = []
    for customer in spreadsheet.range("Sheet1!A1:E4").iter(CustomerWithMixed):
        customers.append(customer)
    
    assert len(customers) == 3
    assert customers[0].customer_id == "CUST001"
    assert customers[0].full_name == "John Doe"
    assert customers[0].email == "john@example.com"
    assert customers[0].phone_number == "+1-555-0101"
    assert customers[0].status == "active"


def test_optional_fields_with_aliases():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()
    
    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)
    
    worksheet = sheet.sheet1
    worksheet.clear()
    
    test_data = [
        ["First Name", "Middle Name", "Last Name", "Age"],
        ["John", "Michael", "Doe", "30"],
        ["Jane", "", "Smith", ""],
        ["Bob", "William", "Johnson", "45"]
    ]
    worksheet.update(test_data, "A1:D4")
    
    spreadsheet = Spreadsheet(service_account_dict, sheet_id)
    
    people = []
    for person in spreadsheet.range("Sheet1!A1:D4").iter(PersonWithOptional):
        people.append(person)
    
    assert len(people) == 3
    assert people[0].first_name == "John"
    assert people[0].middle_name == "Michael"
    assert people[0].age == 30
    assert people[1].first_name == "Jane"
    assert people[1].middle_name is None
    assert people[1].age is None


def test_column_names_with_special_characters():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()
    
    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)
    
    worksheet = sheet.sheet1
    worksheet.clear()
    
    test_data = [
        ["Company (Name)", "Revenue ($USD)", "Growth Rate %", "Contact@Email"],
        ["Acme Corp", "1000000.00", "15.5", "contact@acme.com"],
        ["Global Inc", "2500000.00", "22.3", "info@global.com"],
        ["Tech Solutions", "750000.00", "18.7", "hello@techsol.com"]
    ]
    worksheet.update(test_data, "A1:D4")
    
    spreadsheet = Spreadsheet(service_account_dict, sheet_id)
    
    companies = []
    for company in spreadsheet.range("Sheet1!A1:D4").iter(DataWithSpecialChars):
        companies.append(company)
    
    assert len(companies) == 3
    assert companies[0].company_name == "Acme Corp"
    assert companies[0].revenue_usd == 1000000.00
    assert companies[0].growth_rate == 15.5
    assert companies[0].contact_email == "contact@acme.com"


def test_map_with_selective_update_using_aliases():
    service_account_dict = get_test_credentials()
    sheet_id = get_test_sheet_id()
    
    gspread_client = get_gspread_client()
    sheet = gspread_client.open_spreadsheet(sheet_id)
    
    worksheet = sheet.sheet1
    worksheet.clear()
    
    test_data = [
        ["Product ID", "Product Name", "Unit Price", "Stock Quantity", "Is Active"],
        ["PRD001", "Widget A", "19.99", "100", "TRUE"],
        ["PRD002", "Gadget B", "29.99", "50", "TRUE"],
        ["PRD003", "Tool C", "49.99", "0", "FALSE"]
    ]
    worksheet.update(test_data, "A1:E4")
    
    spreadsheet = Spreadsheet(service_account_dict, sheet_id)
    
    def adjust_price_for_active_products(product: Product) -> Product:
        if product.is_active and product.stock_quantity > 0:
            product.unit_price = product.unit_price * 0.9  # 10% discount
            return product
        return None
    
    spreadsheet.range("Sheet1!A1:E4").map(adjust_price_for_active_products, model=Product)
    
    updated_values = worksheet.get("A1:E4")
    assert float(updated_values[1][2]) == pytest.approx(17.991)
    assert float(updated_values[2][2]) == pytest.approx(26.991)
    assert updated_values[3][2] == "49.99"  # Unchanged because is_active is False