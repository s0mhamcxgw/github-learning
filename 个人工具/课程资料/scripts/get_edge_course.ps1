param([string]$TitlePattern = '*bilibili*')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$courseWindows = @(Get-Process msedge -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -and $_.MainWindowTitle -like $TitlePattern })
if ($courseWindows.Count -ne 1) {
    throw '无法唯一定位课程窗口；请提供当前课程链接，或用TitlePattern缩小范围。'
}
$courseWindow = $courseWindows[0]
$courseRoot = [System.Windows.Automation.AutomationElement]::FromHandle($courseWindow.MainWindowHandle)
$courseCondition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Edit)
$courseEdits = $courseRoot.FindAll([System.Windows.Automation.TreeScope]::Descendants,$courseCondition)
foreach ($courseEdit in $courseEdits) {
    if ($courseEdit.Current.Name -match '地址和搜索栏|Address and search bar|搜索或输入') {
        $coursePattern = $null
        if ($courseEdit.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$coursePattern)) {
            $courseUrl = $coursePattern.Current.Value
            if ($courseUrl -notmatch '^https?://') { $courseUrl = 'https://' + $courseUrl }
            $courseUri = [Uri]$courseUrl
            if ($courseUri.Host -notmatch '(^|\.)bilibili\.com$|^b23\.tv$') { throw '当前标签不是B站课程；请提供需要整理的课程链接。' }
            if ($courseUri.AbsolutePath -match '(BV[a-zA-Z0-9]{10})') {
                $courseBvid = $Matches[1]
                $coursePart = 1
                if ($courseUri.Query -match '(?:\?|&)p=(\d+)') { $coursePart = [int]$Matches[1] }
                $courseUrl = 'https://www.bilibili.com/video/' + $courseBvid + '/?p=' + $coursePart
            }
            [PSCustomObject]@{ title=$courseWindow.MainWindowTitle; url=$courseUrl } | ConvertTo-Json -Compress
            return
        }
    }
}
throw '未读取到课程地址栏；请直接提供当前课程链接。'
