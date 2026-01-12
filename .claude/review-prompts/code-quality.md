# Code Quality & Best Practices Review

Review this code for maintainability, readability, and adherence to Python best practices.

## Critical Checks

### DRY (Don't Repeat Yourself)
- [ ] No duplicated logic that should be extracted
- [ ] Common patterns abstracted into reusable functions
- [ ] Constants defined once, not scattered as magic numbers

### Error Handling
- [ ] Exceptions caught at appropriate levels
- [ ] User-friendly error messages (not raw tracebacks)
- [ ] Errors logged with sufficient context for debugging
- [ ] Graceful degradation where appropriate

### Type Safety
- [ ] Type hints on function signatures
- [ ] Return types specified
- [ ] Complex data structures properly typed
- [ ] No implicit `Any` types on public interfaces

### Readability
- [ ] Function names describe what they do
- [ ] Variable names are descriptive (not `x`, `tmp`, `data`)
- [ ] Complex logic has explanatory comments
- [ ] Functions are focused (single responsibility)

## Questions to Answer

1. Would a new developer understand this code in 5 minutes?
2. Is there logic that would break silently if assumptions change?
3. Are error cases handled or do they crash unexpectedly?
4. Could any of this be simplified?

## Red Flags

- Functions over 50 lines
- More than 3 levels of nesting
- Bare `except:` clauses
- Variables named `data`, `result`, `temp`, `x`
- Copy-pasted code blocks with minor variations
- Comments that say "TODO: fix this later"
