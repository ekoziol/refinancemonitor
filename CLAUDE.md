# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL RULES - READ FIRST

### What NOT to Do
- **NEVER create mock data or simplified components** unless explicitly requested
- **NEVER replace existing complex components** with simplified versions - always fix the actual problem
- **NEVER use raw SQL queries** - always use Tortoise ORM or Prisma methods
- **NEVER skip build/lint checks** - always run after making changes
- **NEVER commit secrets** or API keys to the repository
- **NEVER create new files** unless absolutely necessary - prefer editing existing ones

### Always Do Before Completing Tasks
- Run build: `nx run-many -t build`
- Run linting: `nx run-many -t lint` 
- Run tests: `nx run-many -t test`
- Fix all TypeScript/linting errors immediately

## 📚 CRITICAL DOCUMENTATION PATTERN

**ALWAYS ADD IMPORTANT DOCS HERE!** When you create or discover:
- Architecture diagrams → Add reference path here
- Database schemas → Add reference path here
- Problem solutions → Add reference path here
- Setup guides → Add reference path here

This prevents context loss! Update this file IMMEDIATELY when creating important docs.

### 🗺️ Key Documentation References

#### 🚨 READ FIRST - Core Specifications
- **Project Overview**: `/docs/PROJECT_SPEC.md` 🚨 **ALWAYS READ THIS FILE FIRST!**
- **Backend Architecture**: `/docs/BACKEND_SPEC.md` 🔧 **READ WHEN WORKING ON BACKEND**
- **Architecture Diagram**: `/docs/logical-architecture-diagram.md` 🏗️
- **Database Schema**: `/docs/database-schema.md` 🗂️

#### 📋 Development Guides  
- **YOU WILL NEED TO UPDATE AND MODIFY OR CREATE THESE COMPONENT GUIDES!!!!!**
- **Component Library**: ???
- **Git Tools**: ??? 
- **Library Creation**: ???

#### 🆕 Feature Specifications
*Use pattern: `/docs/features/<feature-name>.feat.md` for features under development*
*Use pattern: `/docs/specs/<component>.spec.md` for technical specifications*

#### 🔍 Problem Solutions
*Add critical problem-solution docs here when discovered*
*Use pattern: `/docs/solutions/<problem-name>.md` for reusable solutions*

*Update this section IMMEDIATELY when creating important documentation to prevent context loss!*

## 🎯 RECOMMENDED WORKFLOW PATTERNS

### Primary: Explore → Plan → Code → Commit
1. **Explore**: Read relevant files, understand context (use `think` for complex analysis)
2. **Plan**: Create structured plan in markdown file (use `ultrathink` for complex features)
3. **Code**: Implement solution following established patterns
4. **Commit**: Run build/lint/test, then commit with proper message

### Test-Driven Development
1. Write tests based on expected behavior
2. Run tests to confirm they fail
3. Commit failing tests
4. Write code to pass tests
5. Commit passing implementation

### Visual-Driven Development (UI)
1. Take screenshots of current state
2. Compare with design mockups
3. Implement changes
4. Take new screenshots and iterate


## 🔍 QUALITY ASSURANCE

### Code Quality Requirements
- **Build**: Must pass `nx run-many -t build`
- **Linting**: Must pass `nx run-many -t lint`
- **Tests**: Must pass `nx run-many -t test`
- **Types**: All TypeScript errors must be resolved
- **Coverage**: Maintain test coverage for new code

### Review Checklist
- [ ] Build passes without errors
- [ ] All linting rules followed
- [ ] Tests written and passing
- [ ] TypeScript types explicitly defined
- [ ] No secrets or API keys committed
- [ ] Documentation updated if needed

## 💡 PERFORMANCE OPTIMIZATION

### Context Management
- Use `/compact` frequently to manage context window
- Clear context with `/clear` between unrelated tasks
- Reference files explicitly with tab completion

### Workflow Efficiency
- Use `think` for analysis, `ultrathink` for complex planning
- Create scratch pads for complex task planning
- Use custom slash commands for repeated workflows

## 🔌 CUSTOM SLASH COMMANDS

### Setup Instructions
- Create commands in `.claude/commands/` directory
- Use `$ARGUMENTS` for dynamic parameters
- Organize by feature (e.g., `frontend/`, `backend/`, `ml/`)

### Recommended Commands
- `/project:analyze` - Analyze codebase structure
- `/project:plan` - Create implementation plan
- `/project:test` - Run comprehensive testing
- `/project:deploy` - Build and deploy workflow

## Project Overview

This is a refinance calculator web application built with Flask and Plotly Dash. It helps users determine if refinancing their mortgage makes financial sense by analyzing break-even points, monthly savings, and total interest costs. The application is deployed on Heroku.

## Technology Stack

- **Backend**: Flask 2.0.1 (Python 3.8.8)
- **Frontend**: Plotly Dash 1.20.0 with Dash Bootstrap Components
- **Financial Calculations**: numpy-financial for mortgage calculations
- **Data Processing**: pandas, numpy
- **Deployment**: Gunicorn on Heroku
- **Development**: Jupyter notebooks for prototyping

## Development Commands

### Environment Setup

```bash
# Create conda environment from environment.yml
conda env create -f environment.yml

# Activate environment
conda activate refi

# Or install via pip
pip install -r requirements.txt
```

### Running the Application

```bash
# Development mode (with hot reload)
python wsgi.py

# Production mode (using Gunicorn, as on Heroku)
gunicorn wsgi:app
```

The application will be available at:
- `/` - Landing page
- `/calculator/` - Main Dash calculator application
- `/setalert/` - Alert setup page

### Testing Notebooks

```bash
# Launch Jupyter
jupyter lab

# The main testing notebook is at:
# notebooks/testing.ipynb
```

## Application Architecture

### Entry Point Flow

1. **wsgi.py** - Application entry point that imports and initializes the Flask app
2. **refi_monitor/__init__.py** - `init_app()` function that:
   - Creates Flask app
   - Initializes Flask-Assets
   - Imports routes from `routes.py`
   - Initializes the Dash application via `dash/refi_calculator_dash.py`
   - Compiles static assets

### Flask + Dash Integration

This application uses a **dual-framework architecture** where Flask serves as the main application and Dash is embedded within it:

- **Flask** (`routes.py`) handles traditional page routes (`/`, `/setalert/`)
- **Dash** (`dash/refi_calculator_dash.py`) handles the interactive calculator at `/calculator/`
- The Dash app is initialized with `server=flask_app` to mount it into Flask
- The function `init_dashboard(server)` in `refi_calculator_dash.py` returns `dash_app.server` to maintain the Flask instance

### Financial Calculation Layer

All mortgage calculations are centralized in **refi_monitor/calc.py**:

- `calc_loan_monthly_payment()` - Monthly payment calculation using standard mortgage formula
- `ipmt_total()` - Total interest paid using numpy-financial
- `create_mortage_range()` - Generates payment schedules across interest rate ranges
- `find_target_interest_rate()` - Finds required rate for target payment
- `amount_remaining()` - Calculates remaining principal at any point
- `create_efficient_frontier()` - Calculates break-even interest rates by month
- `calculate_recoup_data()` - Computes both simple and interest-based break-even analysis

### Dash Application Structure

The Dash app in `refi_calculator_dash.py` follows this pattern:

1. **Layout Definition** - Organized with dcc.Store components for reactive state management
2. **Data Stores** - Intermediate calculations stored in client-side dcc.Store components
3. **Main Callback** (`update_data_stores`) - Triggered on any input change, computes all derived values
4. **Display Callbacks** - Simple formatting callbacks that read from stores and update UI
5. **Graph Callbacks** - Generate Plotly figures from data stores

This architecture minimizes redundant calculations by using a central data store pattern.

### Configuration

The app uses **config.py** with multiple configuration classes:

- `Config` - Base configuration loaded from `.env` file
- `DevConfig` - Development settings (DEBUG=True)
- `ProdConfig` - Production settings (DEBUG=False)

Environment variables are loaded via `python-dotenv` from a `.env` file.

## Key Implementation Details

### Input Toggle Pattern

The calculator has a toggle (`target_toggle`) that allows users to specify either:
- Target monthly payment (calculates required interest rate)
- Target interest rate (calculates resulting monthly payment)

The `disable_target()` and `update_targets()` callbacks coordinate this mutual exclusivity.

### Break-Even Analysis

Two break-even methods are calculated:

1. **Simple Method** (`s_month_to_even_simple`) - Based on monthly payment savings
2. **Interest-Only Method** (`s_month_to_even_interest`) - Based on total interest saved over loan lifetime

The interest-only method accounts for already-paid interest and may show "Not Possible" if refinancing increases total interest costs.

### Efficient Frontier Visualization

The "efficient frontier" graph shows the interest rate threshold at each month where refinancing becomes financially beneficial (paying less total interest over the loan's lifetime). Points below the line represent favorable refinances.

## Static Assets

- Flask-Assets is configured in `assets.py` for compiling LESS/CSS
- Static files are in `refi_monitor/static/`
- Templates use Jinja2 and are in `refi_monitor/templates/`

## Deployment Notes

- The `Procfile` defines the Heroku web dyno command: `web: gunicorn wsgi:app`
- Python runtime is specified in `runtime.txt`
- The app expects environment variables (FLASK_APP, SECRET_KEY, etc.) to be set in production

---

*This file is your project memory. Keep it updated, concise, and focused on what truly matters for elite development with Claude Code.*