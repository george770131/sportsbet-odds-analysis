$content = (Get-Content "scratch/raw_oddsportal_cpbl.html") -join "`n"

$oddsMatches = [regex]::Matches($content, '\\\"active\\\":true,\\\"maxOdds\\\":([0-9\.]+),\\\"avgOdds\\\":([0-9\.]+)')
Write-Output "Found Odds blocks count: $($oddsMatches.Count)"

foreach ($om in $oddsMatches) {
    Write-Output "Max=$($om.Groups[1].Value) | Avg=$($om.Groups[2].Value)"
}
