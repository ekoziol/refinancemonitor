# Performance Review

Analyze code changes for performance implications:

## Database Queries
- N+1 query problems
- Missing indexes for filtered queries
- Unbounded result sets
- Transaction scope and duration
- Connection pool usage

## Background Jobs
- Scheduler efficiency
- Job timeout handling
- Rate limiting for external APIs
- Batch processing opportunities

## API & External Calls
- HTTP connection pooling
- Timeout configurations
- Retry logic and backoff
- Response caching where appropriate

## Memory & Resources
- Large object handling
- File upload/processing
- Email batch processing
- Query result pagination

Suggest specific optimizations where bottlenecks are identified.
