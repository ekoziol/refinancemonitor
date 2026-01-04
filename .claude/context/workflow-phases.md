# Workflow Phases and Development Lifecycle

## Complete Feature Development Lifecycle

The CCPM system follows a disciplined 5-phase approach that ensures every line of code traces back to specifications: **Brainstorm → Document → Plan → Execute → Track**.

## Phase 1: Product Planning

### Purpose
Transform ideas into comprehensive Product Requirements Documents that capture vision, user stories, success criteria, and constraints.

### Commands
```bash
/pm:prd-new feature-name        # Launch comprehensive brainstorming session
/pm:prd-edit feature-name       # Refine and modify existing PRD
/pm:prd-show feature-name       # Review PRD content
/pm:prd-list                    # View all PRDs with status
```

### Process Flow
1. **Guided Brainstorming**: Interactive session covering user needs, business requirements, technical constraints
2. **Stakeholder Analysis**: Identify affected users, systems, and team members
3. **Success Criteria Definition**: Measurable outcomes and acceptance criteria
4. **Constraint Documentation**: Technical, business, and resource limitations
5. **Vision Articulation**: Clear product vision and value proposition

### Outputs
- **File**: `.claude/prds/{feature-name}.md`
- **Content**: Complete PRD with user stories, acceptance criteria, constraints
- **Metadata**: Creation date, status, stakeholder information

### Quality Gates
- All stakeholder perspectives considered
- Clear, measurable success criteria defined
- Technical feasibility validated
- Business value articulated

## Phase 2: Implementation Planning  

### Purpose
Transform PRD into detailed technical implementation plan with architectural decisions, technical approach, and dependency mapping.

### Commands
```bash
/pm:prd-parse feature-name      # Convert PRD to technical epic
/pm:epic-edit feature-name      # Modify epic structure
/pm:epic-show feature-name      # Review epic details
```

### Process Flow
1. **Architecture Analysis**: Review PRD for technical implications
2. **Technology Selection**: Choose appropriate frameworks, libraries, patterns
3. **Dependency Mapping**: Identify system integration points
4. **Risk Assessment**: Technical and implementation risks
5. **Resource Planning**: Development effort and timeline estimates

### Outputs  
- **File**: `.claude/epics/{feature-name}/epic.md`
- **Content**: Technical specifications, architecture decisions, implementation approach
- **Metadata**: Creation date, estimated effort, dependencies

### Quality Gates
- Architecture decisions documented and justified
- All dependencies identified and mapped
- Implementation approach feasible with current resources
- Risk mitigation strategies defined

## Phase 3: Task Decomposition

### Purpose
Break epic into concrete, actionable tasks with acceptance criteria, effort estimates, and parallelization analysis.

### Commands
```bash
/pm:epic-decompose feature-name  # Break epic into implementable tasks
/pm:epic-refresh feature-name    # Update epic progress from task status
```

### Process Flow
1. **Work Breakdown**: Decompose epic into atomic, implementable units
2. **Dependency Analysis**: Map task interdependencies
3. **Parallelization Assessment**: Identify concurrent execution opportunities
4. **Effort Estimation**: Size tasks for development planning
5. **Acceptance Criteria**: Define completion criteria for each task

### Outputs
- **Files**: `.claude/epics/{feature-name}/001.md`, `002.md`, etc.
- **Content**: Detailed task descriptions, acceptance criteria, dependencies
- **Metadata**: Effort estimates, parallel execution flags, conflict indicators

### Quality Gates
- Tasks are atomic and independently implementable
- All dependencies clearly identified
- Acceptance criteria are specific and testable
- Parallelization opportunities maximized

## Phase 4: GitHub Synchronization

### Purpose  
Push epic and tasks to GitHub as issues with appropriate labels and relationships, enabling team collaboration and progress tracking.

### Commands
```bash
/pm:epic-sync feature-name      # Push epic and tasks to GitHub
/pm:epic-oneshot feature-name   # Decompose and sync in single operation
/pm:import                      # Import existing GitHub issues
/pm:sync                        # Full bidirectional sync
```

### Process Flow
1. **Epic Issue Creation**: Create parent epic issue with comprehensive description
2. **Task Issue Generation**: Create child issues for each task
3. **Relationship Establishment**: Link tasks to epic using sub-issue relationships
4. **Label Application**: Apply consistent labeling scheme
5. **Team Notification**: Alert stakeholders to new work items

### Outputs
- **GitHub Issues**: Epic and task issues with full descriptions
- **Issue Relationships**: Parent-child hierarchies via gh-sub-issue
- **Labels**: `epic:feature-name`, `task`, priority, and component labels
- **Local Updates**: Task files renamed to `{issue-number}.md`

### Quality Gates
- All issues created successfully with complete descriptions
- Relationships properly established and visible
- Labels applied consistently for filtering and organization
- Team members can access and understand work scope

## Phase 5: Parallel Execution

### Purpose
Implement tasks using specialized agents while maintaining progress updates and comprehensive audit trail.

### Commands
```bash
/pm:epic-start feature-name     # Initialize parallel development environment
/pm:issue-analyze 1234          # Identify parallel work streams
/pm:issue-start 1234            # Launch specialized agents for implementation
/pm:issue-sync 1234             # Push progress updates to GitHub
/pm:next                        # Get next priority task
```

### Process Flow
1. **Work Environment Setup**: Create isolated git worktree for development
2. **Parallel Stream Identification**: Analyze tasks for concurrent execution opportunities
3. **Agent Coordination**: Launch specialized agents for different work streams
4. **Progress Monitoring**: Track implementation progress across multiple agents  
5. **Quality Assurance**: Continuous testing and code quality validation

### Outputs
- **Git Worktree**: Isolated development environment (`../epic-{name}`)
- **Implementation Code**: Complete feature implementation across multiple files
- **Progress Updates**: Regular status updates posted to GitHub issues
- **Test Results**: Comprehensive test coverage and validation results

### Quality Gates
- All acceptance criteria met for completed tasks
- Code quality standards maintained (no partial implementations)
- Tests passing with comprehensive coverage
- Documentation updated appropriately

## Phase 6: Integration and Completion

### Purpose
Integrate completed work into main branch, update all tracking systems, and close development cycle.

### Commands
```bash
/pm:issue-close 1234           # Mark individual issues complete
/pm:epic-merge feature-name    # Integrate epic into main branch
/pm:epic-close feature-name    # Mark epic complete and clean up
/pm:clean                      # Archive completed work
```

### Process Flow
1. **Final Quality Check**: Comprehensive testing and code review
2. **Integration Testing**: Verify feature works in complete system context
3. **Branch Merge**: Clean merge of epic branch to main
4. **Status Updates**: Close all related issues and update tracking
5. **Documentation**: Update project documentation and context

### Outputs
- **Merged Code**: Feature fully integrated into main branch
- **Closed Issues**: All GitHub issues marked complete
- **Updated Context**: Project context files reflect new capabilities
- **Clean Repository**: No orphaned branches or temporary files

### Quality Gates  
- All tests passing in integrated environment
- No merge conflicts or integration issues
- All GitHub issues properly closed
- Documentation updated to reflect new functionality

## Daily Development Workflows

### Session Startup
```bash
/context:prime                  # Load project context
/pm:status                      # Review overall project status
/pm:next                        # Get next priority task with context
```

### Active Development
```bash
/pm:issue-start {issue-id}      # Begin work with specialized agents
# ... development work ...
/pm:issue-sync {issue-id}       # Push progress updates
```

### Session Completion
```bash
/pm:status                      # Review progress made
/pm:standup                     # Generate standup report
/pm:blocked                     # Check for any blocking issues
```

## Coordination Workflows

### Team Standup Integration
```bash
/pm:standup                     # Generate comprehensive status report
/pm:in-progress                 # List all active work
/pm:blocked                     # Identify impediments
```

### Project Health Monitoring
```bash
/pm:validate                    # Check system integrity
/pm:search "keyword"            # Search across all project content
/pm:sync                        # Sync with latest GitHub state
```

## Quality Assurance Integration

### Continuous Quality
- **Code Analysis**: Automated bug detection and logic tracing
- **Test Execution**: Comprehensive testing with verbose output
- **Context Preservation**: Maintain project knowledge across sessions
- **Progress Tracking**: Transparent audit trail from requirements to code

### Error Recovery Workflows
- **Failed Operations**: Graceful degradation and retry mechanisms  
- **Merge Conflicts**: Human escalation with clear resolution guidance
- **System Inconsistencies**: Automatic detection and repair recommendations
- **Context Loss**: Recovery from project context files and GitHub state

## Performance Optimization

### Parallel Execution Benefits
- **Traditional**: 1 epic → 3 issues → serial execution
- **CCPM**: 1 epic → 3 issues → 4 parallel streams each = **12 simultaneous agents**
- **Result**: 5-8x faster feature delivery for appropriate tasks

### Context Management Efficiency
- **Sub-agent Filtering**: Reduce context usage by ~90%
- **Information Persistence**: Knowledge maintained across sessions
- **Strategic Focus**: Main conversation stays clean and high-level
- **Resource Optimization**: Intelligent tool access and coordination