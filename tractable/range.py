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
    # Convert empty strings to None for optional fields
    cleaned_data = {}
    for key, value in row_dict.items():
        if value == "":
            cleaned_data[key] = None
        else:
            cleaned_data[key] = value
    
    # Let Pydantic handle all validation, aliasing, and defaults
    return model(**cleaned_data)


def model_to_row(item, headers):
    # Get model data as dict
    model_data = item.model_dump(mode='python')
    
    # Build a mapping from validation_alias to field names
    model_class = type(item)
    alias_to_field = {}
    for field_name, field_info in model_class.model_fields.items():
        if hasattr(field_info, 'validation_alias') and field_info.validation_alias:
            alias_to_field[field_info.validation_alias] = field_name
    
    # Build row in order of headers
    new_row = []
    for header in headers:
        if header in alias_to_field:
            # Header matches a validation_alias
            field_name = alias_to_field[header]
            value = model_data.get(field_name)
        elif header in model_data:
            # Header matches a field name directly
            value = model_data.get(header)
        else:
            # Header not found
            value = None
        
        new_row.append(str(value) if value is not None else "")
    return new_row


def dict_to_row(item, headers):
    return [str(item.get(header, "")) for header in headers]


def format_update_range(worksheet_name, row_index, num_columns):
    col_end = chr(ord('A') + num_columns - 1)
    update_range = f"A{row_index}:{col_end}{row_index}"
    return update_range


class Range:
    def __init__(self, spreadsheet, range_name):
        self.spreadsheet = spreadsheet
        self.range_name = range_name
    
    def iter(self, model: Optional[Type[T]] = None):
        worksheet_name, cell_range = parse_range_notation(self.range_name)
        
        if worksheet_name:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
        else:
            worksheets = self.spreadsheet.worksheets()
            worksheet = worksheets[0]
        
        values = worksheet.get(cell_range)
        
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
    
    def map(self, transform_func, *, model: Optional[Type[T]] = None):
        worksheet = self._get_worksheet()
        values = self._get_values(worksheet)
        
        if not values or len(values) < 2:
            return
        
        headers = values[0]
        updates = self._process_rows_for_update(
            values[1:], headers, transform_func, model
        )
        
        if updates:
            worksheet.batch_update(updates)
    
    def _get_worksheet(self):
        worksheet_name, _ = parse_range_notation(self.range_name)
        
        if worksheet_name:
            return self.spreadsheet.worksheet(worksheet_name)
        else:
            worksheets = self.spreadsheet.worksheets()
            return worksheets[0]
    
    def _get_values(self, worksheet):
        _, cell_range = parse_range_notation(self.range_name)
        return worksheet.get(cell_range)
    
    def _process_rows_for_update(self, data_rows, headers, transform_func, model):
        updates = []
        row_index = 2
        
        for row in data_rows:
            # Check for empty row BEFORE trying to prepare the item
            if all(cell == "" for cell in row):
                break
            
            item = self._prepare_item(row, headers, model)
            transformed = transform_func(item)
            
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
    
    def reduce(self, reducer_func, *, initial, model: Optional[Type[T]] = None):
        accumulator = initial
        
        for item in self.iter(model):
            accumulator = reducer_func(accumulator, item)
        
        return accumulator