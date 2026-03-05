#!/usr/bin/env bash
# ==============================================================================
# Nemo — Main Branch Protection Setup
# ==============================================================================
# Configures branch protection rules for the 'main' branch using GitHub CLI.
#
# Prerequisites:
#   - GitHub CLI (gh) installed and authenticated: gh auth login
#   - Repository pushed to GitHub with a 'main' branch
#
# Usage:
#   chmod +x scripts/protect-main.sh
#   ./scripts/protect-main.sh
# ==============================================================================

set -euo pipefail

# ── Detect repo ──────────────────────────────────────────────────────────────
REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null || true)

if [[ -z "$REPO" ]]; then
    echo "❌  Could not detect GitHub repo. Make sure you're in the repo directory"
    echo "    and have pushed to GitHub with: git remote add origin <url>"
    exit 1
fi

echo "🔒  Setting up branch protection for: $REPO (main)"
echo ""

# ── Apply branch protection rules ────────────────────────────────────────────
# Uses the GitHub API directly via gh for full control over rulesets.

gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "/repos/$REPO/branches/main/protection" \
    --input - <<'EOF'
{
    "required_status_checks": {
        "strict": true,
        "contexts": [
            "Lint",
            "Test",
            "Build",
            "Lint — ai-service",
            "Lint — plugin-service",
            "Lint — workflow-service",
            "Lint — vector-service",
            "Test — ai-service",
            "Test — plugin-service",
            "Test — workflow-service",
            "Test — vector-service"
        ]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": false,
        "require_last_push_approval": false
    },
    "required_linear_history": true,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "restrictions": null,
    "required_conversation_resolution": true
}
EOF

echo ""
echo "✅  Branch protection applied to 'main'!"
echo ""
echo "Summary of rules:"
echo "  • PRs required to merge into main"
echo "  • At least 1 approving review required"
echo "  • Stale reviews dismissed on new pushes"
echo "  • All CI status checks must pass (lint, test, build)"
echo "  • Branch must be up-to-date before merging"
echo "  • Linear history enforced (no merge commits)"
echo "  • Force pushes and branch deletion blocked"
echo "  • Conversations must be resolved before merging"
echo "  • Rules enforced for admins too"
