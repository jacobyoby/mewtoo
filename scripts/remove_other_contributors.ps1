# Script to remove all commits from other contributors, keeping only Jacobrakai's commits
# WARNING: This is a destructive operation that rewrites git history

$ErrorActionPreference = "Stop"

$yourName = "Jacobrakai"
$yourEmail = "45674026+jacobyoby@users.noreply.github.com"

Write-Host "Removing commits from all other contributors..."
Write-Host "Keeping only commits from: $yourName <$yourEmail>"
Write-Host ""

# Set git config
git config user.name $yourName
git config user.email $yourEmail

Write-Host "Step 1: Creating backup branch..."
git branch backup-before-filter 2>$null
Write-Host "Backup created at branch 'backup-before-filter'"

Write-Host "`nStep 2: Filtering commits (this may take a few minutes)..."
$env:FILTER_BRANCH_SQUELCH_WARNING = "1"

# Use git filter-branch with commit-filter (without --prune-empty)
# We'll manually skip commits from other authors
git filter-branch -f --commit-filter "
if [ `$GIT_AUTHOR_NAME = '$yourName' ] || [ `$GIT_AUTHOR_EMAIL = '$yourEmail' ]; then
    git commit-tree `$@;
else
    # Skip this commit
    true;
fi
" --tag-name-filter cat -- --all

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nError during filter-branch. Restoring from backup..."
    git reset --hard backup-before-filter
    exit 1
}

Write-Host "`nStep 3: Pruning empty commits..."
# Remove empty commits manually
git filter-branch -f --prune-empty --tag-name-filter cat -- --all

Write-Host "`nStep 4: Cleaning up..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

Write-Host "`nDone! Checking results..."
$yourCommits = git log --oneline --author="$yourName" | Measure-Object -Line
$totalCommits = git log --oneline | Measure-Object -Line

Write-Host "Your commits: $($yourCommits.Lines)"
Write-Host "Total commits: $($totalCommits.Lines)"
Write-Host ""
Write-Host "To push to remote (WARNING: This will overwrite remote history):"
Write-Host "  git push --force --all origin"
Write-Host ""
Write-Host "To restore from backup if needed:"
Write-Host "  git reset --hard backup-before-filter"
