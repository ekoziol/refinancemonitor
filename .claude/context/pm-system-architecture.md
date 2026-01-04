# PM System Architecture

## System Overview

Claude Code PM (CCPM) is a sophisticated project management framework that orchestrates multiple AI agents to handle complex software development workflows. The system enables spec-driven development with parallel execution, full GitHub integration, and comprehensive context preservation.

## Core Architecture

### Directory Structure
```
.claude/
├── commands/           # 43 total commands across 3 categories
│   ├── pm/            # 36 project management commands  
│   ├── context/       # 3 context management commands
│   └── testing/       # 2 test execution commands
├── agents/            # 4 specialized agent types
├── rules/             # 10 operational guideline files
├── scripts/           # Bash implementation layer
├── context/           # Project knowledge management
├── epics/             # Epic and task storage (gitignored)
└── prds/              # Product Requirements Documents
```

### Component Relationships

**Commands → Agents → Rules → Scripts**
- Commands define high-level workflows and allowed tools
- Agents handle specialized implementation details
- Rules provide consistent operational guidelines  
- Scripts offer reusable bash implementation patterns

### Key Architectural Patterns

#### 1. Hierarchical Task Decomposition
- **PRDs** define product requirements and vision
- **Epics** break features into manageable technical chunks
- **Tasks** represent atomic, implementable work units
- **Issues** provide GitHub tracking and team coordination

#### 2. Parallel Processing Architecture  
- File-level parallelism prevents merge conflicts
- Dependency management ensures correct execution ordering
- Conflict detection with human escalation
- Resource coordination across multiple simultaneous agents

#### 3. Context Optimization Strategy
- Sub-agents handle verbose/complex operations
- Main conversation stays clean and strategic
- Information filtering reduces context usage by ~90%
- Knowledge persistence across development sessions

## Integration Points

### Git Workflow
- Single epic branch for related tasks (not per-task branches)
- Development in separate worktrees (`../epic-{name}`)
- Atomic commits: `Issue #{number}: {specific change}`
- Coordination through git status checks and coordination

### GitHub Integration
- Issues as single source of truth for project state
- Epic-task hierarchical relationships via `gh-sub-issue`
- Automatic labeling: `epic:feature-name`, `task`, etc.
- Repository protection prevents accidental sync to templates

### Development Tools
- GitHub CLI (`gh`) for all GitHub operations
- Permission system for safe command execution
- Cross-platform bash script compatibility
- Extension-based feature enhancement (graceful degradation)

## Data Management

### Frontmatter System
```yaml
---
name: feature-name
status: in-progress  # backlog → in-progress → completed
created: 2024-01-15T10:30:00Z
updated: 2024-01-15T14:45:00Z
github: https://github.com/owner/repo/issues/123
---
```

### File Naming Conventions
- PRDs: `{feature-name}.md`
- Epics: `{feature-name}/epic.md` 
- Tasks: `001.md` → `{issue-number}.md` (after GitHub sync)
- Analysis: `{issue-number}-analysis.md`

### Dependency Tracking
- `depends_on: [123, 456]` - Issue number dependencies
- `parallel: true` - Indicates concurrent execution capability
- `conflicts_with: [789]` - File-level conflict identification

## Quality Assurance Integration

### Error Handling Philosophy
- **Fail Fast**: Critical configuration errors stop execution
- **Graceful Degradation**: Reduced functionality when components unavailable
- **Clear Error Messages**: Actionable guidance for problem resolution
- **Human Escalation**: Complex conflicts defer to human judgment

### Quality Gates
- No partial implementations allowed
- Mandatory testing with verbose output for debugging
- Automated code analysis and bug hunting
- Complete feature delivery or rollback

## System Strengths

- **Scalability**: Single features to complex multi-epic initiatives
- **Flexibility**: Adapts to different development patterns and team structures
- **Safety**: Multiple safeguards prevent destructive operations
- **Efficiency**: Parallel execution reduces development time significantly  
- **Traceability**: Complete audit trail from requirements to implementation
- **Persistence**: Context system maintains project knowledge across sessions