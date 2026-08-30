$content = (Get-Content "scratch/raw_oddsportal_cpbl.html") -join "`n"

# 測試用正則 (包含 Singleline / DOTALL 標記)
$pattern = '(?si)\\\"encodeEventId\\\":\\\"([a-zA-Z0-9]{8})\\\".*?\\\"url\\\":\\\"/baseball/h2h/([a-z0-9\-]+)-[a-zA-Z0-9]+/([a-z0-9\-]+)-[a-zA-Z0-9]+/#([a-zA-Z0-9]{8})\\\".*?\\\"colClassName\\\":\\\"datet t(\d+)-'
$matches = [regex]::Matches($content, $pattern)
Write-Output "DOTALL Matches count: $($matches.Count)"

foreach ($m in $matches) {
    $hash = $m.Groups[1].Value
    $home = $m.Groups[2].Value
    $away = $m.Groups[3].Value
    $ts = $m.Groups[5].Value
    Write-Output "Match: $home vs $away | Hash: $hash | TS: $ts"
}
