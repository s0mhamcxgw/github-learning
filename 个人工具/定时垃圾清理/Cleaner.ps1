[CmdletBinding()]
param(
    [ValidateSet('Gui', 'Scan', 'Clean', 'InstallSchedule', 'RemoveSchedule', 'Status')]
    [string]$Mode = 'Gui',
    [switch]$ConfirmClean
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Cleaner.Core.ps1')
$script:Reports = Join-Path $PSScriptRoot 'reports'
$script:Logs = Join-Path $PSScriptRoot 'logs'
$script:TaskName = 'ChatGPT-SafeTempCleaner-' + [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$script:EntryPath = Join-Path $PSScriptRoot 'Cleaner.ps1'

function Get-OwnedTask {
    $task = Get-ScheduledTask -TaskName $script:TaskName -TaskPath '\' -ErrorAction SilentlyContinue
    if ($null -ne $task) {
        $actions = @($task.Actions)
        if ($actions.Count -ne 1 -or -not $actions[0].Arguments.Contains('"' + $script:EntryPath + '"')) {
            throw '同名计划任务属于另一份程序，请先检查任务计划程序。'
        }
    }
    return $task
}

function Install-CleanerSchedule {
    if ((Get-TimeZone).Id -ne 'China Standard Time') { throw '当前系统时区不是北京时间，请在 Windows 设置中调整时区后再启用每周日 20:00。' }
    $existing = Get-OwnedTask
    if ($null -ne $existing) {
        Enable-ScheduledTask -TaskName $script:TaskName -TaskPath '\' | Out-Null
        return '已启用现有的每周清理任务。'
    }
    $powershell = Join-Path $env:windir 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $arguments = '-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $script:EntryPath + '" -Mode Clean -ConfirmClean'
    $action = New-ScheduledTaskAction -Execute $powershell -Argument $arguments -WorkingDirectory $PSScriptRoot
    $trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek Sunday -At '20:00'
    $principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
    Register-ScheduledTask -TaskName $script:TaskName -TaskPath '\' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description '每周日北京时间 20:00 清理超过14天的用户及Windows临时文件；跳过链接、安装包、工具目录和使用中的文件。日志保存在E盘。仅在此用户登录时运行，错过时间后补跑。' | Out-Null
    return '已启用：每周日 20:00（北京时间）。电脑开机且当前用户登录时运行，错过时间后补跑。'
}

function Remove-CleanerSchedule {
    $existing = Get-OwnedTask
    if ($null -ne $existing) { Unregister-ScheduledTask -TaskName $script:TaskName -TaskPath '\' -Confirm:$false }
    return '已关闭自动清理。'
}

function Get-CleanerScheduleStatus {
    $task = Get-OwnedTask
    if ($null -eq $task) { return '自动清理未启用。' }
    $info = Get-ScheduledTaskInfo -TaskName $script:TaskName -TaskPath '\'
    return ('自动清理：{0}；下次运行：{1:yyyy-MM-dd HH:mm}；最近结果：{2}' -f $task.State, $info.NextRunTime, $info.LastTaskResult)
}

function Invoke-CleanerOperation([bool]$Clean) {
    $mutex = New-Object Threading.Mutex($false, ('Local\' + $script:TaskName))
    $acquired = $false
    try {
        try { $acquired = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $acquired = $true }
        if (-not $acquired) { throw '已有检查或清理正在运行，请稍后再试。' }
        $targets = @(Get-ScanTargets)
        if ($Clean) { $targets = @($targets | Where-Object Cleanup) }
        $scan = Get-CleanerScan -Targets $targets
        $report = Save-CleanerReport $scan $script:Reports
        $cleanup = $null
        if ($Clean) { $cleanup = Invoke-TempCleanup -Scan $scan -AllowedTargets $targets -LogDirectory $script:Logs }
        return [pscustomobject]@{Scan=$scan; Report=$report; Cleanup=$cleanup}
    } finally {
        if ($acquired) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
}

function Show-CleanerWindow {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    [Windows.Forms.Application]::EnableVisualStyles()
    $form = New-Object Windows.Forms.Form
    $form.Text = '电脑垃圾检查与定时清理'
    $form.Size = New-Object Drawing.Size(980, 640)
    $form.MinimumSize = New-Object Drawing.Size(820, 550)
    $form.StartPosition = 'CenterScreen'
    $form.Font = New-Object Drawing.Font('Microsoft YaHei UI', 10)
    $intro = New-Object Windows.Forms.Label
    $intro.Text = '自动清理：超过 14 天未使用的临时文件。缓存和回收站只统计。'
    $intro.Location = New-Object Drawing.Point(18, 16)
    $intro.Size = New-Object Drawing.Size(910, 30)
    $intro.Anchor = 'Top,Left,Right'
    $form.Controls.Add($intro)
    $status = New-Object Windows.Forms.Label
    $status.Location = New-Object Drawing.Point(18, 48)
    $status.Size = New-Object Drawing.Size(910, 52)
    $status.Anchor = 'Top,Left,Right'
    try { $status.Text = Get-CleanerScheduleStatus } catch { $status.Text = $_.Exception.Message }
    $form.Controls.Add($status)
    $list = New-Object Windows.Forms.ListView
    $list.Location = New-Object Drawing.Point(18, 105)
    $list.Size = New-Object Drawing.Size(925, 342)
    $list.Anchor = 'Top,Bottom,Left,Right'
    $list.View = 'Details'; $list.FullRowSelect = $true; $list.GridLines = $true
    foreach ($col in @(@('检查项目',365),@('占用',105),@('可自动清理',115),@('文件数',80),@('检查状态',210))) { [void]$list.Columns.Add([string]$col[0], [int]$col[1]) }
    $form.Controls.Add($list)
    $info = New-Object Windows.Forms.TextBox
    $info.Multiline = $true; $info.ReadOnly = $true; $info.ScrollBars = 'Vertical'
    $info.Location = New-Object Drawing.Point(18, 459)
    $info.Size = New-Object Drawing.Size(925, 65)
    $info.Anchor = 'Bottom,Left,Right'
    $info.Text = '点“检查占用”生成报告。手动清理前会提示确认；清理文件不进入回收站。桌面、下载、聊天记录及浏览器登录信息不会被清理。'
    $form.Controls.Add($info)
    $buttons = New-Object 'System.Collections.Generic.List[object]'
    $labels = @('检查占用','清理临时文件','启用每周清理','关闭自动清理','打开报告目录')
    for ($i=0; $i -lt $labels.Count; $i++) {
        $button = New-Object Windows.Forms.Button
        $button.Text = $labels[$i]
        $button.Location = New-Object Drawing.Point((18 + $i * 184), 543)
        $button.Size = New-Object Drawing.Size(173, 38)
        $button.Anchor = 'Bottom,Left'
        $buttons.Add($button); $form.Controls.Add($button)
    }
    $buttons[0].Add_Click({
        foreach ($b in $buttons) { $b.Enabled = $false }; $form.UseWaitCursor = $true
        $info.Text = '正在检查，请稍候……'; $form.Refresh()
        try {
            $operation = Invoke-CleanerOperation $false
            $list.Items.Clear()
            [long]$eligible = 0
            foreach ($row in $operation.Scan.Summary) {
                $item = New-Object Windows.Forms.ListViewItem($row.Category)
                [void]$item.SubItems.Add($row.Size); [void]$item.SubItems.Add($row.EligibleSize)
                [void]$item.SubItems.Add([string]$row.Files); [void]$item.SubItems.Add($row.Status)
                [void]$list.Items.Add($item); $eligible += $row.EligibleBytes
            }
            $info.Text = '符合自动清理规则：' + (Format-Bytes $eligible) + "`r`n报告：" + $operation.Report
        } catch { $info.Text = '检查失败：' + $_.Exception.Message }
        finally { foreach ($b in $buttons) { $b.Enabled = $true }; $form.UseWaitCursor = $false }
    })
    $buttons[1].Add_Click({
        $answer = [Windows.Forms.MessageBox]::Show('将重新检查并永久删除超过 14 天未使用的临时文件。使用中的文件和保护目录会跳过。是否清理？', '清理临时文件', 'YesNo', 'Question')
        if ($answer -ne [Windows.Forms.DialogResult]::Yes) { return }
        foreach ($b in $buttons) { $b.Enabled = $false }; $form.UseWaitCursor = $true
        $info.Text = '正在清理，请稍候……'; $form.Refresh()
        try {
            $operation = Invoke-CleanerOperation $true
            $info.Text = '已清理 ' + $operation.Cleanup.DeletedFiles + ' 个文件，' + $operation.Cleanup.DeletedSize + '；跳过 ' + $operation.Cleanup.SkippedFiles + " 个。`r`n日志：" + $operation.Cleanup.Log
            $list.Items.Clear()
        } catch { $info.Text = '清理失败：' + $_.Exception.Message }
        finally { foreach ($b in $buttons) { $b.Enabled = $true }; $form.UseWaitCursor = $false }
    })
    $buttons[2].Add_Click({ try { $info.Text = Install-CleanerSchedule; $status.Text = Get-CleanerScheduleStatus } catch { $info.Text = '启用失败：' + $_.Exception.Message } })
    $buttons[3].Add_Click({ try { $info.Text = Remove-CleanerSchedule; $status.Text = Get-CleanerScheduleStatus } catch { $info.Text = '关闭失败：' + $_.Exception.Message } })
    $buttons[4].Add_Click({
        try {
            New-Item -ItemType Directory -Path $script:Reports -Force | Out-Null
            Start-Process -FilePath 'explorer.exe' -ArgumentList ('"' + $script:Reports + '"')
        } catch { $info.Text = $_.Exception.Message }
    })
    [void]$form.ShowDialog()
    $form.Dispose()
}

try {
    switch ($Mode) {
        'Gui' { Show-CleanerWindow }
        'Scan' { $result = Invoke-CleanerOperation $false; $result.Scan.Summary | Format-Table Category,Size,EligibleSize,Status -AutoSize; Write-Output ('Report: ' + $result.Report) }
        'Clean' {
            if (-not $ConfirmClean) { throw '命令行清理需加 -ConfirmClean；检查请使用 -Mode Scan。' }
            $result = Invoke-CleanerOperation $true
            $result.Cleanup | ConvertTo-Json
        }
        'InstallSchedule' { Install-CleanerSchedule }
        'RemoveSchedule' { Remove-CleanerSchedule }
        'Status' { Get-CleanerScheduleStatus }
    }
} catch {
    $fatal = $_
    try {
        New-Item -ItemType Directory -Path $script:Logs -Force | Out-Null
        [pscustomobject]@{At=(Get-Date).ToString('s'); Mode=$Mode; Error=$fatal.Exception.Message} |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $script:Logs ('错误-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.json')) -Encoding UTF8
    } catch { }
    Write-Error $fatal -ErrorAction Continue
    exit 1
}
