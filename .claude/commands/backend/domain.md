# Create New Backend Domain

Create a new backend domain following DDD patterns: $ARGUMENTS

## Domain Creation Process

1. **Domain Analysis**:
   - Analyze the domain requirements
   - Identify core entities and value objects
   - Define domain boundaries and relationships
   - Map to existing domains to avoid duplication

2. **Setup Domain Structure**:
   - Copy from example domain: `cp -r src/domains/example src/domains/$ARGUMENTS`
   - Update all identifiers from "example" to the new domain name
   - Rename files and classes appropriately

3. **Define Models**:
   - Create Tortoise ORM models in `models/models.py`
   - Define relationships with other domains
   - Add validation rules and constraints
   - Ensure database migrations are created

4. **Create Services**:
   - Implement business logic in `services/`
   - Follow existing patterns for async/sync operations
   - Add proper error handling and logging
   - Include input validation

5. **Setup CQRS**:
   - Create command and query handlers in `cqrs/`
   - Define DTOs for commands and queries
   - Implement proper separation of concerns
   - Add transaction management where needed

6. **Create API Endpoints**:
   - Implement router factory in `api/`
   - Define OpenAPI specifications
   - Add authentication and authorization
   - Include proper HTTP status codes

7. **Configure DI Container**:
   - Setup dependency injection in `di/`
   - Wire all services and handlers
   - Register with main container
   - Add to `module_paths.py`

8. **Testing**:
   - Create unit tests for all services
   - Add integration tests for API endpoints
   - Test database operations
   - Verify dependency injection works correctly

## Post-Creation Checklist

- [ ] Domain models created and validated
- [ ] Services implemented with proper error handling
- [ ] API endpoints documented and tested
- [ ] DI container configured and registered
- [ ] Tests written and passing
- [ ] Database migrations created
- [ ] Documentation updated