[CmdletBinding()]
param([ValidateSet('Backup','Proton','Restore','Status')][string]$Mode='Status')
$ErrorActionPreference='Stop'
$backupPath=Join-Path $PSScriptRoot '切换前代理备份.json'
$internetKey='HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
$connectionsKey=Join-Path $internetKey 'Connections'
$proxyNames=@('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY')

function Notify-ProxyChange {
    if (-not ('ProxySwitchNative' -as [type])) {
        Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class ProxySwitchNative {
    [DllImport("wininet.dll", SetLastError=true)]
    public static extern bool InternetSetOption(IntPtr hInternet, int option, IntPtr buffer, int length);
    [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam, uint flags, uint timeout, out UIntPtr result);
}
'@
    }
    [void][ProxySwitchNative]::InternetSetOption([IntPtr]::Zero,39,[IntPtr]::Zero,0)
    [void][ProxySwitchNative]::InternetSetOption([IntPtr]::Zero,37,[IntPtr]::Zero,0)
    [UIntPtr]$result=[UIntPtr]::Zero
    [void][ProxySwitchNative]::SendMessageTimeout([IntPtr]0xffff,0x1a,[UIntPtr]::Zero,'Environment',2,1500,[ref]$result)
}

function Get-ProxyRegistryRecord([string]$Path,[string]$Name) {
    $key=Get-Item -LiteralPath $Path -ErrorAction SilentlyContinue
    $exists=$null -ne $key -and @($key.GetValueNames()) -contains $Name
    $kind=$null; $value=$null
    if($exists) {
        $kind=[string]$key.GetValueKind($Name)
        $value=$key.GetValue($Name,$null,[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
        if($kind -eq 'Binary'){$value=[Convert]::ToBase64String($value)}
    }
    return [pscustomobject]@{Path=$Path;Name=$Name;Exists=$exists;Kind=$kind;Value=$value}
}

function Show-ProxyStatus {
    $settings=Get-ItemProperty -LiteralPath $internetKey
    [pscustomobject]@{
        SystemProxyEnabled=([int]$settings.ProxyEnable -ne 0)
        SystemProxyServer=$settings.ProxyServer
        UserHTTP_PROXY=[Environment]::GetEnvironmentVariable('HTTP_PROXY','User')
        UserHTTPS_PROXY=[Environment]::GetEnvironmentVariable('HTTPS_PROXY','User')
        UserALL_PROXY=[Environment]::GetEnvironmentVariable('ALL_PROXY','User')
        Backup=$backupPath
    } | ConvertTo-Json
}

if($Mode -eq 'Backup' -or $Mode -eq 'Proton') {
    if(-not (Test-Path -LiteralPath $backupPath)) {
        $records=@()
        foreach($name in @('ProxyEnable','ProxyServer','ProxyOverride','AutoConfigURL','AutoDetect')) {
            $records+=Get-ProxyRegistryRecord $internetKey $name
        }
        foreach($name in @('DefaultConnectionSettings','SavedLegacySettings')) {
            $records+=Get-ProxyRegistryRecord $connectionsKey $name
        }
        $environment=@()
        foreach($name in $proxyNames) {
            $environment+=[pscustomobject]@{Name=$name;Value=[Environment]::GetEnvironmentVariable($name,'User')}
        }
        [pscustomobject]@{At=(Get-Date).ToString('o');UserSid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value;Registry=$records;UserEnvironment=$environment} |
            ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $backupPath -Encoding UTF8
    }
}

if($Mode -eq 'Proton') {
    $before=Get-ItemProperty -LiteralPath $internetKey
    if($before.ProxyEnable -and $before.ProxyServer -and $before.ProxyServer -notmatch '^(127\.0\.0\.1|localhost):7897$') {
        throw '系统代理已不是预期的 Clash 地址，停止切换以避免覆盖新设置。'
    }
    Set-ItemProperty -LiteralPath $internetKey -Name ProxyEnable -Value 0 -Type DWord
    Remove-ItemProperty -LiteralPath $internetKey -Name ProxyServer -ErrorAction SilentlyContinue
    foreach($name in @('DefaultConnectionSettings','SavedLegacySettings')) {
        $record=Get-ProxyRegistryRecord $connectionsKey $name
        if($record.Exists -and $record.Kind -eq 'Binary') {
            $bytes=[Convert]::FromBase64String($record.Value)
            if($bytes.Length -gt 8) {
                # Remove only the manual-proxy flag, preserving other connection preferences.
                $bytes[8]=[byte]($bytes[8] -band 0xfd)
                Set-ItemProperty -LiteralPath $connectionsKey -Name $name -Value $bytes -Type Binary
            }
        }
    }
    foreach($name in $proxyNames) {
        $value=[Environment]::GetEnvironmentVariable($name,'User')
        if($value -match '^(https?|socks5h?)://(127\.0\.0\.1|localhost):7897/?$') {
            [Environment]::SetEnvironmentVariable($name,$null,'User')
        } elseif($value) { Write-Warning ('保留了其他代理变量：'+$name) }
        $current=[Environment]::GetEnvironmentVariable($name,'Process')
        if($current -match '^(https?|socks5h?)://(127\.0\.0\.1|localhost):7897/?$') {
            [Environment]::SetEnvironmentVariable($name,$null,'Process')
        }
    }
    Notify-ProxyChange
}

if($Mode -eq 'Restore') {
    $backup=Get-Content -LiteralPath $backupPath -Raw | ConvertFrom-Json
    if($backup.UserSid -ne [Security.Principal.WindowsIdentity]::GetCurrent().User.Value) {throw '备份不属于当前用户。'}
    foreach($record in $backup.Registry) {
        if($record.Exists) {
            if(-not (Test-Path -LiteralPath $record.Path)) { New-Item -Path $record.Path -Force | Out-Null }
            $value=$record.Value
            if($record.Kind -eq 'Binary') {$value=[Convert]::FromBase64String($record.Value)}
            Set-ItemProperty -LiteralPath $record.Path -Name $record.Name -Value $value -Type $record.Kind
        } else { Remove-ItemProperty -LiteralPath $record.Path -Name $record.Name -ErrorAction SilentlyContinue }
    }
    foreach($entry in $backup.UserEnvironment) {
        [Environment]::SetEnvironmentVariable($entry.Name,$entry.Value,'User')
        [Environment]::SetEnvironmentVariable($entry.Name,$entry.Value,'Process')
    }
    Notify-ProxyChange
}
Show-ProxyStatus
