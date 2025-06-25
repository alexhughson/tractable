"""
Range class for tractable
"""
from typing import Optional, Type, TypeVar, Union
from pydantic import BaseModel


T = TypeVar('T', bound=BaseModel)


def parse_range_notation(range_string):
    if '!' in range_string:
        worksheet_name, cell_range = range_string.split('!', 1)
        worksheet_name = worksheet_name.strip("'\"")
        return worksheet_name, cell_range
    else:
        return None, range_string


def row_to_dict(headers, row):
    return dict(zip(headers, row))


def dict_to_model(model, row_dict):
    typed_data = {}
    for field_name, field_info in model.model_fields.items():
        if field_name in row_dict:
            value = row_dict[field_name]
            if value == "":
                if field_info.default is not None:
                    continue
                elif not field_info.is_required():
                    typed_data[field_name] = None
                    continue
            typed_data[field_name] = value
    
    if hasattr(model, 'model_config') and model.model_config.get('extra') == 'allow':
        for key, value in row_dict.items():
            if key not in model.model_fields:
                typed_data[key] = value
    
    return model(**typed_data)


def model_to_row(item, headers):
    new_row = []
    for header in headers:
        field_value = getattr(item, header, None)
        if field_value is None and hasattr(item, '__dict__'):
            field_value = item.__dict__.get(header)
        new_row.append(str(field_value) if field_value is not None else "")
    return new_row


def dict_to_row(item, headers):
    return [str(item.get(header, "")) for header in headers]


def format_update_range(worksheet_name, row_index, num_columns):
    col_end = chr(ord('A') + num_columns - 1)
    update_range = f"A{row_index}:{col_end}{row_index}"
    return update_range


class Range:
    def __init__(self, async_client, sheet_id, range_name):
        self.async_client = async_client
        self.sheet_id = sheet_id
        self.range_name = range_name
    
    async def iter(self, model: Optional[Type[T]] = None):
        spreadsheet = await self.async_client.open_by_key(self.sheet_id)
        
        worksheet_name, cell_range = parse_range_notation(self.range_name)
        
        if worksheet_name:
            worksheet = await spreadsheet.worksheet(worksheet_name)
        else:
            worksheets = await spreadsheet.worksheets()
            worksheet = worksheets[0]
        
        values = await worksheet.get(cell_range)
        
        if not values:
            raise ValueError("No data found in range")
        
        if len(values) < 2:
            return
        
        headers = values[0]
        for row in values[1:]:
            if all(cell == "" for cell in row):
                break
            
            row_dict = row_to_dict(headers, row)
            
            if model:
                yield dict_to_model(model, row_dict)
            else:
                yield row_dict
    
    async def map(self, transform_func, *, model: Optional[Type[T]] = None):
        worksheet = await self._get_worksheet()
        values = await self._get_values(worksheet)
        
        if not values or len(values) < 2:
            return
        
        headers = values[0]
        updates = await self._process_rows_for_update(
            values[1:], headers, transform_func, model
        )
        
        if updates:
            await worksheet.batch_update(updates)
    
    async def _get_worksheet(self):
        spreadsheet = await self.async_client.open_by_key(self.sheet_id)
        worksheet_name, _ = parse_range_notation(self.range_name)
        
        if worksheet_name:
            return await spreadsheet.worksheet(worksheet_name)
        else:
            worksheets = await spreadsheet.worksheets()
            return worksheets[0]
    
    async def _get_values(self, worksheet):
        _, cell_range = parse_range_notation(self.range_name)
        return await worksheet.get(cell_range)
    
    async def _process_rows_for_update(self, data_rows, headers, transform_func, model):
        updates = []
        row_index = 2
        
        for row in data_rows:
            if all(cell == "" for cell in row):
                break
            
            item = self._prepare_item(row, headers, model)
            transformed = await transform_func(item)
            
            if transformed is not None:
                update = self._create_update(transformed, headers, row_index, model)
                updates.append(update)
            
            row_index += 1
        
        return updates
    
    def _prepare_item(self, row, headers, model):
        row_dict = row_to_dict(headers, row)
        if model:
            return dict_to_model(model, row_dict)
        return row_dict
    
    def _create_update(self, transformed, headers, row_index, model):
        if model:
            new_row = model_to_row(transformed, headers)
        else:
            new_row = dict_to_row(transformed, headers)
        
        worksheet_name, _ = parse_range_notation(self.range_name)
        update_range = format_update_range(worksheet_name, row_index, len(headers))
        
        return {
            'range': update_range,
            'values': [new_row]
        }
    
