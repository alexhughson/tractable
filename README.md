# tractable

Type-safe, async-first Python library for Google Sheets operations.

## Installation

```bash
pip install tractable
```

## Authentication

```python
from tractable import Spreadsheet

# Pass service account credentials as a dictionary
service_account_dict = {
    "type": "service_account",
    "project_id": "your-project",
    "private_key_id": "...",
    "private_key": "...",
    "client_email": "...",
    "client_id": "...",
    # ... other fields
}

# Create spreadsheet instance
sheet = await Spreadsheet(service_account_dict, "your-sheet-id")
```

## Core Operations

### Iterate - Read rows as typed models or dicts

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str
    score: float = 0.0

# Iterate with Pydantic model
async for user in sheet.range("A1:Z100").iter(User):
    print(f"{user.name}: {user.score}")

# Iterate as dicts (no model)
async for row in sheet.range("A1:Z100").iter():
    print(row["name"], row["email"])
```

### Map - Transform and update rows

```python
# Transform function - return None to skip update
async def boost_score(user: User) -> User:
    user.score *= 1.1
    return user

# Apply transformation to range
await sheet.range("A2:Z100").map(boost_score, model=User)

# Map without model (dict mode)
async def process_row(row: dict) -> dict:
    row["status"] = "processed"
    return row

await sheet.range("A2:Z100").map(process_row)
```

### Filter - Query without modification

```python
# Returns async iterator, doesn't modify sheet
async for user in sheet.range("A2:Z100").filter(User, lambda u: u.score > 50):
    print(user.name)

# Filter dicts
async for row in sheet.range("A2:Z100").filter(lambda r: r.get("active") == "yes"):
    print(row)
```

## Working with Ranges

```python
# Define ranges using A1 notation
# Ranges will treat the first row as a header
data_range = sheet.range("A1:E100")

# Define unbounded ranges
data_range = sheet.range("A:D")  # all rows

# Named ranges
summary = sheet.range("MonthlySummary")  # Uses named range

# Worksheet as range
users_sheet = sheet.range("Users")  # Entire worksheet
```

## Examples

### Simple data processing

```python
import asyncio
from tractable import Spreadsheet

async def main():
    # Setup auth - load your service account JSON
    service_account_dict = load_service_account_json()  # your implementation
    sheet = await Spreadsheet(service_account_dict, "your-sheet-id")

    # Read and process data
    total = 0
    async for user in sheet.range("Users!A2:Z").iter(User):
        total += user.score

    print(f"Total score: {total}")

    # Update scores
    async def normalize(user: User) -> User:
        if user.score > 100:
            user.score = 100
        return user

    await sheet.range("Users!A2:Z").map(normalize, model=User)

asyncio.run(main())
```

### Working without models

```python
# Pure dict operations
async for row in sheet.range("A2:Z").iter():
    if row.get("status") == "pending":
        row["status"] = "processing"
        await sheet.range(f"A{row['_row']}:Z{row['_row']}").map(lambda r: row)
```

## Notes

- All operations are async-first
- Map functions return `None` to skip updates, or the modified object to update
- Pydantic models are optional - use dicts for simpler cases
- Uses gspread authentication under the hood

## License

MIT