#!/bin/bash
# Enforce CHANGELOG.md updates when src/ files are committed.
# Minor/maintenance commits (fix:, chore:, ci:, style:, docs:, test:)
# are auto-exempt. All other commits must include a CHANGELOG.md update.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only applies to git commit commands
echo "$COMMAND" | grep -qE '(^|[[:space:]])git[[:space:]]+commit([[:space:]]|$)' || exit 0

# Only when src/ files are staged (or will be staged via -a/--all)
if echo "$COMMAND" | grep -qE '(^|[[:space:]])(-a|--all)([[:space:]]|$)'; then
    STAGED=$( { git diff --cached --name-only 2>/dev/null; git diff --name-only 2>/dev/null; } | sort -u )
else
    STAGED=$(git diff --cached --name-only 2>/dev/null)
fi
echo "$STAGED" | grep -q '^src/' || exit 0

# Pass if CHANGELOG.md is already staged
echo "$STAGED" | grep -q '^CHANGELOG.md$' && exit 0

# Auto-exempt minor/maintenance commits (only detectable when using -m)
echo "$COMMAND" | grep -qE -- '-m[[:space:]]+["'"'"']?(fix|chore|ci|style|docs|test)[:(]' && exit 0

echo "BLOCK: src/ files are staged but CHANGELOG.md has no staged changes." >&2
echo "Either update CHANGELOG.md and stage it, or use an appropriate" >&2
echo "semantic commit prefix (fix:, chore:, ci:, style:, docs:, test:)" >&2
echo "if the change does not warrant a changelog entry." >&2
exit 2
