param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDirectory,

    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,

    [ValidateRange(1, 10000)]
    [int]$DevelopmentCount = 20,

    [string]$SourceName = "Apple iPhone 15",
    [string]$SourceVersion = "iOS 26.3.1",
    [string]$AcquiredBy = "Смагулов Амирхан Каиржанович"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command magick -ErrorAction SilentlyContinue)) {
    throw "ImageMagick (magick.exe) не найден в PATH."
}

$sourcePath = (Resolve-Path -LiteralPath $SourceDirectory).Path
$sourceFiles = @(Get-ChildItem -LiteralPath $sourcePath -File |
    Where-Object { $_.Extension.ToLowerInvariant() -in @(".heic", ".heif") } |
    Sort-Object Name)

if ($sourceFiles.Count -lt $DevelopmentCount) {
    throw "Найдено HEIC/HEIF: $($sourceFiles.Count); требуется минимум: $DevelopmentCount."
}

$root = [System.IO.Path]::GetFullPath($OutputRoot)
$allOriginals = Join-Path $root "00_source_original_heic"
$selectedOriginals = Join-Path $root "01_selected_original_heic"
$developmentJpeg = Join-Path $root "02_development_jpeg"
$manifests = Join-Path $root "manifests"

@($allOriginals, $selectedOriginals, $developmentJpeg, $manifests) |
    ForEach-Object { New-Item -ItemType Directory -Force -Path $_ | Out-Null }

function Copy-VerifiedOriginal {
    param(
        [Parameter(Mandatory = $true)][System.IO.FileInfo]$SourceFile,
        [Parameter(Mandatory = $true)][string]$DestinationDirectory
    )

    $destination = Join-Path $DestinationDirectory $SourceFile.Name
    $sourceHash = (Get-FileHash -LiteralPath $SourceFile.FullName -Algorithm SHA256).Hash.ToUpperInvariant()

    if (Test-Path -LiteralPath $destination) {
        $existingHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToUpperInvariant()
        if ($existingHash -ne $sourceHash) {
            throw "Отказ от перезаписи: существующий файл отличается от источника: $destination"
        }
    }
    else {
        Copy-Item -LiteralPath $SourceFile.FullName -Destination $destination
    }

    $copiedHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($copiedHash -ne $sourceHash) {
        throw "Ошибка проверки SHA-256 после копирования: $($SourceFile.Name)"
    }

    return [PSCustomObject]@{
        Destination = $destination
        Sha256 = $copiedHash
    }
}

$sourceManifestRows = @()
foreach ($sourceFile in $sourceFiles) {
    $copy = Copy-VerifiedOriginal -SourceFile $sourceFile -DestinationDirectory $allOriginals
    $sourceManifestRows += [PSCustomObject][ordered]@{
        original_filename = $sourceFile.Name
        stored_filename = "00_source_original_heic/$($sourceFile.Name)"
        sha256 = $copy.Sha256
        file_size_bytes = (Get-Item -LiteralPath $copy.Destination).Length
        copied_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
        verification = "source_and_copy_sha256_match"
        selected_for_development = $false
    }
}

$selected = @($sourceFiles | Select-Object -First $DevelopmentCount)
$registerRows = @()
$conversionRows = @()

for ($index = 0; $index -lt $selected.Count; $index++) {
    $sourceFile = $selected[$index]
    $originalCopy = Copy-VerifiedOriginal -SourceFile $sourceFile -DestinationDirectory $selectedOriginals
    $sourceRow = $sourceManifestRows | Where-Object { $_.original_filename -eq $sourceFile.Name }
    $sourceRow.selected_for_development = $true

    $originalIdentity = (& magick identify -ping -format "%w|%h|%m" ($originalCopy.Destination + "[0]")).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Не удалось прочитать HEIC: $($originalCopy.Destination)"
    }
    $originalParts = $originalIdentity -split "\|"

    $originalId = "IMG-{0:D6}" -f ($index + 1)
    $jpegId = "IMG-{0:D6}" -f ($DevelopmentCount + $index + 1)
    $jpegName = $sourceFile.BaseName + ".jpg"
    $jpegPath = Join-Path $developmentJpeg $jpegName
    $temporaryJpeg = $jpegPath + ".building.jpg"

    if (Test-Path -LiteralPath $temporaryJpeg) {
        Remove-Item -LiteralPath $temporaryJpeg -Force
    }

    & magick ($originalCopy.Destination + "[0]") -auto-orient -sampling-factor "4:4:4" -quality 95 $temporaryJpeg
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $temporaryJpeg)) {
        throw "Ошибка преобразования HEIC в JPEG: $($sourceFile.Name)"
    }
    Move-Item -LiteralPath $temporaryJpeg -Destination $jpegPath -Force

    $jpegIdentity = (& magick identify -ping -format "%w|%h|%m" $jpegPath).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Не удалось проверить JPEG: $jpegPath"
    }
    $jpegParts = $jpegIdentity -split "\|"
    $jpegHash = (Get-FileHash -LiteralPath $jpegPath -Algorithm SHA256).Hash.ToUpperInvariant()

    $common = [ordered]@{
        split = "development"
        ground_truth = "real"
        truth_basis = "controlled_capture"
        source_name = $SourceName
        source_version = $SourceVersion
        original_filename = $sourceFile.Name
        acquired_at = (Get-Date).ToString("yyyy-MM-dd")
        acquired_by = $AcquiredBy
        license_or_permission = "owner_provided_for_project_research"
    }

    $registerRows += [PSCustomObject][ordered]@{
        sample_id = $originalId
        family_id = $originalId
        parent_sample_id = ""
        split = $common.split
        ground_truth = $common.ground_truth
        truth_basis = $common.truth_basis
        source_type = "camera"
        source_name = $common.source_name
        source_version = $common.source_version
        original_filename = $common.original_filename
        stored_filename = "01_selected_original_heic/$($sourceFile.Name)"
        file_format = $originalParts[2].ToUpperInvariant()
        width = [int]$originalParts[0]
        height = [int]$originalParts[1]
        sha256 = $originalCopy.Sha256
        acquired_at = $common.acquired_at
        acquired_by = $common.acquired_by
        license_or_permission = $common.license_or_permission
        transformation = "none"
        transformation_params = ""
        notes = "Preserved camera original; not passed to JPEG/PNG-only detectors."
    }

    $transformParams = "ImageMagick 7.1.2-26; primary frame [0]; auto-orient; JPEG quality=95; sampling-factor=4:4:4"
    $registerRows += [PSCustomObject][ordered]@{
        sample_id = $jpegId
        family_id = $originalId
        parent_sample_id = $originalId
        split = $common.split
        ground_truth = $common.ground_truth
        truth_basis = $common.truth_basis
        source_type = "controlled_transformation"
        source_name = $common.source_name
        source_version = $common.source_version
        original_filename = $common.original_filename
        stored_filename = "02_development_jpeg/$jpegName"
        file_format = $jpegParts[2].ToUpperInvariant()
        width = [int]$jpegParts[0]
        height = [int]$jpegParts[1]
        sha256 = $jpegHash
        acquired_at = $common.acquired_at
        acquired_by = $common.acquired_by
        license_or_permission = $common.license_or_permission
        transformation = "HEIC_to_JPEG"
        transformation_params = $transformParams
        notes = "Controlled derivative used as detector input; ground truth inherited from documented camera original."
    }

    $conversionRows += [PSCustomObject][ordered]@{
        family_id = $originalId
        parent_sample_id = $originalId
        child_sample_id = $jpegId
        source_filename = $sourceFile.Name
        source_sha256 = $originalCopy.Sha256
        output_filename = $jpegName
        output_sha256 = $jpegHash
        transformation = "HEIC_to_JPEG"
        transformation_params = $transformParams
        created_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
    }
}

$sourceManifestRows | Export-Csv -LiteralPath (Join-Path $manifests "SOURCE_COPY_MANIFEST.csv") -NoTypeInformation -Encoding utf8
$conversionRows | Export-Csv -LiteralPath (Join-Path $manifests "CONVERSION_MANIFEST.csv") -NoTypeInformation -Encoding utf8
$registerRows | Export-Csv -LiteralPath (Join-Path $manifests "DATASET_REGISTER.csv") -NoTypeInformation -Encoding utf8

Write-Host "Исходников сохранено и проверено: $($sourceFiles.Count)"
Write-Host "Выбрано исходников для development: $($selected.Count)"
Write-Host "Контролируемых JPEG создано: $($conversionRows.Count)"
Write-Host "Папка набора: $root"
