# Performance & Scalability Review

Review this code for performance issues and scalability concerns.

## Critical Checks

### Database & API Efficiency
- [ ] No N+1 query patterns (fetching in loops)
- [ ] Bulk operations used where appropriate
- [ ] Connections properly pooled/reused
- [ ] Results paginated for large datasets

### Caching Strategy
- [ ] Expensive computations cached appropriately
- [ ] Cache invalidation logic is correct
- [ ] TTLs set appropriately for data freshness needs
- [ ] No cache stampede vulnerabilities

### Async Patterns
- [ ] I/O-bound operations don't block
- [ ] Background tasks for long-running operations
- [ ] Proper async/await usage (no blocking in async)
- [ ] Concurrent requests handled efficiently

### Memory & Resources
- [ ] Large datasets processed in chunks/streams
- [ ] File handles properly closed
- [ ] No unbounded list accumulation
- [ ] Resources released in finally/context managers

## Questions to Answer

1. What happens if this runs with 10x the data?
2. Are there API calls or DB queries inside loops?
3. Should any of this be cached or backgrounded?
4. Could this block the main thread?

## Red Flags

- `for item in items: db.query(...)` patterns
- Loading entire files into memory
- Synchronous HTTP calls in request handlers
- Missing connection timeouts
- `time.sleep()` in request paths
- Unbounded `list.append()` in loops

## refi_alert Specific

- Rate API calls should use caching (rates don't change per-second)
- Mortgage calculations are CPU-bound; batch where possible
- Historical data queries should be paginated
- Alert checks can be async/background
