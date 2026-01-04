# Documentation Management and Generation

Comprehensive documentation review and generation for: $ARGUMENTS

## Documentation Audit and Organization

1. **Current Documentation Review**:
   - Audit existing documentation for accuracy and completeness
   - Identify outdated or inconsistent information
   - Check for broken links and missing references
   - Validate code examples and installation instructions

2. **Documentation Architecture**:
   - Ensure hierarchical organization follows patterns
   - Verify proper use of `.feat.md` for features in development
   - Check `.spec.md` files for technical specifications
   - Organize solution documentation in `/docs/solutions/`

3. **Content Quality Assessment**:
   - Technical accuracy and up-to-date information
   - Clear and consistent writing style
   - Proper code syntax highlighting
   - Comprehensive but concise explanations

## Documentation Patterns and Standards

### File Naming Conventions
```
/docs/
├── PROJECT_SPEC.md          # 🚨 ALWAYS READ FIRST
├── BACKEND_SPEC.md          # Backend-specific guide
├── logical-architecture-diagram.md
├── features/                # Features under development
│   ├── mmm-optimization.feat.md
│   └── real-time-dashboard.feat.md
├── specs/                   # Technical specifications
│   ├── authentication.spec.md
│   └── api-design.spec.md
└── solutions/              # Problem-solution documentation
    ├── azure-deployment.md
    └── performance-optimization.md
```

### Documentation Hierarchy
1. **Core Specifications** (Always read first)
   - `PROJECT_SPEC.md` - Master project overview
   - `BACKEND_SPEC.md` - Backend implementation guide
   - Architecture diagrams and ERDs

2. **Development Guides** (Reference as needed)
   - Component library documentation
   - Development tool guides
   - Setup and configuration instructions

3. **Feature Documentation** (Active development)
   - `*.feat.md` - Features being implemented
   - Include architecture, components, testing

4. **Problem Solutions** (Reusable knowledge)
   - Common issues and solutions
   - Troubleshooting guides
   - Best practices documentation

## Documentation Generation Tasks

### API Documentation
```bash
# Generate OpenAPI/Swagger documentation
cd apps/backend
poetry run python -c "
import json
from src.main import app
with open('api-docs.json', 'w') as f:
    json.dump(app.openapi(), f, indent=2)
"

# Generate API client documentation
swagger-codegen generate -i api-docs.json -l typescript-fetch -o frontend/src/generated
```

### Code Documentation
```bash
# Generate Python docstring documentation
cd apps/backend
poetry run pydoc-markdown

# Generate TypeScript documentation
cd apps/frontend
npx typedoc src/ --out docs/typescript
```

### Database Documentation
```bash
# Generate database schema documentation
cd apps/backend
poetry run python -c "
from tortoise import Tortoise, run_async
from tortoise.utils import get_schema_sql

async def generate_schema():
    await Tortoise.init(db_url='sqlite://:memory:', modules={'models': ['src.domains.forecast.models']})
    schema = get_schema_sql(Tortoise.get_connection('default'), safe=True)
    with open('database-schema.sql', 'w') as f:
        f.write(schema)

run_async(generate_schema())
"
```

## Documentation Content Creation

### Feature Documentation Template
```markdown
# Feature Name - Technical Specification

## Overview
Brief description of the feature purpose and scope.

## Architecture
### Technology Stack
- List of technologies and versions
- Dependencies and integrations
- Performance considerations

### Key Components
- Component descriptions
- Interaction patterns
- Data flow diagrams

## Implementation Plan
### Phase 1: Foundation
- [ ] Core infrastructure
- [ ] Basic models and services
- [ ] Initial API endpoints

### Phase 2: Enhancement
- [ ] Advanced features
- [ ] Performance optimization
- [ ] Integration testing

## Testing Strategy
- Unit testing approach
- Integration testing scenarios
- Performance validation
- Security considerations

## Documentation Links
- [Back to Project Overview](/docs/PROJECT_SPEC.md)
- [Related Backend Specification](/docs/BACKEND_SPEC.md)
```

### Problem-Solution Template
```markdown
# Problem: [Clear Problem Statement]

## Context
Description of when and why this problem occurs.

## Root Cause
Technical explanation of the underlying issue.

## Solution
Step-by-step resolution process.

## Prevention
How to avoid this problem in the future.

## Related Issues
Links to similar problems and solutions.

## Last Updated
Date and author of last update.
```

## Documentation Maintenance

### Regular Review Checklist
- [ ] All code examples work with current versions
- [ ] Installation instructions are accurate
- [ ] External links are functional
- [ ] Screenshots and diagrams are up-to-date
- [ ] Version numbers match current releases

### Content Updates
```bash
# Update documentation after major changes
# 1. Review affected documentation files
# 2. Update version numbers and compatibility info
# 3. Refresh code examples and outputs
# 4. Update installation and setup instructions
# 5. Regenerate API documentation if needed
```

### Documentation Testing
```bash
# Test documentation code examples
cd docs/examples
python test_examples.py

# Validate markdown formatting
markdownlint docs/**/*.md

# Check for broken links
markdown-link-check docs/**/*.md
```

## Integration with Development Workflow

### Git Hooks for Documentation
```bash
# Pre-commit hook to validate documentation
#!/bin/sh
# Check for updated documentation when code changes
if git diff --cached --name-only | grep -E '\.(py|ts|tsx)$'; then
    echo "Code changes detected. Please review documentation:"
    echo "- Update relevant .spec.md files"
    echo "- Add problem solutions if applicable" 
    echo "- Update API documentation if needed"
fi
```

### Continuous Documentation
- Update documentation as part of feature development
- Include documentation review in code review process
- Automate documentation generation where possible
- Link documentation to specific code versions

## Documentation Quality Metrics

### Completeness Metrics
- API endpoint documentation coverage
- Code comment density
- Feature documentation completeness
- Setup guide accuracy

### Usability Metrics
- Documentation search effectiveness
- User feedback and questions
- Time to find information
- Onboarding success rate

## Automated Documentation Tools

### Setup Documentation Generation
```bash
# Install documentation tools
pip install mkdocs mkdocs-material
pip install sphinx sphinx-rtd-theme
npm install -g @compodoc/compodoc

# Generate comprehensive documentation site
mkdocs build
compodoc -p tsconfig.json -s
```

### Documentation Publishing
```bash
# Deploy documentation to GitHub Pages
mkdocs gh-deploy

# Generate PDF documentation
pandoc docs/*.md -o artemis-documentation.pdf
```

## Action Items Checklist

### Immediate Actions
- [ ] Audit all existing documentation for accuracy
- [ ] Fix broken links and outdated information
- [ ] Organize files according to hierarchy patterns
- [ ] Update CLAUDE.md documentation references

### Short-term Actions
- [ ] Create missing feature specification files
- [ ] Document common problems and solutions
- [ ] Set up automated documentation generation
- [ ] Implement documentation review process

### Long-term Actions
- [ ] Establish documentation standards and guidelines
- [ ] Create interactive documentation portal
- [ ] Implement automated testing of documentation
- [ ] Set up metrics tracking for documentation usage

---

*This command helps maintain comprehensive, accurate, and well-organized documentation for the Artemis MMM platform.*