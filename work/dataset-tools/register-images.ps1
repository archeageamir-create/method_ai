param(
    [Parameter(Mandatory = $true)]
    [string]$InputDirectory,

    [Parameter(Mandatory = $true)]
    [string]$OutputCsv,

    [Parameter(Mandatory = $true)]
    [ValidateSet("real", "ai_generated")]
    [string]$GroundTruth,

    [ValidateSet("development", "internal_holdout", "external_holdout")]
    [string]$Split = "development",

    [ValidateSet("controlled_capture", "controlled_generation", "trusted_dataset", "provided_with_provenance")]
    [string]$TruthBasis,

    [Parameter(Mandatory = $true)]
    [string]$SourceType,

    [Parameter(Mandatory = $true)]
    [string]$SourceName,

    [string]$SourceVersion = "",
    [string]$AcquiredBy = "Смагулов Амирхан Каиржанович",
    [string]$LicenseOrPermission = "project_research_use"
)

$ErrorActionPreference = "Stop"
$allowedExtensions = @(".jpg", ".jpeg", ".png")
$inputPath = (Resolve-Path -LiteralPath $InputDirectory).Path
$outputPath = [System.IO.Path]::GetFullPath($OutputCsv)
$outputParent = Split-Path -Parent $outputPath

if (-not (Get-Command magick -ErrorAction SilentlyContinue)) {
    throw "ImageMagick (magick.exe) не найден в PATH."
}

New-Item -ItemType Directory -Force $outputParent | Out-Null

$existingRows = @()
if (Test-Path -LiteralPath $outputPath) {
    $existingRows = @(Import-Csv -LiteralPath $outputPath)
}

$knownHashes = @{}
$maxId = 0
foreach ($row in $existingRows) {
    if ($row.sha256) {
        $knownHashes[$row.sha256.ToUpperInvariant()] = $row.sample_id
    }
    if ($row.sample_id -match '^IMG-(\d+)$') {
        $maxId = [Math]::Max($maxId, [int]$Matches[1])
    }
}

$files = Get-ChildItem -LiteralPath $inputPath -File -Recurse |
    Where-Object { $allowedExtensions -contains $_.Extension.ToLowerInvariant() } |
    Sort-Object FullName

if ($files.Count -eq 0) {
    throw "В папке нет JPEG или PNG изображений: $inputPath"
}

$newRows = @()
foreach ($file in $files) {
    $sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($knownHashes.ContainsKey($sha256)) {
        Write-Warning "Пропущен дубликат $($file.Name); уже зарегистрирован как $($knownHashes[$sha256])."
        continue
    }

    $identity = (& magick identify -format "%w,%h,%m" $file.FullName).Trim()
    if ($LASTEXITCODE -ne 0 -or $identity -notmatch '^(\d+),(\d+),(.+)$') {
        throw "Не удалось прочитать изображение: $($file.FullName)"
    }

    $maxId += 1
    $sampleId = "IMG-{0:D6}" -f $maxId
    $relativeName = [System.IO.Path]::GetRelativePath($inputPath, $file.FullName).Replace('\', '/')

    $row = [PSCustomObject][ordered]@{
        sample_id             = $sampleId
        family_id             = $sampleId
        parent_sample_id      = ""
        split                 = $Split
        ground_truth          = $GroundTruth
        truth_basis           = $TruthBasis
        source_type           = $SourceType
        source_name           = $SourceName
        source_version        = $SourceVersion
        original_filename     = $file.Name
        stored_filename       = $relativeName
        file_format           = $Matches[3].ToUpperInvariant()
        width                 = [int]$Matches[1]
        height                = [int]$Matches[2]
        sha256                = $sha256
        acquired_at           = (Get-Date).ToString("yyyy-MM-dd")
        acquired_by           = $AcquiredBy
        license_or_permission = $LicenseOrPermission
        transformation        = "none"
        transformation_params = ""
        notes                 = ""
    }

    $newRows += $row
    $knownHashes[$sha256] = $sampleId
}

if ($newRows.Count -eq 0) {
    Write-Host "Новых файлов нет. Реестр не изменён."
    exit 0
}

if (Test-Path -LiteralPath $outputPath) {
    $newRows | Export-Csv -LiteralPath $outputPath -NoTypeInformation -Encoding utf8 -Append
}
else {
    $newRows | Export-Csv -LiteralPath $outputPath -NoTypeInformation -Encoding utf8
}

Write-Host "Добавлено файлов: $($newRows.Count)"
Write-Host "Реестр: $outputPath"

