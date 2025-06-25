"""
Test Range.reduce method
"""
import pytest
from pydantic import BaseModel
from tractable import Spreadsheet
from tests.helpers import get_test_credentials, get_test_sheet_id, create_test_worksheet, cleanup_test_worksheet


class Product(BaseModel):
    name: str
    price: float
    quantity: int


def test_reduce_with_pydantic_model():
    worksheet = create_test_worksheet("ReduceModelTest", rows=10, cols=3)
    worksheet.update(values=[
        ["name", "price", "quantity"],
        ["Apple", "1.50", "10"],
        ["Banana", "0.75", "15"],
        ["Orange", "2.00", "8"],
        ["Grape", "3.50", "5"]
    ], range_name="A1:C5")
    
    sheet = Spreadsheet(get_test_credentials(), get_test_sheet_id())
    
    def calculate_total(accumulator, product):
        return accumulator + (product.price * product.quantity)
    
    total_value = sheet.range("ReduceModelTest!A1:C5").reduce(
        calculate_total,
        initial=0.0,
        model=Product
    )
    
    expected = (1.50 * 10) + (0.75 * 15) + (2.00 * 8) + (3.50 * 5)
    assert total_value == expected
    
    cleanup_test_worksheet("ReduceModelTest")


def test_reduce_with_dicts():
    worksheet = create_test_worksheet("ReduceDictTest", rows=10, cols=2)
    worksheet.update(values=[
        ["name", "score"],
        ["Player1", "100"],
        ["Player2", "250"],
        ["Player3", "175"],
        ["Player4", "300"]
    ], range_name="A1:B5")
    
    sheet = Spreadsheet(get_test_credentials(), get_test_sheet_id())
    
    def find_max_score(accumulator, row):
        score = int(row["score"])
        return max(accumulator, score)
    
    max_score = sheet.range("ReduceDictTest!A1:B5").reduce(
        find_max_score,
        initial=0
    )
    
    assert max_score == 300
    
    cleanup_test_worksheet("ReduceDictTest")


def test_reduce_empty_range():
    worksheet = create_test_worksheet("ReduceEmptyTest", rows=10, cols=2)
    worksheet.update(values=[["name", "value"]], range_name="A1:B1")
    
    sheet = Spreadsheet(get_test_credentials(), get_test_sheet_id())
    
    def sum_values(acc, row):
        return acc + int(row["value"])
    
    result = sheet.range("ReduceEmptyTest!A1:B10").reduce(
        sum_values,
        initial=0
    )
    
    assert result == 0
    
    cleanup_test_worksheet("ReduceEmptyTest")