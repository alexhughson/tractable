"""
Spreadsheet class for tractable
"""
from .range import Range
from .connection_pool import get_connection_pool


class Spreadsheet:
    def __init__(self, service_account_dict, sheet_id):
        self.service_account_dict = service_account_dict
        self.sheet_id = sheet_id
        
        # Get or create the global connection pool
        pool = get_connection_pool(service_account_dict)
        
        # Get spreadsheet from pool (with automatic retry)
        self.spreadsheet = pool.open_spreadsheet(sheet_id)
    
    def range(self, range_name):
        return Range(self.spreadsheet, range_name)