# Project Architecture Alignment Review

Review this code for consistency with the refi_alert project structure and patterns.

## Project Structure Reference

```
refi_alert/
├── src/refi_alert/     # Core application code
│   ├── calc.py         # Financial calculations
│   ├── config.py       # Configuration management
│   ├── rates.py        # Rate fetching and caching
│   └── alert.py        # Alert logic
├── tests/              # Unit and integration tests
├── scripts/            # CLI and automation scripts
└── .claude/            # Claude Code configuration
```

## Critical Checks

### File Organization
- [ ] New code placed in appropriate module
- [ ] Tests alongside or mirroring source structure
- [ ] No business logic in scripts/
- [ ] Configuration separate from logic

### Import Patterns
- [ ] Standard library imports first
- [ ] Third-party imports second
- [ ] Local imports third (with blank lines between groups)
- [ ] No circular imports
- [ ] Relative imports within package

### Pattern Consistency
- [ ] Follows existing error handling patterns
- [ ] Uses project's logging conventions
- [ ] Matches naming conventions (snake_case functions, etc.)
- [ ] Configuration accessed through config module

### Coupling
- [ ] Modules have clear responsibilities
- [ ] Dependencies flow in one direction
- [ ] No hidden dependencies via global state
- [ ] Interface boundaries respected

## Questions to Answer

1. Does this change belong in this file/module?
2. Are there existing utilities this could reuse?
3. Does this follow the patterns established elsewhere?
4. Will this cause import issues or circular dependencies?

## Red Flags

- New top-level files without clear purpose
- Direct database/API access outside designated modules
- Hardcoded paths or environment-specific values
- Importing from tests/ in production code
- Deep imports into other module internals
