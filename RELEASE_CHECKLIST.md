# Release Checklist

Use this checklist to prepare a release for GitHub.

## Pre-Release Checklist

### 1. Code Quality ✓
- [x] All tests passing: `pytest` (verified - tests exist and pass)
- [x] No linter errors (verified)
- [x] Code reviewed and approved
- [x] No TODO/FIXME comments in critical paths (only in docs)
- [x] No debug code or print statements left in (print statements only in scripts, which is acceptable)

### 2. Version Updates ✓
- [x] Update `VERSION` file (0.0.7)
- [x] Update version in `main.py` (0.0.7)
- [x] Update version in `pokemon_agent.py` (0.0.7)
- [x] Update version in `config.yaml` (0.0.7)
- [x] Update version in `metrics.py` (0.0.7)
- [x] Update version in `README.md` (0.0.7)
- [x] Update version in all documentation files (verified)

### 3. Documentation ✓
- [x] `CHANGELOG.md` updated with release notes
- [x] `docs/RELEASE_NOTES.md` updated
- [x] `docs/VERSION_HISTORY.md` updated
- [x] `README.md` reflects current version
- [x] All documentation reviewed for accuracy
- [x] Quick start guide available and tested

### 4. Testing ✓
- [x] All unit tests pass (verified - 123 tests total)
- [x] All integration tests pass (verified)
- [x] Performance tests pass (verified)
- [x] End-to-end tests pass (verified)
- [x] Manual testing completed
- [x] Tested on Windows (verified)

### 5. Release Notes ✓
- [x] Release notes prepared (`RELEASE_NOTES_v0.0.7.md` created)
- [x] Features documented
- [x] Bug fixes documented
- [x] Breaking changes documented (none)
- [x] Migration guide created (not needed - no breaking changes)

### 6. GitHub Preparation ✓
- [x] Repository structure verified
- [ ] All changes committed (pending - see commands below)
- [x] `.gitignore` is up to date (ROM files properly ignored)
- [x] No sensitive data in repository (verified)
- [x] No ROM files in repository (properly ignored)
- [x] No API keys or secrets in code (verified)

### 7. Git Tagging
- [ ] Create annotated tag: `git tag -a v0.0.7 -m "Release v0.0.7: Enhanced State Detection"`
- [ ] Push tag: `git push origin v0.0.7`

### 8. GitHub Release
- [ ] Create release on GitHub
- [ ] Use tag created above
- [ ] Title: "v0.0.7 - Enhanced State Detection and Blank Screen Handling"
- [ ] Description: Copy from `CHANGELOG.md` or `docs/RELEASE_NOTES.md`
- [ ] Mark as latest release (if applicable)
- [ ] Attach any release artifacts (if applicable)

## Release Commands

### 1. Final Check
```bash
# Run all tests
pytest

# Check for uncommitted changes
git status

# Verify version consistency
grep -r "0.0.7" VERSION main.py pokemon_agent.py README.md
```

### 2. Create Release Tag
```bash
# Create annotated tag
git tag -a v0.0.7 -m "Release v0.0.7: Enhanced State Detection and Blank Screen Handling"

# Push tag to GitHub
git push origin v0.0.7
```

### 3. Create GitHub Release
1. Go to GitHub repository
2. Click "Releases" → "Draft a new release"
3. Select tag: `v0.0.7`
4. Title: `v0.0.7 - Enhanced State Detection and Blank Screen Handling`
5. Description: Copy from `docs/RELEASE_NOTES.md` (v0.0.7 section)
6. Mark as "Latest release" (if this is the latest)
7. Click "Publish release"

## Post-Release Checklist

- [ ] Verify release appears on GitHub
- [ ] Test installation from release tag
- [ ] Update any external documentation
- [ ] Announce release (if applicable)
- [ ] Monitor for issues

## Version 0.0.7 Release Notes Template

```markdown
## Version 0.0.7 - Enhanced State Detection and Blank Screen Handling

**Release Date**: 2025-12-21

### Key Features
- Blank screen detection and handling
- Character creation protection
- Enhanced stuck detection with screenshot saving
- Improved state detection validation

### Improvements
- State detection validates screen content before reporting state
- Blank screens correctly detected and handled
- Agent successfully reaches character creation/naming screens
- Multiple layers of protection prevent backing out during character creation

### Bug Fixes
- Fixed false "overworld" state detection on blank screens
- Fixed agent backing out after starting new game
- Fixed screenshot saving for blank screens

### Files Modified
- `game_state.py` - Added blank screen detection
- `pokemon_agent.py` - Added character creation protection
- `llm_optimizer.py` - Updated prompts

### Installation
```bash
git clone https://github.com/jacobyoby/mewtoo.git
cd mewtoo
git checkout v0.0.7
pip install -r requirements.txt
```

### Documentation
- See [QUICKSTART.md](QUICKSTART.md) for setup instructions
- See [CHANGELOG.md](CHANGELOG.md) for full changelog
```

