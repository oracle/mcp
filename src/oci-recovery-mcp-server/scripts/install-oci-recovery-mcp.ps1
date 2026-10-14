param(
    [string]$ParentDirectory
)

$ErrorActionPreference = "Stop"
$installerScript = Join-Path $PSScriptRoot "install_oci_recovery_mcp.py"
if (-not (Test-Path -LiteralPath $installerScript -PathType Leaf)) {
    throw "The Python installer must be beside this launcher: $installerScript"
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is required. Install Git for Windows, then run this installer again."
}

$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCommand) {
    $uvPath = $uvCommand.Source
} else {
    Write-Host "uv was not found; installing uv for your user account."
    Invoke-Expression (Invoke-RestMethod -Uri "https://astral.sh/uv/install.ps1")
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvCommand) {
        $uvPath = $uvCommand.Source
    } else {
        $uvCandidates = @(
            (Join-Path $HOME ".local\bin\uv.exe"),
            (Join-Path $HOME ".cargo\bin\uv.exe")
        )
        $uvPath = $uvCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    }
}

if (-not $uvPath) {
    throw "uv installation finished, but uv.exe was not found. Open a new PowerShell window and rerun this script."
}

$env:OCI_RECOVERY_UV = $uvPath
$uvArguments = @("run", "--python", "3.13", "--no-project", "--no-sync", $installerScript)
if ($ParentDirectory) { $uvArguments += @("--parent-dir", $ParentDirectory) }
& $uvPath @uvArguments
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
