# Data Integrity Review

Review code for data consistency and reliability:

## Transaction Safety
- Database transaction boundaries
- Rollback on partial failures
- Atomic operations for related updates
- Concurrent modification handling

## Notification Reliability
- Duplicate notification prevention
- Email delivery confirmation
- Failed notification retry logic
- Notification state tracking

## State Management
- Alert status transitions
- Subscription state consistency
- User account state changes
- Payment status synchronization

## Race Conditions
- Concurrent alert evaluation
- Simultaneous user actions
- Scheduler job overlap
- Webhook processing conflicts

## Data Validation
- Input constraint enforcement
- Referential integrity
- Orphaned record prevention
- Soft delete consistency

Flag issues that could lead to data corruption or inconsistent state.
