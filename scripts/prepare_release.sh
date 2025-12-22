#!/bin/bash
# Release Preparation Script for Mewtoo
# Usage: ./scripts/prepare_release.sh [version]

set -e

VERSION=${1:-$(cat VERSION)}
echo "Preparing release v${VERSION}..."

# Check if we're on main/master branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ] && [ "$BRANCH" != "master" ]; then
    echo "Warning: Not on main/master branch. Current branch: $BRANCH"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Error: You have uncommitted changes. Please commit or stash them first."
    exit 1
fi

# Run tests
echo "Running tests..."
pytest || {
    echo "Error: Tests failed. Fix tests before releasing."
    exit 1
}

# Verify version consistency
echo "Verifying version consistency..."
grep -q "$VERSION" VERSION || { echo "Error: VERSION file doesn't match"; exit 1; }
grep -q "$VERSION" main.py || { echo "Error: main.py doesn't match"; exit 1; }
grep -q "$VERSION" pokemon_agent.py || { echo "Error: pokemon_agent.py doesn't match"; exit 1; }

# Create tag
echo "Creating tag v${VERSION}..."
git tag -a "v${VERSION}" -m "Release v${VERSION}: Enhanced State Detection and Blank Screen Handling"

echo ""
echo "Release preparation complete!"
echo ""
echo "Next steps:"
echo "1. Review the tag: git show v${VERSION}"
echo "2. Push the tag: git push origin v${VERSION}"
echo "3. Create GitHub release using the tag"
echo "4. Use release notes from docs/RELEASE_NOTES.md"

