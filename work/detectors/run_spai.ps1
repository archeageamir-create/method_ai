param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,
    [string]$OutputPath = "",
    [ValidateRange(256, 8192)]
    [int]$ResizeTo = 1024,
    [ValidateRange(0, 16)]
    [int]$DataWorkers = 2
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Join-Path $root "spai"
$python = Join-Path $root ".venv-spai\Scripts\python.exe"
$model = Join-Path $repo "weights\spai.pth"

if (-not $OutputPath) {
    $OutputPath = Join-Path $root "spai-output"
}

$resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
$resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
New-Item -ItemType Directory -Force $resolvedOutput | Out-Null

Push-Location $repo
try {
    & $python -m spai infer `
        --input $resolvedInput `
        --output $resolvedOutput `
        --model $model `
        --resize-to $ResizeTo `
        --opt DATA.NUM_WORKERS $DataWorkers
    if ($LASTEXITCODE -ne 0) {
        throw "SPAI завершился с кодом $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

Get-ChildItem -LiteralPath $resolvedOutput -Filter "*.csv"
