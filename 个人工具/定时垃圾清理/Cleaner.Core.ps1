Set-StrictMode -Version 2.0

function Format-Bytes([long]$Bytes) {
    if ($Bytes -ge 1GB) { return ('{0:N2} GB' -f ($Bytes / 1GB)) }
    if ($Bytes -ge 1MB) { return ('{0:N2} MB' -f ($Bytes / 1MB)) }
    return ('{0:N1} KB' -f ($Bytes / 1KB))
}

function Get-FullPath([string]$Path) {
    return [IO.Path]::GetFullPath($Path).TrimEnd('\')
}

function Test-PathWithin([string]$Path, [string]$Root) {
    $p = Get-FullPath $Path
    $r = Get-FullPath $Root
    return $p.StartsWith($r + '\', [StringComparison]::OrdinalIgnoreCase)
}

function Test-NoReparseAncestors([string]$Path) {
    $p = Get-FullPath $Path
    while ($p) {
        try {
            $item = Get-Item -LiteralPath $p -Force -ErrorAction Stop
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { return $false }
        } catch { return $false }
        $p = [IO.Path]::GetDirectoryName($p)
    }
    return $true
}

function Test-TempCandidate($File, [string]$Root, [datetime]$Cutoff) {
    if (-not (Test-PathWithin $File.FullName $Root)) { return $false }
    if ($File.PSIsContainer -or (($File.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) { return $false }
    # Recent creation, writes or access all protect the file. Windows access timestamps may be delayed.
    if ($File.CreationTime -ge $Cutoff -or $File.LastWriteTime -ge $Cutoff -or $File.LastAccessTime -ge $Cutoff) { return $false }
    if ($File.Extension -match '^\.(exe|msi|msix|msixbundle|msp|cab|dll|sys|lnk)$') { return $false }
    $relative = $File.FullName.Substring((Get-FullPath $Root).Length + 1)
    # Preserve temporary working directories belonging to development tools and this assistant.
    if ($relative -match '(?i)(^|\\)[^\\]*(codex|chatgpt|openai|pip-|uv-|npm-|node-|msi|installer|setup)[^\\]*(\\|$)') { return $false }
    return $true
}

function Get-ScanTargets {
    $targets = New-Object 'System.Collections.Generic.List[object]'
    $seen = @{}
    function Add-Target([string]$Name, [string]$Path, [bool]$Cleanup) {
        if (-not $Path) { return }
        $full = Get-FullPath $Path
        if ($seen.ContainsKey($full)) { return }
        $seen[$full] = $true
        $targets.Add([pscustomobject]@{Name=$Name; Path=$full; Cleanup=$Cleanup})
    }
    Add-Target '用户临时文件' (Join-Path $env:LOCALAPPDATA 'Temp') $true
    Add-Target 'Windows 临时文件' (Join-Path $env:windir 'Temp') $true
    Add-Target 'DirectX 着色器缓存（仅统计）' (Join-Path $env:LOCALAPPDATA 'D3DSCache') $false
    Add-Target '应用崩溃转储（仅统计）' (Join-Path $env:LOCALAPPDATA 'CrashDumps') $false
    Add-Target 'Windows 错误报告（仅统计）' (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\WER') $false
    Add-Target '系统错误报告（仅统计）' (Join-Path $env:ProgramData 'Microsoft\Windows\WER') $false
    Add-Target 'Windows 更新下载缓存（仅统计）' (Join-Path $env:windir 'SoftwareDistribution\Download') $false
    Add-Target 'NVIDIA DX 缓存（仅统计）' (Join-Path $env:LOCALAPPDATA 'NVIDIA\DXCache') $false
    Add-Target 'NVIDIA GL 缓存（仅统计）' (Join-Path $env:LOCALAPPDATA 'NVIDIA\GLCache') $false
    Add-Target 'pip 下载缓存（仅统计）' (Join-Path $env:LOCALAPPDATA 'pip\Cache') $false
    Add-Target 'npm 缓存（仅统计）' (Join-Path $env:LOCALAPPDATA 'npm-cache') $false
    Add-Target 'uv 缓存（仅统计）' (Join-Path $env:LOCALAPPDATA 'uv\cache') $false
    Add-Target '旧 Internet 临时缓存（仅统计）' (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\INetCache') $false
    foreach ($browser in @(@{Name='Chrome'; Path='Google\Chrome\User Data'}, @{Name='Edge'; Path='Microsoft\Edge\User Data'})) {
        $base = Join-Path $env:LOCALAPPDATA $browser.Path
        if (Test-Path -LiteralPath $base) {
            foreach ($profile in @(Get-ChildItem -LiteralPath $base -Directory -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^(Default|Profile \d+)$' })) {
                foreach ($cache in @('Cache', 'Code Cache', 'GPUCache', 'Service Worker\CacheStorage')) {
                    Add-Target ($browser.Name + ' ' + $profile.Name + ' ' + $cache + '（仅统计）') (Join-Path $profile.FullName $cache) $false
                }
            }
        }
    }
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    foreach ($drive in @(Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Name -match '^[A-Z]$' })) {
        Add-Target ($drive.Name + ' 盘回收站（仅统计）') (Join-Path $drive.Root ('$Recycle.Bin\' + $sid)) $false
    }
    return $targets.ToArray()
}

function Get-CleanerScan {
    param([object[]]$Targets = (Get-ScanTargets), [int]$MinAgeDays = 14)
    if ($MinAgeDays -lt 14) { throw '保留天数不能少于 14 天。' }
    $cutoff = (Get-Date).AddDays(-$MinAgeDays)
    $files = New-Object 'System.Collections.Generic.List[object]'
    $summary = New-Object 'System.Collections.Generic.List[object]'
    foreach ($target in $Targets) {
        $count = 0; [long]$bytes = 0; $candidates = 0; [long]$candidateBytes = 0; $errors = 0; $links = 0
        $status = '已扫描'
        if (-not (Test-Path -LiteralPath $target.Path -PathType Container)) {
            $status = '不存在或无权限'
        } elseif (-not (Test-NoReparseAncestors $target.Path)) {
            $status = '路径含链接，已跳过'
        } else {
            $pending = New-Object 'System.Collections.Generic.Stack[string]'
            $pending.Push($target.Path)
            while ($pending.Count -gt 0) {
                $dir = $pending.Pop()
                try { $children = @(Get-ChildItem -LiteralPath $dir -Force -ErrorAction Stop) }
                catch { $errors++; continue }
                foreach ($file in $children) {
                    if (($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { $links++; continue }
                    if ($file.PSIsContainer) { $pending.Push($file.FullName); continue }
                    $count++; $bytes += $file.Length
                    $eligible = $target.Cleanup -and (Test-TempCandidate $file $target.Path $cutoff)
                    if ($eligible) { $candidates++; $candidateBytes += $file.Length }
                    $files.Add([pscustomobject]@{
                        Category=$target.Name; Root=$target.Path; Path=$file.FullName; Bytes=[long]$file.Length
                        LastWriteTime=$file.LastWriteTime.ToString('s'); Eligible=[bool]$eligible
                    })
                }
            }
            if ($errors -gt 0) { $status = '部分文件夹无法读取' }
        }
        $summary.Add([pscustomobject]@{
            Category=$target.Name; Root=$target.Path; Files=$count; Bytes=$bytes; Size=(Format-Bytes $bytes)
            EligibleFiles=$candidates; EligibleBytes=$candidateBytes; EligibleSize=(Format-Bytes $candidateBytes)
            Errors=$errors; SkippedLinks=$links; Status=$status; AutoCleanup=[bool]$target.Cleanup
        })
    }
    return [pscustomobject]@{ScannedAt=(Get-Date).ToString('s'); MinAgeDays=$MinAgeDays; Summary=$summary.ToArray(); Files=$files.ToArray()}
}

function Save-CleanerReport($Scan, [string]$Directory) {
    New-Item -ItemType Directory -Path $Directory -Force -ErrorAction Stop | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    $prefix = Join-Path $Directory ('检查-' + $stamp)
    $Scan.Summary | Export-Csv -LiteralPath ($prefix + '-汇总.csv') -NoTypeInformation -Encoding UTF8
    $Scan.Files | Export-Csv -LiteralPath ($prefix + '-文件.csv') -NoTypeInformation -Encoding UTF8
    [pscustomobject]@{ScannedAt=$Scan.ScannedAt; MinAgeDays=$Scan.MinAgeDays; Summary=$Scan.Summary} |
        ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ($prefix + '.json') -Encoding UTF8
    $lines = New-Object 'System.Collections.Generic.List[string]'
    $lines.Add('# 电脑垃圾文件检查')
    $lines.Add('')
    $lines.Add('检查时间：' + $Scan.ScannedAt)
    $lines.Add('自动清理范围：用户及 Windows 临时目录；创建、修改、访问均超过 14 天；跳过链接、安装包和工具工作目录。')
    $lines.Add('统计的是文件逻辑大小；受权限、文件变动和磁盘压缩影响，实际释放空间可能不同。缓存占用不代表全部无用。')
    $lines.Add('')
    $lines.Add('| 类别 | 占用 | 可自动清理 | 文件数 | 状态 |')
    $lines.Add('|---|---:|---:|---:|---|')
    foreach ($row in $Scan.Summary) { $lines.Add('| ' + $row.Category + ' | ' + $row.Size + ' | ' + $row.EligibleSize + ' | ' + $row.Files + ' | ' + $row.Status + ' |') }
    $lines.Add('')
    $lines.Add('## 较大的临时文件清理候选项')
    foreach ($file in @($Scan.Files | Where-Object Eligible | Sort-Object Bytes -Descending | Select-Object -First 20)) {
        $lines.Add('- ' + (Format-Bytes $file.Bytes) + ' — `' + $file.Path + '`')
    }
    $lines.Add('')
    $lines.Add('桌面、文档、下载、聊天记录、浏览器登录数据和系统组件不属于自动清理范围。回收站也不会自动清空。')
    $lines | Set-Content -LiteralPath ($prefix + '.md') -Encoding UTF8
    Copy-Item -LiteralPath ($prefix + '.md') -Destination (Join-Path $Directory '最新检查报告.md') -Force -ErrorAction Stop
    return ($prefix + '.md')
}

function Invoke-TempCleanup {
    param($Scan, [object[]]$AllowedTargets, [string]$LogDirectory)
    # Never recursively delete directories. Re-check the trusted allowlist and current file metadata for every deletion.
    New-Item -ItemType Directory -Path $LogDirectory -Force -ErrorAction Stop | Out-Null
    $log = Join-Path $LogDirectory ('清理-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.jsonl')
    $cutoff = (Get-Date).AddDays(-14)
    [long]$deletedBytes = 0; $deleted = 0; $skipped = 0
    foreach ($row in @($Scan.Files | Where-Object Eligible)) {
        $result = 'Skipped'; $message = ''; [long]$length = 0
        try {
            $root = @($AllowedTargets | Where-Object { $_.Cleanup -and (Test-PathWithin $row.Path $_.Path) } | Select-Object -First 1)
            if ($root.Count -eq 0) { throw '不属于允许的临时目录' }
            if (-not (Test-NoReparseAncestors $row.Path)) { throw '路径包含链接或已经不存在' }
            $file = Get-Item -LiteralPath $row.Path -Force -ErrorAction Stop
            if (-not (Test-TempCandidate $file $root[0].Path $cutoff)) { throw '文件已更新或受到保护' }
            $length = $file.Length
            # An exclusive open rejects in-use files, including files that allow shared deletion.
            $handle = [IO.File]::Open($file.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::None)
            $handle.Dispose()
            if (-not (Test-NoReparseAncestors $row.Path)) { throw '删除前路径检查失败' }
            Remove-Item -LiteralPath $file.FullName -ErrorAction Stop
            $result = 'Deleted'; $deleted++; $deletedBytes += $length
        } catch { $skipped++; $message = $_.Exception.Message }
        [pscustomobject]@{At=(Get-Date).ToString('s'); Path=$row.Path; Bytes=$length; Result=$result; Message=$message} |
            ConvertTo-Json -Compress | Add-Content -LiteralPath $log -Encoding UTF8 -ErrorAction Stop
    }
    $resultSummary = [pscustomobject]@{At=(Get-Date).ToString('s'); DeletedFiles=$deleted; DeletedBytes=$deletedBytes; DeletedSize=(Format-Bytes $deletedBytes); SkippedFiles=$skipped; Log=$log}
    $resultSummary | ConvertTo-Json | Set-Content -LiteralPath ($log + '.summary.json') -Encoding UTF8
    return $resultSummary
}
