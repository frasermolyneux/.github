<#
.SYNOPSIS
    Cleans up local Git branches across all repositories in the workspace.

.DESCRIPTION
    This script prunes local Git branches that have been merged or no longer exist remotely.
    It processes all Git repositories found in the workspace directory.

.PARAMETER WorkspacePath
    The root path containing all repositories. Defaults to C:\Git\gh-frasermolyneux

.PARAMETER DryRun
    If specified, shows what would be deleted without actually deleting branches.

.PARAMETER VerboseOutput
    If specified, shows detailed output for each operation.

.PARAMETER SkipMergedBranches
    If specified, only removes branches that don't exist remotely (skips merged branch cleanup).

.EXAMPLE
    .\clean-local-branches.ps1
    Cleans all repositories with default settings.

.EXAMPLE
    .\clean-local-branches.ps1 -DryRun -VerboseOutput
    Shows what would be cleaned without making changes.

.EXAMPLE
    .\clean-local-branches.ps1 -SkipMergedBranches
    Only removes branches that no longer exist remotely.
#>

param(
    [string]$WorkspacePath = "C:\Git\gh-frasermolyneux",
    [switch]$DryRun,
    [switch]$VerboseOutput,
    [switch]$SkipMergedBranches
)

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Get-GitRepositories {
    param([string]$RootPath)
    
    if (-not (Test-Path $RootPath)) {
        Write-ColorOutput "Workspace path not found: $RootPath" "Red"
        return @()
    }

    $repos = Get-ChildItem -Path $RootPath -Directory | Where-Object {
        Test-Path (Join-Path $_.FullName ".git")
    }

    return $repos
}

function Get-CurrentBranch {
    param([string]$RepoPath)
    
    Push-Location $RepoPath
    try {
        $branch = git rev-parse --abbrev-ref HEAD 2>$null
        return $branch
    }
    finally {
        Pop-Location
    }
}

function Get-DefaultBranch {
    param([string]$RepoPath)
    
    Push-Location $RepoPath
    try {
        # Try to get the default branch from origin
        $defaultBranch = git symbolic-ref refs/remotes/origin/HEAD 2>$null
        if ($defaultBranch) {
            return ($defaultBranch -replace 'refs/remotes/origin/', '')
        }
        
        # Fallback to common defaults
        $branches = git branch -r 2>$null
        if ($branches -match "origin/main") {
            return "main"
        }
        elseif ($branches -match "origin/master") {
            return "master"
        }
        
        return "main"
    }
    finally {
        Pop-Location
    }
}

function Clean-Repository {
    param(
        [string]$RepoPath,
        [string]$RepoName
    )
    
    Write-ColorOutput "`n========================================" "Cyan"
    Write-ColorOutput "Processing: $RepoName" "Cyan"
    Write-ColorOutput "========================================" "Cyan"
    
    Push-Location $RepoPath
    try {
        # Get current branch
        $currentBranch = Get-CurrentBranch -RepoPath $RepoPath
        if ($VerboseOutput) {
            Write-ColorOutput "Current branch: $currentBranch" "Gray"
        }

        # Fetch and prune to update remote tracking branches
        Write-ColorOutput "Fetching and pruning remote references..." "Yellow"
        $fetchOutput = git fetch --prune 2>&1
        if ($VerboseOutput) {
            $fetchOutput | ForEach-Object { Write-ColorOutput "  $_" "Gray" }
        }

        # Get all local branches except current
        $localBranches = git branch --format='%(refname:short)' | Where-Object { 
            $_ -ne $currentBranch -and $_ -ne "main" -and $_ -ne "master" 
        }

        if ($localBranches.Count -eq 0) {
            Write-ColorOutput "No branches to clean up." "Green"
            return
        }

        $deletedCount = 0
        $skippedCount = 0

        foreach ($branch in $localBranches) {
            $branch = $branch.Trim()
            if ([string]::IsNullOrWhiteSpace($branch)) { continue }

            # Check if remote tracking branch exists
            $remoteBranch = git rev-parse --verify "origin/$branch" 2>$null
            $hasRemote = $LASTEXITCODE -eq 0

            if (-not $hasRemote) {
                # Branch doesn't exist remotely
                Write-ColorOutput "  Branch '$branch' no longer exists on remote" "Yellow"
                
                if ($DryRun) {
                    Write-ColorOutput "    [DRY RUN] Would delete local branch" "Magenta"
                    $deletedCount++
                }
                else {
                    $deleteOutput = git branch -D $branch 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        Write-ColorOutput "    Deleted local branch" "Green"
                        $deletedCount++
                    }
                    else {
                        Write-ColorOutput "    Failed to delete: $deleteOutput" "Red"
                    }
                }
            }
            elseif (-not $SkipMergedBranches) {
                # Check if branch has been merged into default branch
                $defaultBranch = Get-DefaultBranch -RepoPath $RepoPath
                $mergedBranches = git branch --merged $defaultBranch --format='%(refname:short)' 2>$null
                
                if ($mergedBranches -contains $branch) {
                    Write-ColorOutput "  Branch '$branch' has been merged into $defaultBranch" "Yellow"
                    
                    if ($DryRun) {
                        Write-ColorOutput "    [DRY RUN] Would delete merged branch" "Magenta"
                        $deletedCount++
                    }
                    else {
                        $deleteOutput = git branch -d $branch 2>&1
                        if ($LASTEXITCODE -eq 0) {
                            Write-ColorOutput "    Deleted merged branch" "Green"
                            $deletedCount++
                        }
                        else {
                            Write-ColorOutput "    Failed to delete: $deleteOutput" "Red"
                        }
                    }
                }
                else {
                    if ($VerboseOutput) {
                        Write-ColorOutput "  Branch '$branch' - keeping (not merged, remote exists)" "Gray"
                    }
                    $skippedCount++
                }
            }
            else {
                if ($VerboseOutput) {
                    Write-ColorOutput "  Branch '$branch' - keeping (remote exists)" "Gray"
                }
                $skippedCount++
            }
        }

        # Summary for this repository
        if ($deletedCount -gt 0 -or $skippedCount -gt 0) {
            Write-ColorOutput "`nSummary for $RepoName" "Cyan"
            if ($DryRun) {
                Write-ColorOutput "  Would delete: $deletedCount branch(es)" "Magenta"
            }
            else {
                Write-ColorOutput "  Deleted: $deletedCount branch(es)" "Green"
            }
            if ($VerboseOutput) {
                Write-ColorOutput "  Kept: $skippedCount branch(es)" "Gray"
            }
        }
    }
    catch {
        Write-ColorOutput "Error processing repository: $_" "Red"
    }
    finally {
        Pop-Location
    }
}

# Main script execution
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "Git Branch Cleanup Script" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "Workspace: $WorkspacePath" "White"
if ($DryRun) {
    Write-ColorOutput "Mode: DRY RUN (no changes will be made)" "Magenta"
}
if ($SkipMergedBranches) {
    Write-ColorOutput "Mode: Only removing branches without remote tracking" "Yellow"
}

# Get all repositories
$repositories = Get-GitRepositories -RootPath $WorkspacePath

if ($repositories.Count -eq 0) {
    Write-ColorOutput "No Git repositories found in $WorkspacePath" "Red"
    exit 1
}

Write-ColorOutput "Found $($repositories.Count) Git repositories" "Green"

# Process each repository
$totalDeleted = 0
foreach ($repo in $repositories) {
    Clean-Repository -RepoPath $repo.FullName -RepoName $repo.Name
}

# Final summary
Write-ColorOutput "`n========================================" "Cyan"
Write-ColorOutput "Cleanup Complete!" "Cyan"
Write-ColorOutput "========================================" "Cyan"
if ($DryRun) {
    Write-ColorOutput "This was a dry run. Re-run without -DryRun to apply changes." "Magenta"
}
