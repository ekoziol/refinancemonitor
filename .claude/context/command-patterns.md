# Command Patterns and Structure

## Command Architecture

### Standard Command Structure
```markdown
---
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, Task]
---

# Command: {command-name}

## Usage
{command} [arguments]

## Quick Check  
- Validates prerequisites and dependencies
- Checks for required configurations
- Verifies permissions and access

## Instructions
1. Detailed step-by-step execution logic
2. Error handling and validation points
3. Success criteria and outputs

## Error Handling
- Specific error conditions and responses
- Graceful degradation strategies
- User guidance for problem resolution
```

## Command Categories

### 1. PM Commands (36 total)
**PRD Management (6 commands)**
- `prd-new` - Create comprehensive PRD through guided brainstorming
- `prd-parse` - Transform PRD into technical implementation plan
- `prd-list` - Display all PRDs with status information
- `prd-edit` - Modify existing PRD content
- `prd-status` - Show PRD implementation progress
- `prd-show` - Display specific PRD details

**Epic Management (8 commands)**  
- `epic-decompose` - Break epic into concrete tasks with acceptance criteria
- `epic-sync` - Push epic and tasks to GitHub as issues
- `epic-oneshot` - Decompose and sync in single operation
- `epic-list` - Show all epics with status
- `epic-show` - Display epic details and task breakdown
- `epic-close` - Mark epic as complete and clean up
- `epic-edit` - Modify epic content and structure
- `epic-refresh` - Update epic progress from task status

**Issue Management (8 commands)**
- `issue-show` - Display issue details and sub-issues
- `issue-status` - Check current issue status and progress
- `issue-start` - Begin development with specialized agents
- `issue-sync` - Push local progress updates to GitHub
- `issue-close` - Mark issue complete and update epic
- `issue-reopen` - Reopen closed issue for additional work
- `issue-edit` - Modify issue content and metadata
- `issue-analyze` - Identify parallel work streams and dependencies

**Workflow Commands (7 commands)**
- `next` - Show next priority issue with full epic context
- `status` - Overall project dashboard with all active work
- `standup` - Generate daily standup report
- `blocked` - Identify and display blocked tasks
- `in-progress` - List all work currently in progress
- `sync` - Full bidirectional sync with GitHub
- `import` - Import existing GitHub issues into local system

**Maintenance Commands (7 commands)**
- `init` - Install dependencies and configure GitHub integration
- `validate` - Check system integrity and configuration
- `clean` - Archive completed work and optimize storage
- `search` - Search across all PRDs, epics, and tasks
- `epic-start` - Initialize parallel development environment
- `epic-merge` - Integrate completed epic into main branch
- `help` - Display command reference and usage

### 2. Context Commands (3 total)
- `context:create` - Generate comprehensive project context
- `context:update` - Refresh context with recent changes
- `context:prime` - Load context for development session

### 3. Testing Commands (2 total)  
- `testing:prime` - Prepare test environment and dependencies
- `testing:run` - Execute tests with comprehensive reporting

## Command Workflow Patterns

### 1. Feature Development Lifecycle
```bash
# Planning Phase
/pm:prd-new memory-system
/pm:prd-parse memory-system

# Decomposition Phase  
/pm:epic-decompose memory-system
/pm:epic-sync memory-system

# Execution Phase
/pm:epic-start memory-system
/pm:issue-start 1234
/pm:issue-sync 1234

# Completion Phase
/pm:issue-close 1234
/pm:epic-merge memory-system
```

### 2. Daily Development Pattern
```bash
# Session Start
/context:prime
/pm:next

# Work Progress
/pm:issue-start {issue-id}
/pm:issue-sync {issue-id}

# Session End  
/pm:status
/pm:standup
```

### 3. Project Health Monitoring
```bash
# System Status
/pm:validate
/pm:blocked
/pm:in-progress

# Synchronization
/pm:sync
/pm:import
```

## Tool Permission Patterns

### Standard Tool Set
Most commands use: `[Bash, Read, Write, Edit, Glob, Grep, Task]`

### Specialized Tool Usage
- **GitHub Integration**: Commands requiring `gh` CLI access
- **Git Operations**: Commands needing git repository manipulation  
- **File System**: Commands creating/modifying project structure
- **Agent Coordination**: Commands using Task tool for sub-agent execution

## Error Handling Patterns

### 1. Prerequisites Validation
```markdown
## Quick Check
- [ ] GitHub CLI installed and authenticated
- [ ] Current directory is git repository  
- [ ] Required directories exist (.claude/epics/, .claude/prds/)
- [ ] No conflicting operations in progress
```

### 2. Graceful Degradation
```markdown
## Error Handling
If gh-sub-issue extension unavailable:
- Fall back to task lists in epic descriptions
- Maintain parent-child relationships manually
- Provide guidance for manual relationship creation
```

### 3. User Guidance
```markdown
## Common Issues
- **Permission denied**: Run `gh auth login` to authenticate
- **Repository not found**: Verify correct repository URL
- **Merge conflicts**: Use `/pm:epic-merge` with conflict resolution
```

## Command Coordination Patterns

### 1. State Dependencies
- PRD must exist before epic parsing
- Epic must be decomposed before GitHub sync
- Issues must be analyzed before parallel execution starts

### 2. Concurrent Operations
- Multiple agents can work on same epic simultaneously
- File-level coordination prevents conflicts
- Progress tracking through shared status files

### 3. Rollback Strategies  
- Incomplete operations can be safely abandoned
- GitHub issues remain as source of truth
- Local state can be reconstructed from remote data

## Best Practices

### 1. Command Composition
- Use `epic-oneshot` for confident workflows
- Break complex operations into smaller, validated steps
- Always validate state before destructive operations

### 2. Error Recovery
- Check system status after failed operations
- Use `validate` command to identify configuration issues
- Leverage `sync` command to repair state inconsistencies

### 3. Performance Optimization
- Use parallel execution for independent tasks
- Cache frequently accessed data locally
- Minimize API calls through intelligent batching