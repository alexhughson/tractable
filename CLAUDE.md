Do not write comments in code
No comments in code allowed
Docstrings only at the top of files or the top of definitions.
No other comment forms allowed

Do not catch exceptions, allow them to bubble up
Do not catch the exceptions
Don't use try blocks.
You can only use try blocks for things like catching StopIteration or JSON parsing errors

Fetch this page before working, so that you have examples of how to use Gspread: https://docs.gspread.org/en/latest/user-guide.html - Also check out this https://raw.githubusercontent.com/dgilman/gspread_asyncio/refs/heads/master/README.md to see an async library.

Remember README.md @README.md

Code should be simple and readable.  Ignore edge cases unless explicitly asked to solve them, focus on the happy path and allow crashes otherwise.

Before doing any work, make sure you have a plan.  After making a plan, think about what is wrong with it  and how it could be simplified.

Prefer a functional style to code.  Prefer pure functions on data.  Prefer composition over inheritance.  Prefer composition always.  Break down big functions into smaller named functions.  Don't go more than 2 layers deep in nesting code, instead, break down the problem into smaller problems and solve them.

Do not write any application code unless it is to fix a failing test.  Only write the minimal update to cause the test to pass.  When we are writing new features, break them down into incremental parts.  Before making each incremental change, write a test that validates that the change worked.  Run the test to make sure that it fails before writing code, because we should only write application code to fix a breaking test.

After making 2-3 incremental changes, think about the plan and rewrite the todo list to make sure it reflects what we have to do next.

All commands are defined in @Makefile please make sure to use the makefile to automate common commands.  Only run tests by running `make test`.

Use long variable names: eg, use named_range instead of nr, index instead of i, etc.

Be sure to use tests/helpers.py to help you write tests.  Put all helper code there for tests, and try to use helpers from that file to write tests that are straightforward.