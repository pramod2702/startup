# PowerShell script to fix the typo in trail_customer.html
$file = "trail_customer.html"
(Get-Content $file) | ForEach-Object {
    if ($_ -match 'isuccess') {
        $_ -replace 'isuccess', 'success', $_.PSPath -ParentPath (Split-Path -Leaf)
    }
}) | Set-Content $file
