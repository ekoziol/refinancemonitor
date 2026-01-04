# Agent Coordination and Specialization

## Agent Architecture Overview

The CCPM system uses specialized sub-agents to optimize context usage while maintaining development efficiency. Each agent type serves specific purposes and coordinates through well-defined interfaces.

## Agent Types and Specializations

### 1. Parallel-Worker Agent
**Purpose**: Coordinates multiple simultaneous work streams within single epics

**Capabilities**:
- Manages git worktree isolation for parallel development
- Coordinates file-level access to prevent conflicts
- Tracks progress across multiple simultaneous implementations
- Handles merge coordination and conflict resolution

**Usage Patterns**:
```bash
/pm:epic-start memory-system  # Initializes parallel work environment
/pm:issue-analyze 1234       # Identifies parallel work streams
```

**Coordination Strategy**:
- Creates separate worktree (`../epic-{name}`) for development isolation
- Assigns specific file patterns to each work stream
- Uses dependency graphs to sequence dependent operations
- Provides conflict detection with human escalation

### 2. Code-Analyzer Agent  
**Purpose**: Specialized code analysis, bug hunting, and logic tracing

**Capabilities**:
- Deep code analysis with minimal context pollution
- Bug detection and vulnerability identification
- Logic flow tracing across complex codebases
- Performance bottleneck identification

**Usage Patterns**:
- Automatically invoked for code analysis tasks
- Used by issue-start command for codebase understanding
- Integrated into quality assurance workflows

**Information Filtering**:
- Processes verbose code analysis results
- Returns concise, actionable summaries
- Highlights critical issues and patterns
- Reduces context usage by ~85-90%

### 3. File-Analyzer Agent
**Purpose**: Optimizes context by summarizing verbose file outputs

**Capabilities**:
- Extracts critical information from log files
- Summarizes verbose command outputs
- Processes large configuration files
- Handles binary file analysis

**Usage Patterns**:
- Always used when reading large or complex files
- Integrated into command output processing
- Automatically invoked for log analysis

**Context Optimization**:
- Reduces file content to essential information
- Maintains critical details while filtering noise
- Provides structured summaries for decision making
- Preserves actionable insights

### 4. Test-Runner Agent
**Purpose**: Handles test execution with clean context management

**Capabilities**:
- Executes comprehensive test suites
- Captures full test output for debugging
- Analyzes test failures and provides guidance
- Maintains test environment isolation

**Usage Patterns**:
```bash
/testing:run                 # Execute full test suite
/pm:issue-start 1234        # Includes testing in implementation
```

**Quality Integration**:
- Ensures verbose test output for debugging
- Never uses mock services (tests against real implementations)
- Completes current test before moving to next
- Validates test structure before refactoring

## Agent Coordination Patterns

### 1. Context Firewall Strategy
**Problem**: Main conversation gets polluted with implementation details
**Solution**: Sub-agents handle complex operations, return concise summaries

**Implementation**:
- Main thread maintains strategic oversight
- Agents process verbose outputs in isolation
- Information flows back as structured summaries
- Context window stays clean for high-level coordination

### 2. Parallel Execution Coordination
**Traditional Approach**: 1 epic → 3 issues → serial execution
**CCPM Approach**: 1 epic → 3 issues → 4 parallel streams each = 12 agents

**Coordination Mechanisms**:
- **File-Level Assignment**: Each agent gets specific file patterns
- **Dependency Sequencing**: Dependent tasks wait for prerequisites  
- **Conflict Detection**: Shared files trigger coordination protocols
- **Progress Synchronization**: Regular status updates across agents

### 3. Error Isolation and Recovery
**Agent Failure Handling**:
- Individual agent failures don't cascade to main workflow
- Failed operations can be retried with different agents
- Error context preserved for debugging without main thread pollution
- Graceful degradation when specialized agents unavailable

## Agent Communication Protocols

### 1. Task Assignment Interface
```markdown
Agent: parallel-worker
Task: Implement user authentication system
Files: src/auth/*.js, tests/auth/*.test.js  
Dependencies: [database-migration-123]
Conflicts: [shared-config.json]
```

### 2. Progress Reporting Interface  
```markdown
Status: in-progress
Completed: 
- Database migration scripts
- Service layer implementation
Remaining:
- API endpoint integration  
- UI component updates
Blockers: None
```

### 3. Error Escalation Interface
```markdown
Error: Merge conflict detected
Files: src/config/database.js
Description: Concurrent modifications to connection pooling
Resolution: Manual merge required
Recommendation: Human review of conflict resolution
```

## Workflow Integration Patterns

### 1. Command → Agent Handoff
Commands identify appropriate agent based on:
- Task complexity and scope
- Required tool access permissions
- Context optimization needs
- Specialization requirements

### 2. Agent → Agent Coordination
Agents coordinate through:
- Shared progress files in epic directories
- Git commit messages with coordination info
- Dependency tracking in task metadata
- Explicit conflict flagging mechanisms

### 3. Agent → Human Escalation
Escalation triggers:
- Merge conflicts requiring business logic decisions
- Architecture decisions outside agent scope
- Quality gate failures requiring review
- Resource conflicts needing prioritization

## Performance Optimization Strategies

### 1. Context Memory Management
- Sub-agents prevent context window overflow
- Strategic information filtering at agent boundaries  
- Persistent context files maintain project knowledge
- Regular context cleanup and optimization

### 2. Parallel Processing Efficiency
- Independent work streams execute simultaneously
- Dependency graphs minimize blocking operations
- File-level granularity prevents unnecessary conflicts
- Resource pooling across multiple agents

### 3. Tool Access Optimization  
- Agents receive minimal required tool permissions
- Specialized tools assigned to appropriate agent types
- Resource access coordinated to prevent conflicts
- Permission escalation only when necessary

## Quality Assurance Integration

### 1. Agent Specialization Benefits
- **Code-Analyzer**: Catches bugs early in development cycle
- **Test-Runner**: Ensures comprehensive testing coverage
- **File-Analyzer**: Maintains clean documentation standards
- **Parallel-Worker**: Coordinates quality across work streams

### 2. Error Prevention Patterns
- Validation at agent assignment boundaries
- Pre-execution compatibility checking
- Resource conflict detection before work begins
- Quality gate enforcement at completion

### 3. Continuous Integration
- Agents integrate with existing CI/CD pipelines
- Test results feed back into development coordination
- Code quality metrics influence agent assignment
- Performance monitoring guides optimization efforts

## Best Practices for Agent Utilization

### 1. Agent Selection
- Use parallel-worker for large, decomposable features
- Employ code-analyzer for complex bug investigation
- Leverage file-analyzer for verbose output processing
- Deploy test-runner for comprehensive quality assurance

### 2. Coordination Efficiency
- Minimize cross-agent dependencies
- Design file access patterns to reduce conflicts
- Use git as coordination mechanism between agents
- Implement clear escalation paths for human intervention

### 3. Performance Monitoring
- Track agent utilization and efficiency metrics
- Monitor context usage across agent boundaries
- Measure parallel execution speedup factors
- Optimize agent assignment based on historical performance