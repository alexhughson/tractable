"""
Centralized connection pool for Google Sheets API with automatic retry logic
"""
import time
import functools
from typing import TypeVar, Callable, Any
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError

T = TypeVar('T')


class SheetsConnectionPool:
    def __init__(self, service_account_dict, max_retries=5, initial_delay=2.0, backoff_factor=2.0):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        
        # Initialize gspread client
        credentials = Credentials.from_service_account_info(service_account_dict)
        scoped_credentials = credentials.with_scopes([
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets", 
            "https://www.googleapis.com/auth/drive",
        ])
        self.client = gspread.authorize(scoped_credentials)
        
        # Cache for opened spreadsheets
        self._spreadsheet_cache = {}
    
    def _with_retry(self, func: Callable[..., T]) -> T:
        """Execute a function with exponential backoff retry on rate limit errors"""
        delay = self.initial_delay
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func()
            except APIError as e:
                if e.response.status_code == 429:  # Rate limit exceeded
                    last_exception = e
                    if attempt < self.max_retries:
                        time.sleep(delay)
                        delay *= self.backoff_factor
                        continue
                raise
        
        if last_exception:
            raise last_exception
    
    def open_spreadsheet(self, sheet_id: str):
        """Open a spreadsheet by ID with caching and retry logic"""
        if sheet_id not in self._spreadsheet_cache:
            spreadsheet = self._with_retry(lambda: self.client.open_by_key(sheet_id))
            self._spreadsheet_cache[sheet_id] = SpreadsheetProxy(spreadsheet, self)
        return self._spreadsheet_cache[sheet_id]
    
    def execute_with_retry(self, func: Callable[[], T]) -> T:
        """Execute any function with retry logic"""
        return self._with_retry(func)


class SpreadsheetProxy:
    """Proxy for gspread.Spreadsheet that routes all operations through the connection pool"""
    def __init__(self, spreadsheet: gspread.Spreadsheet, pool: SheetsConnectionPool):
        self._spreadsheet = spreadsheet
        self._pool = pool
        self.id = spreadsheet.id
    
    @property
    def sheet1(self):
        """Get the first worksheet (sheet1) with retry logic"""
        worksheet = self._pool.execute_with_retry(lambda: self._spreadsheet.sheet1)
        return WorksheetProxy(worksheet, self._pool)
    
    def worksheet(self, title: str):
        """Get worksheet by title with retry logic"""
        worksheet = self._pool.execute_with_retry(lambda: self._spreadsheet.worksheet(title))
        return WorksheetProxy(worksheet, self._pool)
    
    def worksheets(self):
        """Get all worksheets with retry logic"""
        worksheets = self._pool.execute_with_retry(lambda: self._spreadsheet.worksheets())
        return [WorksheetProxy(ws, self._pool) for ws in worksheets]
    
    def add_worksheet(self, title: str, rows: int, cols: int):
        """Add a new worksheet with retry logic"""
        worksheet = self._pool.execute_with_retry(
            lambda: self._spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)
        )
        return WorksheetProxy(worksheet, self._pool)
    
    def del_worksheet(self, worksheet):
        """Delete a worksheet with retry logic"""
        # Handle both WorksheetProxy and gspread.Worksheet
        if isinstance(worksheet, WorksheetProxy):
            worksheet = worksheet._worksheet
        return self._pool.execute_with_retry(lambda: self._spreadsheet.del_worksheet(worksheet))


class WorksheetProxy:
    """Proxy for gspread.Worksheet that routes all operations through the connection pool"""
    def __init__(self, worksheet: gspread.Worksheet, pool: SheetsConnectionPool):
        self._worksheet = worksheet
        self._pool = pool
        self.title = worksheet.title
    
    def get(self, range_name: str = None):
        """Get values from range with retry logic"""
        return self._pool.execute_with_retry(lambda: self._worksheet.get(range_name))
    
    def batch_update(self, updates):
        """Batch update values with retry logic"""
        return self._pool.execute_with_retry(lambda: self._worksheet.batch_update(updates))
    
    def update(self, values, range_name=None):
        """Update values with retry logic"""
        return self._pool.execute_with_retry(lambda: self._worksheet.update(values, range_name))
    
    def clear(self):
        """Clear worksheet with retry logic"""
        return self._pool.execute_with_retry(lambda: self._worksheet.clear())
    
    def get_all_values(self):
        """Get all values from worksheet with retry logic"""
        return self._pool.execute_with_retry(lambda: self._worksheet.get_all_values())


# Global connection pool instance (singleton pattern)
_global_pool = None


def get_connection_pool(service_account_dict=None):
    """Get or create the global connection pool"""
    global _global_pool
    if _global_pool is None:
        if service_account_dict is None:
            raise ValueError("service_account_dict required for first initialization")
        _global_pool = SheetsConnectionPool(service_account_dict)
    return _global_pool