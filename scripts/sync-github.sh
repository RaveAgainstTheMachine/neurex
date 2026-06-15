#!/usr/bin/env bash
# scripts/sync-github.sh — Sanitized Orphan Squash Push to the public GitHub remote.
#
# Creates an isolated temporary git worktree sandbox, strips all internal-only
# files per .github-exclude, commits the clean workspace as a single-commit history
# (orphan), and force-pushes it to github:[branch].
# If HEAD carries a tag, the tag is forwarded to the sanitized commit.
#
# Usage:
#   ./scripts/sync-github.sh [branch]              # normal sync to target branch (defaults to active branch)
#   ./scripts/sync-github.sh [branch] --dry-run    # show what would happen without pushing

set -euo pipefail

REMOTE="github"
EXCLUDE_FILE=".github-exclude"
TEMP_BRANCH="__github_sync_temp__"
WORKTREE_DIR="${PWD}/__github_sync_worktree__"
DRY_RUN=false
BRANCH=""

# Parse arguments
for arg in "$@"; do
    if [[ "$arg" == "--dry-run" ]]; then
        DRY_RUN=true
    elif [[ "$arg" != -* ]]; then
        BRANCH="$arg"
    fi
done

# Detect current local branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ -z "$BRANCH" ]]; then
    BRANCH="$CURRENT_BRANCH"
fi

if [[ "$DRY_RUN" == "true" ]]; then
    echo "🔍 DRY RUN — no pushes will be made."
fi

# ── Preflight checks ─────────────────────────────────────────────────────────
if ! git remote get-url "$REMOTE" &>/dev/null; then
    echo "❌ Remote '$REMOTE' not configured. Aborting."
    exit 1
fi

if [[ ! -f "$EXCLUDE_FILE" ]]; then
    echo "❌ Exclusion manifest '$EXCLUDE_FILE' not found. Aborting."
    exit 1
fi

# Ensure working tree is clean
if [[ -n "$(git status --porcelain)" ]]; then
    echo "❌ Working tree is dirty. Commit or stash changes first."
    exit 1
fi

# ── Read exclusion list ──────────────────────────────────────────────────────
EXCLUDES=()
while IFS= read -r line; do
    # Skip comments and empty lines
    line="${line%%#*}"
    line="$(echo "$line" | xargs)"
    [[ -z "$line" ]] && continue
    EXCLUDES+=("$line")
done < "$EXCLUDE_FILE"

if [[ ${#EXCLUDES[@]} -eq 0 ]]; then
    echo "⚠️  No exclusions found in '$EXCLUDE_FILE'. Pushing as-is."
fi

echo "📋 Exclusion manifest loaded: ${#EXCLUDES[@]} paths"
for path in "${EXCLUDES[@]}"; do
    echo "   ✗ $path"
done

# ── Gather active commit metadata ──────────────────────────────────────────
ORIGINAL_SHA=$(git rev-parse HEAD)
ORIGINAL_MSG=$(git log -1 --format='%s' HEAD)
HEAD_TAG=$(git tag --points-at HEAD 2>/dev/null | head -n1 || true)
if [[ -n "$HEAD_TAG" ]]; then
    echo "🏷️  Tag detected at HEAD: $HEAD_TAG"
fi

# ── Setup Isolated Worktree Sandbox ──────────────────────────────────────────
echo "🔨 Initializing isolated git worktree sandbox..."
# Clean up any remnants from previous failed runs
git worktree prune &>/dev/null || true
rm -rf "$WORKTREE_DIR" &>/dev/null || true

# Add a detached worktree at the current HEAD
git worktree add --detach "$WORKTREE_DIR" HEAD --quiet

# Enter the sandbox directory
cd "$WORKTREE_DIR"

# ── Convert Worktree to Orphan Branch ────────────────────────────────────────
echo "🧹 Creating history-free (orphan) sanitized snapshot..."
git branch -D "$TEMP_BRANCH" &>/dev/null || true
git checkout --orphan "$TEMP_BRANCH" --quiet

# Unstage everything so we can build the index from scratch
git reset --quiet

# Remove excluded paths from the sandbox filesystem
for path in "${EXCLUDES[@]}"; do
    rm -rf "$path" 2>/dev/null || true
done

# Also strip the .github-exclude file itself from public view
rm -f .github-exclude 2>/dev/null || true

# Add all remaining sanitized files to the orphan index
git add -A --all --force

# Commit the sanitized files as a single, parentless release commit
git commit --quiet --allow-empty \
    -m "$ORIGINAL_MSG" \
    -m "Sanitized mirror snapshot from Gitea commit ${ORIGINAL_SHA:0:10}" \
    -m "Excluded $((${#EXCLUDES[@]} + 1)) internal paths per exclusion manifest."

SANITIZED_SHA=$(git rev-parse HEAD)
echo "✅ Sanitized commit created: ${SANITIZED_SHA:0:8}"

# ── Verify Exclusion Absence ──────────────────────────────────────────────────
echo "🔒 Verifying exclusions are absent in sanitized tree..."
ALL_CLEAN=true
for path in "${EXCLUDES[@]}"; do
    clean_path="${path%/}"
    if git ls-tree --name-only HEAD | grep -qx "$clean_path"; then
        echo "   ❌ STILL PRESENT: $path"
        ALL_CLEAN=false
    else
        echo "   ✓ Stripped: $path"
    fi
done

if git ls-tree --name-only HEAD | grep -qx ".github-exclude"; then
    echo "   ❌ STILL PRESENT: .github-exclude"
    ALL_CLEAN=false
else
    echo "   ✓ Stripped: .github-exclude"
fi

if [[ "$ALL_CLEAN" != "true" ]]; then
    echo "❌ Exclusion verification failed. Aborting."
    cd - >/dev/null
    git worktree remove "$WORKTREE_DIR" --force
    exit 1
fi

# ── Force-Push to GitHub ──────────────────────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
    echo ""
    echo "🔍 DRY RUN: Would force-push ${SANITIZED_SHA:0:8} as a history-free commit to $REMOTE/$BRANCH"
    if [[ -n "$HEAD_TAG" ]]; then
        echo "🔍 DRY RUN: Would push release tag $HEAD_TAG to $REMOTE"
    fi
else
    echo ""
    echo "🚀 Force-pushing sanitized history-free commit to $REMOTE/$BRANCH..."
    git push "$REMOTE" "$TEMP_BRANCH:$BRANCH" --force

    if [[ -n "$HEAD_TAG" ]]; then
        echo "🏷️  Pushing sanitized tag $HEAD_TAG to $REMOTE..."
        # Force overwrite the tag on the public remote pointing to the sanitized single-commit state
        git push "$REMOTE" ":refs/tags/$HEAD_TAG" 2>/dev/null || true
        git tag -f "$HEAD_TAG" "$SANITIZED_SHA"
        git push "$REMOTE" "$HEAD_TAG"
    fi
fi

# ── Cleanup ──────────────────────────────────────────────────────────────────
echo "🧹 Cleaning up worktree sandbox..."
cd - >/dev/null

# Remove the temporary worktree and clean internal git refs
git worktree remove "$WORKTREE_DIR" --force
git branch -D "$TEMP_BRANCH" --quiet &>/dev/null || true

# If a tag was forwarded and overridden locally, restore the original Gitea tag pointing to our rich dev history
if [[ "$DRY_RUN" != "true" && -n "$HEAD_TAG" ]]; then
    git tag -f "$HEAD_TAG" "$ORIGINAL_SHA"
fi

echo ""
echo "✅ GitHub sync complete."
if [[ -n "$HEAD_TAG" ]]; then
    echo "   📦 Release tag $HEAD_TAG forwarded to public sanitized commit."
fi
echo "   🔗 Gitea (origin): full developer history preserved"
echo "   🌐 GitHub (github):  purged of history & sanitized"
