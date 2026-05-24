#!/usr/bin/env bash
# scripts/sync-github.sh — Sanitized push to the public GitHub remote.
#
# Reads .github-exclude for internal-only paths, creates a temporary
# branch with those paths removed, and force-pushes to github:main.
# If HEAD carries a tag, the tag is forwarded to the sanitized commit.
#
# Usage:
#   ./scripts/sync-github.sh              # normal sync
#   ./scripts/sync-github.sh --dry-run    # show what would happen without pushing

set -euo pipefail

REMOTE="github"
BRANCH="main"
EXCLUDE_FILE=".github-exclude"
TEMP_BRANCH="__github_sync_temp__"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
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

# ── Detect tag at HEAD ───────────────────────────────────────────────────────
ORIGINAL_SHA=$(git rev-parse HEAD)
HEAD_TAG=$(git tag --points-at HEAD 2>/dev/null | head -n1 || true)
if [[ -n "$HEAD_TAG" ]]; then
    echo "🏷️  Tag detected at HEAD: $HEAD_TAG"
fi

# ── Create sanitized branch from HEAD ────────────────────────────────────────
# Clean up any leftover temp branch from a previous failed run
git branch -D "$TEMP_BRANCH" &>/dev/null || true

echo "🔨 Creating sanitized snapshot from HEAD..."

# Create a real branch at HEAD (not orphan — preserves the index correctly)
git checkout -b "$TEMP_BRANCH" --quiet

# Remove excluded paths from the working tree AND index
for path in "${EXCLUDES[@]}"; do
    if git ls-files --error-unmatch "$path" &>/dev/null 2>&1; then
        git rm -r --quiet "$path" 2>/dev/null || true
    elif [[ -d "$path" ]] && git ls-tree --name-only HEAD "${path%/}" &>/dev/null 2>&1; then
        git rm -r --quiet "$path" 2>/dev/null || true
    fi
done

# Also strip the .github-exclude file itself — public repo shouldn't know about it
git rm --quiet .github-exclude 2>/dev/null || true

# Commit the sanitized tree (amend to avoid a separate "removal" commit)
ORIGINAL_MSG=$(git log -1 --format='%s' HEAD)
git commit --quiet --allow-empty --amend \
    -m "$ORIGINAL_MSG" \
    -m "Sanitized sync from internal commit ${ORIGINAL_SHA:0:10}" \
    -m "Excluded $((${#EXCLUDES[@]} + 1)) internal paths per .github-exclude"

SANITIZED_SHA=$(git rev-parse HEAD)
echo "✅ Sanitized commit: ${SANITIZED_SHA:0:8}"

# ── List what was stripped (verification) ────────────────────────────────────
echo ""
echo "📦 Sanitized tree contents (top-level):"
git ls-tree --name-only HEAD | while read -r name; do
    echo "   ✓ $name"
done

echo ""
echo "🔒 Verifying exclusions are absent..."
ALL_CLEAN=true
for path in "${EXCLUDES[@]}"; do
    # Strip trailing slash for tree lookup
    clean_path="${path%/}"
    if git ls-tree --name-only HEAD | grep -qx "$clean_path"; then
        echo "   ❌ STILL PRESENT: $path"
        ALL_CLEAN=false
    else
        echo "   ✓ Stripped: $path"
    fi
done

# Also verify .github-exclude itself was stripped
if git ls-tree --name-only HEAD | grep -qx ".github-exclude"; then
    echo "   ❌ STILL PRESENT: .github-exclude"
    ALL_CLEAN=false
else
    echo "   ✓ Stripped: .github-exclude"
fi

if [[ "$ALL_CLEAN" != "true" ]]; then
    echo "❌ Exclusion verification failed. Aborting push."
    git checkout main --quiet
    git branch -D "$TEMP_BRANCH" --quiet
    exit 1
fi

# ── Push to GitHub ───────────────────────────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
    echo ""
    echo "🔍 DRY RUN: Would force-push ${SANITIZED_SHA:0:8} to $REMOTE/$BRANCH"
    if [[ -n "$HEAD_TAG" ]]; then
        echo "🔍 DRY RUN: Would push tag $HEAD_TAG to $REMOTE"
    fi
else
    echo ""
    echo "🚀 Force-pushing sanitized snapshot to $REMOTE/$BRANCH..."
    git push "$REMOTE" "$TEMP_BRANCH:$BRANCH" --force

    if [[ -n "$HEAD_TAG" ]]; then
        echo "🏷️  Pushing tag $HEAD_TAG to $REMOTE..."
        # Delete the old tag on remote first (it points to the unsanitized commit)
        git push "$REMOTE" ":refs/tags/$HEAD_TAG" 2>/dev/null || true
        # Create a new lightweight tag at the sanitized commit
        git tag -f "$HEAD_TAG" "$SANITIZED_SHA" --quiet
        git push "$REMOTE" "$HEAD_TAG"
        # Restore the original tag to point at the real internal commit
        git tag -f "$HEAD_TAG" "$ORIGINAL_SHA" --quiet
    fi
fi

# ── Cleanup ──────────────────────────────────────────────────────────────────
git checkout main --quiet
git branch -D "$TEMP_BRANCH" --quiet 2>/dev/null || true

echo ""
echo "✅ GitHub sync complete."
if [[ -n "$HEAD_TAG" ]]; then
    echo "   📦 Release tag $HEAD_TAG forwarded to sanitized commit."
fi
echo "   🔗 Internal (origin): full history preserved"
echo "   🌐 Public (github):   sanitized snapshot pushed"
