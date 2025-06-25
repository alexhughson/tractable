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


@pytest.mark.asyncio
async def test_reduce_with_pydantic_model():
    worksheet = create_test_worksheet("ReduceModelTest", rows=10, cols=3)
    worksheet.update(range_name="A1:C5", values=[
        ["name", "price", "quantity"],
        ["Apple", "1.50", "10"],
        ["Banana", "0.75", "15"],
        ["Orange", "2.00", "8"],
        ["Grape", "3.50", "5"]
    ])
    
    sheet = await Spreadsheet(get_test_credentials(), get_test_sheet_id())
    
    async def calculate_total(accumulator, product):
        return accumulator + (product.price * product.quantity)
    
    total_value = await sheet.range("ReduceModelTest!A1:C5").reduce(
        calculate_total,
        initial=0.0,
        model=Product
    )
    
    expected = (1.50 * 10) + (0.75 * 15) + (2.00 * 8) + (3.50 * 5)
    assert total_value == expected
    
    cleanup_test_worksheet("ReduceModelTest")


@pytest.mark.asyncio
async def test_reduce_with_dicts():
    worksheet = create_test_worksheet("ReduceDictTest", rows=10, cols=2)
    worksheet.update(range_name="A1:B5", values=[
        ["name", "score"],
        ["Player1", "100"],
        ["Player2", "250"],
        ["Player3", "175"],
        ["Player4", "300"]
    ])
    
    sheet = await Spreadsheet(get_test_credentials(), get_test_sheet_id())
    
    async def find_max_score(accumulator, row):
        score = int(row["score"])
        return max(accumulator, score)
    
    max_score = await sheet.range("ReduceDictTest!A1:B5").reduce(
        find_max_score,
        initial=0
    )
    
    assert max_score == 300
    
    cleanup_test_worksheet("ReduceDictTest")


@pytest.mark.asyncio
async def test_reduce_empty_range():
    worksheet = create_test_worksheet("ReduceEmptyTest", rows=10, cols=2)
    worksheet.update(range_name="A1:B1", values=[["name", "value"]])
    
    sheet = await Spreadsheet(get_test_credentials(), get_test_sheet_id())
    
    async def sum_values(acc, row):
        return acc + int(row["value"])
    
    result = await sheet.range("ReduceEmptyTest!A1:B10").reduce(
        sum_values,
        initial=0
    )
    
    assert result == 0
    
    cleanup_test_worksheet("ReduceEmptyTest")
