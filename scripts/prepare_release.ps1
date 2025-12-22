# Release Preparation Script for Mewtoo (PowerShell)
# Usage: .\scripts\prepare_release.ps1 [version]

param(
    [string]$Version = (Get-Content VERSION).Trim()
)

Write-Host "Preparing release v$Version..." -ForegroundColor Cyan

# Check if we're on main/master branch
$Branch = git rev-parse --abbrev-ref HEAD
if ($Branch -ne "main" -and $Branch -ne "master") {
    Write-Host "Warning: Not on main/master branch. Current branch: $Branch" -ForegroundColor Yellow
    $Continue = Read-Host "Continue anyway? (y/n)"
    if ($Continue -ne "y" -and $Continue -ne "Y") {
        exit 1
    }
}

# Check for uncommitted changes
$Status = git status --porcelain
if ($Status) {
    Write-Host "Error: You have uncommitted changes. Please commit or stash them first." -ForegroundColor Red
    exit 1
}

# Run tests
Write-Host "Running tests..." -ForegroundColor Cyan
pytest
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Tests failed. Fix tests before releasing." -ForegroundColor Red
    exit 1
}

# Verify version consistency
Write-Host "Verifying version consistency..." -ForegroundColor Cyan
$VersionFile = Get-Content VERSION
if ($VersionFile -notmatch $Version) {
    Write-Host "Error: VERSION file doesn't match" -ForegroundColor Red
    exit 1
}

# Create tag
Write-Host "Creating tag v$Version..." -ForegroundColor Cyan
git tag -a "v$Version" -m "Release v$Version: Enhanced State Detection and Blank Screen Handling"

Write-Host ""
Write-Host "Release preparation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Review the tag: git show v$Version"
Write-Host "2. Push the tag: git push origin v$Version"
Write-Host "3. Create GitHub release using the tag"
Write-Host "4. Use release notes from docs/RELEASE_NOTES.md"

