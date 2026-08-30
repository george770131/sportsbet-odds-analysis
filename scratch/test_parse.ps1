$content = (Get-Content "scratch/raw_oddsportal_cpbl.html") -join "`n"

# 1. 抽取所有 match JSON 物件
# 正則匹配 encodeEventId 與 url
$eventPattern = '(?i)\\\"encodeEventId\\\":\\\"([a-zA-Z0-9]{8})\\\".*?\\\"url\\\":\\\"/baseball/h2h/([a-z0-9\-]+)-[a-zA-Z0-9]+/([a-z0-9\-]+)-[a-zA-Z0-9]+/#([a-zA-Z0-9]{8})\\\".*?\\\"colClassName\\\":\\\"datet t(\d+)-'
$matches = [regex]::Matches($content, $eventPattern)

Write-Output "Found Events count: $($matches.Count)"

foreach ($m in $matches) {
    $hash = $m.Groups[1].Value
    $homeSlug = $m.Groups[2].Value
    $awaySlug = $m.Groups[3].Value
    $ts = [int64]$m.Groups[5].Value
    
    # 轉換時間
    $utcDate = (Get-Date "1970-01-01 00:00:00").AddSeconds($ts)
    $twDate = $utcDate.AddHours(8)
    $twStr = $twDate.ToString("yyyy-MM-dd HH:mm")

    # 尋找該 Hash 對應的精準 odds
    # 格式: \"vZUtcB2n\":{\"event\":10102491,\"odds\":[{\"active\":true,\"maxOdds\":1.76,\"avgOdds\":1.72 ... \"avgOdds\":2.01
    $oddsRegex = '(?i)\\\"' + $hash + '\\\":\{\\\"event\\\":\d+,\\\"odds\\\":\[\{\\\"active\\\":true,\\\"maxOdds\\\":([0-9\.]+),\\\"avgOdds\\\":([0-9\.]+).*?\\\"active\\\":true,\\\"maxOdds\\\":([0-9\.]+),\\\"avgOdds\\\":([0-9\.]+)'
    $om = [regex]::Match($content, $oddsRegex)
    if ($om.Success) {
        $hOdds = $om.Groups[2].Value
        $aOdds = $om.Groups[4].Value
        Write-Output "EVENT: $homeSlug (Home) vs $awaySlug (Away) | Time: $twStr (TW) | Hash: $hash | HomeML: $hOdds | AwayML: $aOdds"
    } else {
        Write-Output "EVENT: $homeSlug vs $awaySlug | Time: $twStr | Hash: $hash | NO ODDS MATCH"
    }
}
