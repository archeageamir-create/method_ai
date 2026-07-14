param(
    [string]$CloudProjectRoot = "G:\Мой диск\ИИ методика",
    [string]$MirrorFolderName = "_LOCAL_REPO_MIRROR"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
Push-Location $repoRoot
try {
    if ((git rev-parse --is-inside-work-tree 2>$null) -ne "true") {
        throw "Текущая папка не является Git-репозиторием: $repoRoot"
    }

    $status = @(git status --porcelain)
    if ($LASTEXITCODE -ne 0) {
        throw "Не удалось проверить состояние Git."
    }
    if ($status.Count -gt 0) {
        throw "Синхронизация остановлена: сначала зафиксируйте изменения Git-коммитом."
    }

    $commit = (git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $commit) {
        throw "В репозитории нет доступного HEAD-коммита."
    }

    $cloudRoot = (Resolve-Path -LiteralPath $CloudProjectRoot).Path.TrimEnd('\')
    $mirrorCandidate = Join-Path $cloudRoot $MirrorFolderName
    New-Item -ItemType Directory -Force -Path $mirrorCandidate | Out-Null
    $mirror = (Resolve-Path -LiteralPath $mirrorCandidate).Path.TrimEnd('\')

    $expectedPrefix = $cloudRoot + '\'
    if (-not $mirror.StartsWith($expectedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Небезопасный путь зеркала: $mirror"
    }
    if ($mirror -eq $cloudRoot -or [string]::IsNullOrWhiteSpace($MirrorFolderName)) {
        throw "Путь зеркала не должен совпадать с корнем Google Drive."
    }

    $tempRoot = Join-Path $repoRoot "tmp\cloud-sync"
    $stage = Join-Path $tempRoot "stage"
    $archive = Join-Path $tempRoot "repo.zip"
    $bundle = Join-Path $tempRoot "PROJECT_HISTORY.bundle"

    if (Test-Path -LiteralPath $tempRoot) {
        $resolvedTemp = (Resolve-Path -LiteralPath $tempRoot).Path
        $safeTempPrefix = (Join-Path $repoRoot "tmp").TrimEnd('\') + '\'
        if (-not $resolvedTemp.StartsWith($safeTempPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Небезопасный временный путь: $resolvedTemp"
        }
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }

    New-Item -ItemType Directory -Force -Path $stage | Out-Null
    git archive --format=zip --output=$archive HEAD
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $archive)) {
        throw "Не удалось создать архив Git HEAD."
    }
    Expand-Archive -LiteralPath $archive -DestinationPath $stage -Force

    git bundle create $bundle --all
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $bundle)) {
        throw "Не удалось создать резервную копию Git-истории."
    }

    $expectedFiles = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $copiedCount = 0
    $unchangedCount = 0

    foreach ($stageFile in Get-ChildItem -LiteralPath $stage -Recurse -File) {
        $relativePath = [IO.Path]::GetRelativePath($stage, $stageFile.FullName)
        [void]$expectedFiles.Add($relativePath)
        $destination = Join-Path $mirror $relativePath
        $destinationParent = Split-Path -Parent $destination
        New-Item -ItemType Directory -Force -Path $destinationParent | Out-Null

        $needsCopy = $true
        if (Test-Path -LiteralPath $destination) {
            $destinationFile = Get-Item -LiteralPath $destination
            if ($destinationFile.Length -eq $stageFile.Length) {
                $sourceHash = (Get-FileHash -LiteralPath $stageFile.FullName -Algorithm SHA256).Hash
                $destinationHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
                $needsCopy = $sourceHash -ne $destinationHash
            }
        }

        if ($needsCopy) {
            Copy-Item -LiteralPath $stageFile.FullName -Destination $destination -Force
            $copiedCount += 1
        }
        else {
            $unchangedCount += 1
        }
    }

    $bundleDestination = Join-Path $mirror "PROJECT_HISTORY.bundle"
    $bundleNeedsCopy = $true
    if (Test-Path -LiteralPath $bundleDestination) {
        $existingBundle = Get-Item -LiteralPath $bundleDestination
        if ($existingBundle.Length -eq (Get-Item -LiteralPath $bundle).Length) {
            $bundleNeedsCopy =
                (Get-FileHash -LiteralPath $bundle -Algorithm SHA256).Hash -ne
                (Get-FileHash -LiteralPath $bundleDestination -Algorithm SHA256).Hash
        }
    }
    if ($bundleNeedsCopy) {
        Copy-Item -LiteralPath $bundle -Destination $bundleDestination -Force
        $copiedCount += 1
    }
    else {
        $unchangedCount += 1
    }

    $removedCount = 0
    foreach ($mirrorFile in Get-ChildItem -LiteralPath $mirror -Recurse -File) {
        if ($mirrorFile.Name -in @("SYNC_METADATA.json", "PROJECT_HISTORY.bundle")) {
            continue
        }
        $relativePath = [IO.Path]::GetRelativePath($mirror, $mirrorFile.FullName)
        if (-not $expectedFiles.Contains($relativePath)) {
            Remove-Item -LiteralPath $mirrorFile.FullName -Force
            $removedCount += 1
        }
    }

    Get-ChildItem -LiteralPath $mirror -Recurse -Directory |
        Sort-Object FullName -Descending |
        ForEach-Object {
            if (-not (Get-ChildItem -LiteralPath $_.FullName -Force | Select-Object -First 1)) {
                Remove-Item -LiteralPath $_.FullName -Force
            }
        }

    $metadata = [PSCustomObject][ordered]@{
        source = $repoRoot
        commit = $commit
        synced_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
        mirror = $mirror
        policy = "local_git_is_source_of_truth"
        history_bundle = "PROJECT_HISTORY.bundle"
        history_bundle_sha256 = (Get-FileHash -LiteralPath $bundleDestination -Algorithm SHA256).Hash
    }
    $metadata | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $mirror "SYNC_METADATA.json") -Encoding utf8

    Remove-Item -LiteralPath $tempRoot -Recurse -Force

    Write-Host "Синхронизация завершена."
    Write-Host "Commit: $commit"
    Write-Host "Зеркало: $mirror"
    Write-Host "Скопировано изменённых файлов: $copiedCount"
    Write-Host "Пропущено неизменённых файлов: $unchangedCount"
    Write-Host "Удалено устаревших файлов из зеркала: $removedCount"
}
finally {
    Pop-Location
}
