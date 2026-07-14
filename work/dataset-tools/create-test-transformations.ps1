param(
    [Parameter(Mandatory = $true)]
    [string]$InputDirectory,

    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory
)

$ErrorActionPreference = "Stop"
$allowedExtensions = @(".jpg", ".jpeg", ".png")
$inputPath = (Resolve-Path -LiteralPath $InputDirectory).Path
$outputPath = [System.IO.Path]::GetFullPath($OutputDirectory)
$manifestPath = Join-Path $outputPath "TRANSFORM_MANIFEST.csv"

if (-not (Get-Command magick -ErrorAction SilentlyContinue)) {
    throw "ImageMagick (magick.exe) не найден в PATH."
}

New-Item -ItemType Directory -Force $outputPath | Out-Null

$existingHashes = @{}
if (Test-Path -LiteralPath $manifestPath) {
    foreach ($row in @(Import-Csv -LiteralPath $manifestPath)) {
        if ($row.sha256) { $existingHashes[$row.sha256.ToUpperInvariant()] = $true }
    }
}

function Add-ManifestRow {
    param(
        [System.IO.FileInfo]$Parent,
        [string]$DerivedPath,
        [string]$Transformation,
        [string]$Parameters
    )

    $identity = (& magick identify -format "%w,%h,%m" $DerivedPath).Trim()
    if ($LASTEXITCODE -ne 0 -or $identity -notmatch '^(\d+),(\d+),(.+)$') {
        throw "Не удалось проверить производный файл: $DerivedPath"
    }

    $sha = (Get-FileHash -LiteralPath $DerivedPath -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($existingHashes.ContainsKey($sha)) { return $null }
    $existingHashes[$sha] = $true

    return [PSCustomObject][ordered]@{
        parent_filename       = $Parent.Name
        derived_filename      = [System.IO.Path]::GetRelativePath($outputPath, $DerivedPath).Replace('\', '/')
        transformation        = $Transformation
        transformation_params = $Parameters
        file_format           = $Matches[3].ToUpperInvariant()
        width                 = [int]$Matches[1]
        height                = [int]$Matches[2]
        sha256                = $sha
        created_at            = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
        tool                  = "ImageMagick 7"
    }
}

$rows = @()
$files = Get-ChildItem -LiteralPath $inputPath -File -Recurse |
    Where-Object { $allowedExtensions -contains $_.Extension.ToLowerInvariant() } |
    Sort-Object FullName

foreach ($file in $files) {
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    $identity = (& magick identify -format "%w,%h" $file.FullName).Trim()
    if ($identity -notmatch '^(\d+),(\d+)$') { throw "Не удалось прочитать $($file.FullName)" }
    $width = [int]$Matches[1]
    $height = [int]$Matches[2]
    $cropWidth = [Math]::Max(1, [Math]::Floor($width * 0.9))
    $cropHeight = [Math]::Max(1, [Math]::Floor($height * 0.9))

    $jpegPath = Join-Path $outputPath "${stem}__jpeg_q75.jpg"
    & magick $file.FullName -quality 75 $jpegPath
    $row = Add-ManifestRow $file $jpegPath "jpeg_reencode" "quality=75"
    if ($row) { $rows += $row }

    $resizePath = Join-Path $outputPath "${stem}__resize_50.png"
    & magick $file.FullName -resize "50%" $resizePath
    $row = Add-ManifestRow $file $resizePath "resize" "scale=0.5"
    if ($row) { $rows += $row }

    $cropPath = Join-Path $outputPath "${stem}__crop_10.png"
    & magick $file.FullName -gravity center -crop "${cropWidth}x${cropHeight}+0+0" +repage $cropPath
    $row = Add-ManifestRow $file $cropPath "crop" "center_crop=10_percent"
    if ($row) { $rows += $row }

    $combinedPath = Join-Path $outputPath "${stem}__resize_50_jpeg_q75.jpg"
    & magick $file.FullName -resize "50%" -quality 75 $combinedPath
    $row = Add-ManifestRow $file $combinedPath "combined" "resize=0.5;jpeg_quality=75"
    if ($row) { $rows += $row }
}

if ($rows.Count -gt 0) {
    if (Test-Path -LiteralPath $manifestPath) {
        $rows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8 -Append
    }
    else {
        $rows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8
    }
}

Write-Host "Создано новых производных файлов: $($rows.Count)"
Write-Host "Манифест: $manifestPath"

