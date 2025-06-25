"""
Spreadsheet class for tractable
"""
import gspread_asyncio
from gspread_asyncio import AsyncioGspreadClientManager
from google.oauth2.service_account import Credentials
from .range import Range


def create_credentials_function(service_account_dict):
    def get_credentials():
        credentials = Credentials.from_service_account_info(service_account_dict)
        scoped_credentials = credentials.with_scopes([
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ])
        return scoped_credentials
    return get_credentials


class Spreadsheet:
    def __init__(self, service_account_dict, sheet_id):
        self.service_account_dict = service_account_dict
        self.sheet_id = sheet_id
        credentials_function = create_credentials_function(service_account_dict)
        self.async_client_manager = AsyncioGspreadClientManager(credentials_function)
        self.async_client = None
        return self
    
    async def __new__(cls, service_account_dict, sheet_id):
        instance = object.__new__(cls)
        instance.__init__(service_account_dict, sheet_id)
        instance.async_client = await instance.async_client_manager.authorize()
        return instance
    
    def range(self, range_name):
        return Range(self.async_client, self.sheet_id, range_name)