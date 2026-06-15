# Release Policy

This document defines the rules for tagging, building, and publishing Neurex releases.

## Core Rules

1. **Minimum Validation Gate**: 
   - `make test` must pass locally.
   - `make lint` must pass locally (this includes the version drift check).
   - No exceptions.

2. **Cooldown Period**:
   - There is a **minimum 1-hour cooldown** between tagged releases.
   - If a critical hotfix is needed within 1 hour of a release, **do not bump the version**. Instead, delete the prior tag on Gitea (`origin`), re-cut the tag with the fix included, and allow the pipeline to run.

3. **Batch Rule**:
   - Accumulate related fixes on `main` and cut a single release when the batch is stable. Do not ship rapid-fire releases (e.g., v0.15.3 followed by v0.15.4 four minutes later).

4. **Docs-Only Changes**:
   - Use `make release-docs` with `[skip ci]`.
   - Never bump the version number for documentation-only changes.

## Dual-Remote Release Lifecycle

Neurex uses a dual-remote sync model:
- **Gitea (`origin`)**: Internal development. Tags here are **mutable**.
- **GitHub (`github`)**: Public mirror. Releases and assets here are **strictly immutable**.

### Gitea (Internal)
Tags on Gitea can be deleted and recreated during the 1-hour cooldown window if a hotfix is needed before public announcement.

### GitHub (Public)
Attempting to overwrite, delete, or re-upload assets for an existing tag via the GitHub release workflows will cause validation failures. If a release asset on GitHub is broken and the 1-hour cooldown has passed, you **MUST** increment the patch version (e.g., `v0.15.4` -> `v0.15.5`) and push a new release tag. Do NOT attempt to rewrite history on the GitHub remote.

## Changelog Extraction

GitHub Release bodies must contain ONLY the changelog section for the current tag. The CI workflow (`release.yml`) automatically extracts the relevant section from `CHANGELOG.md` via a Python regex parser. Never manually attach the full changelog history to a release.
