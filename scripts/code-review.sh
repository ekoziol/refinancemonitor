#!/bin/bash
# code-review.sh - Claude Code integration for GitLab MR reviews
# Invokes Claude Code with MR context and posts review as comment

set -euo pipefail

# Required environment variables
: "${CI_MERGE_REQUEST_IID:?CI_MERGE_REQUEST_IID is required}"
: "${CI_PROJECT_PATH:?CI_PROJECT_PATH is required}"
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY is required}"
: "${GITLAB_TOKEN:?GITLAB_TOKEN is required}"

# Optional configuration
REVIEW_PROMPTS_DIR="${REVIEW_PROMPTS_DIR:-.claude/review-prompts}"
MAX_DIFF_LINES="${MAX_DIFF_LINES:-5000}"

# Collect MR metadata
echo "Collecting MR context for MR !${CI_MERGE_REQUEST_IID}..."

# Get MR description and metadata
MR_INFO=$(glab mr view "$CI_MERGE_REQUEST_IID" --output json 2>/dev/null || echo '{}')
MR_TITLE=$(echo "$MR_INFO" | jq -r '.title // "No title"')
MR_DESCRIPTION=$(echo "$MR_INFO" | jq -r '.description // "No description"')
TARGET_BRANCH=$(echo "$MR_INFO" | jq -r '.target_branch // "main"')
SOURCE_BRANCH=$(echo "$MR_INFO" | jq -r '.source_branch // "unknown"')

# Get changed files
CHANGED_FILES=$(glab mr diff "$CI_MERGE_REQUEST_IID" --name-only 2>/dev/null || git diff --name-only "origin/${TARGET_BRANCH}...HEAD")

# Get diff (truncated if too large)
DIFF=$(glab mr diff "$CI_MERGE_REQUEST_IID" 2>/dev/null || git diff "origin/${TARGET_BRANCH}...HEAD")
DIFF_LINES=$(echo "$DIFF" | wc -l)
if [ "$DIFF_LINES" -gt "$MAX_DIFF_LINES" ]; then
    echo "Warning: Diff truncated from $DIFF_LINES to $MAX_DIFF_LINES lines"
    DIFF=$(echo "$DIFF" | head -n "$MAX_DIFF_LINES")
    DIFF="${DIFF}

... [truncated - diff exceeded ${MAX_DIFF_LINES} lines]"
fi

# Load review prompts
PROMPTS=""
if [ -d "$REVIEW_PROMPTS_DIR" ]; then
    for prompt_file in "$REVIEW_PROMPTS_DIR"/*.md "$REVIEW_PROMPTS_DIR"/*.txt; do
        [ -f "$prompt_file" ] || continue
        echo "Loading prompt: $prompt_file"
        PROMPTS="${PROMPTS}

$(cat "$prompt_file")"
    done
fi

# Default prompt if none configured
if [ -z "$PROMPTS" ]; then
    PROMPTS="Review this merge request for:
- Code quality and best practices
- Potential bugs or security issues
- Performance concerns
- Test coverage gaps
- Documentation needs

Be concise and actionable. Focus on important issues."
fi

# Build the review request
REVIEW_REQUEST="# Merge Request Review

## MR Details
- **Title:** ${MR_TITLE}
- **Source:** ${SOURCE_BRANCH} -> ${TARGET_BRANCH}
- **MR:** !${CI_MERGE_REQUEST_IID}

## Description
${MR_DESCRIPTION}

## Changed Files
\`\`\`
${CHANGED_FILES}
\`\`\`

## Review Instructions
${PROMPTS}

## Diff
\`\`\`diff
${DIFF}
\`\`\`

Please provide a code review based on the instructions above."

# Create temp file for the request
REQUEST_FILE=$(mktemp)
echo "$REVIEW_REQUEST" > "$REQUEST_FILE"
trap 'rm -f "$REQUEST_FILE"' EXIT

# Invoke Claude Code
echo "Invoking Claude Code for review..."
REVIEW_OUTPUT=$(claude --print "$REVIEW_REQUEST" 2>&1) || {
    echo "Error: Claude Code invocation failed"
    echo "$REVIEW_OUTPUT"
    exit 1
}

# Format as GitLab comment
COMMENT="## :robot: Claude Code Review

${REVIEW_OUTPUT}

---
*Automated review by Claude Code*"

# Post comment to MR
echo "Posting review comment to MR !${CI_MERGE_REQUEST_IID}..."
glab mr comment "$CI_MERGE_REQUEST_IID" --message "$COMMENT"

echo "Review complete!"
