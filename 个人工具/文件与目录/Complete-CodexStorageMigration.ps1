$ErrorActionPreference = 'Stop'
$taskRoot = 'E:\Documents\ChatGPT\电脑调试'
$taskStatus = Join-Path $taskRoot '迁移状态.json'
$taskLog = Join-Path $taskRoot '迁移收尾.log'

function Set-MigrationStatus([string]$phase, [string]$message) {
    [ordered]@{ phase=$phase; message=$message; updatedAt=[DateTimeOffset]::Now.ToString('o') } |
        ConvertTo-Json | Set-Content -LiteralPath $taskStatus -Encoding utf8
    Add-Content -LiteralPath $taskLog -Value ([DateTimeOffset]::Now.ToString('o')+' '+$message) -Encoding utf8
}

function Get-MigrationSHA([string]$path) {
    $stream = [IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
    try { [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream)) }
    finally { $stream.Dispose() }
}

function Assert-RegularTree([string]$path) {
    if ((Get-Item -LiteralPath $path).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Unexpected link: $path" }
    if (@(Get-ChildItem -LiteralPath $path -Recurse -Force -Attributes ReparsePoint).Count) { throw "Nested link found: $path" }
}

function Sync-AndVerify([string]$source, [string]$destination) {
    Assert-RegularTree $source
    & robocopy $source $destination /E /COPY:DAT /DCOPY:DAT /XJ /R:0 /W:0 /NP /NFL /NDL /NJH /NJS "/LOG+:$taskLog" | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "Copy failed ($LASTEXITCODE): $source" }
    foreach ($file in Get-ChildItem -LiteralPath $source -File -Recurse -Force) {
        $relative = $file.FullName.Substring($source.Length+1)
        if ((Get-MigrationSHA $file.FullName) -ne (Get-MigrationSHA (Join-Path $destination $relative))) { throw "Hash mismatch: $relative" }
    }
}

function Assert-Junction([string]$source, [string]$destination) {
    $item = Get-Item -LiteralPath $source
    if ($item.LinkType -ne 'Junction' -or [string]$item.Target -ine $destination) { throw "Incorrect junction: $source" }
}

$taskPairs = @(
    @{ Source='C:\Users\Lenovo\Documents\Codex'; Destination='E:\Documents\ChatGPT\Codex'; Backup='C:\Users\Lenovo\Documents\Codex.final-backup-20261010' },
    @{ Source='C:\Users\Lenovo\.codex\visualizations'; Destination='E:\Documents\ChatGPT\可视化'; Backup='C:\Users\Lenovo\.codex\visualizations.final-backup-20261010' }
)
$taskOldBackup = 'C:\Users\Lenovo\Documents\Codex.migration-backup-20261010'

try {
    Set-MigrationStatus 'waiting_for_app_exit' '已校验 E 盘副本，等待完全退出 ChatGPT/Codex 应用后安全切换旧目录。'
    $deadline = [DateTimeOffset]::Now.AddHours(2)
    while ($true) {
        $running = @(Get-Process -Name ChatGPT,codex -ErrorAction SilentlyContinue | Where-Object {
            try { $_.Path -match '\\OpenAI\.Codex_[^\\]+\\app\\ChatGPT\.exe$|\\AppData\\Local\\OpenAI\\Codex\\bin\\[^\\]+\\codex\.exe$' }
            catch { $true }
        })
        if (!$running.Count) { break }
        if ([DateTimeOffset]::Now -gt $deadline) { throw '等待应用退出超过两小时。原文件和 E 盘副本均保留；可在退出应用后重新运行此脚本。' }
        Start-Sleep -Seconds 3
    }

    Set-MigrationStatus 'migrating' '应用已退出，正在同步并校验最终文件。'
    if (Test-Path -LiteralPath $taskOldBackup) { Sync-AndVerify $taskOldBackup 'E:\Documents\ChatGPT\Codex' }

    foreach ($pair in $taskPairs) {
        $source = [IO.Path]::GetFullPath($pair.Source)
        $destination = [IO.Path]::GetFullPath($pair.Destination)
        $backup = [IO.Path]::GetFullPath($pair.Backup)
        if ($source -cne $pair.Source -or $destination -cne $pair.Destination -or $backup -cne $pair.Backup) { throw 'Absolute path check failed.' }
        if (!(Test-Path -LiteralPath $destination)) { New-Item -ItemType Directory -Path $destination | Out-Null }
        if (Test-Path -LiteralPath $source) {
            if ((Get-Item -LiteralPath $source).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                Assert-Junction $source $destination
            } else {
                if (Test-Path -LiteralPath $backup) { throw "Backup already exists: $backup" }
                Sync-AndVerify $source $destination
                [IO.Directory]::Move($source,$backup)
                try { New-Item -ItemType Junction -Path $source -Target $destination | Out-Null }
                catch {
                    if (!(Test-Path -LiteralPath $source)) { [IO.Directory]::Move($backup,$source) }
                    throw
                }
                Assert-Junction $source $destination
            }
        } else {
            if (Test-Path -LiteralPath $backup) { Sync-AndVerify $backup $destination }
            New-Item -ItemType Junction -Path $source -Target $destination | Out-Null
            Assert-Junction $source $destination
        }
        Set-MigrationStatus 'verifying' ("已建立旧路径到 E 盘的链接："+$source)
    }

    # Both links must be correct before deleting any original backup.
    foreach ($pair in $taskPairs) { Assert-Junction $pair.Source $pair.Destination }
    $cleanupPairs = @(
        @{ Backup='C:\Users\Lenovo\Documents\Codex.migration-backup-20261010'; Destination='E:\Documents\ChatGPT\Codex' },
        @{ Backup='C:\Users\Lenovo\Documents\Codex.final-backup-20261010'; Destination='E:\Documents\ChatGPT\Codex' },
        @{ Backup='C:\Users\Lenovo\.codex\visualizations.final-backup-20261010'; Destination='E:\Documents\ChatGPT\可视化' }
    )
    $allowlist = @('C:\Users\Lenovo\Documents\Codex.migration-backup-20261010','C:\Users\Lenovo\Documents\Codex.final-backup-20261010','C:\Users\Lenovo\.codex\visualizations.final-backup-20261010')
    foreach ($pair in $cleanupPairs) {
        if (!(Test-Path -LiteralPath $pair.Backup)) { continue }
        $resolved = (Get-Item -LiteralPath $pair.Backup).FullName
        if ($allowlist -cnotcontains $resolved) { throw 'Deletion path is outside the exact backup allowlist.' }
        Assert-RegularTree $resolved
        foreach ($file in Get-ChildItem -LiteralPath $resolved -File -Recurse -Force) {
            $relative = $file.FullName.Substring($resolved.Length+1)
            if ((Get-MigrationSHA $file.FullName) -ne (Get-MigrationSHA (Join-Path $pair.Destination $relative))) { throw "Backup changed; preserved: $relative" }
        }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
    foreach ($path in $allowlist) { if (Test-Path -LiteralPath $path) { throw "Backup cleanup incomplete: $path" } }

    $taskReadme = @'
# ChatGPT 与 Codex 文件存放

统一作品目录：E:\Documents\ChatGPT

迁移已完成：Codex 独立聊天的历史文件位于 E:\Documents\ChatGPT\Codex，可视化文件位于 E:\Documents\ChatGPT\可视化。C 盘原文件及本次迁移备份已删除。两个旧目录仅保留指向 E 盘的 Windows 目录链接，旧聊天链接继续可用，旧路径的新写入也实际存储在 E 盘。

现有论文、PPT、文献阅读等项目继续使用此总目录下的项目文件夹。本机 AGENTS.md 已保存 E 盘输出偏好。

程序本身的配置、认证、聊天数据库、插件和内部缓存仍在原位置。本次没有迁移应用安装目录或这些程序数据。

ChatGPT 网页版下载仍由浏览器下载设置决定，本地 AGENTS.md 不会改变网页或浏览器设置。

迁移状态和日志位于 电脑调试\迁移状态.json 与 电脑调试\迁移收尾.log。
'@
    Set-Content -LiteralPath 'E:\Documents\ChatGPT\文件存放说明.md' -Value $taskReadme -Encoding utf8
    Set-MigrationStatus 'complete' '迁移完成。旧目录均已链接到 E 盘，逐文件校验通过，C 盘原文件及迁移备份已删除。'
} catch {
    Set-MigrationStatus 'needs_attention' $_.Exception.Message
    exit 1
}
