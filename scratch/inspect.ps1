$content = Get-Content -Path "scratch/raw_oddsportal_cpbl.html" -Raw
$matches = [regex]::Matches($content, '(?i)(Fubon|Rakuten|Brothers|Lions|Dragons|Hawks|Uni-President)[^"<>]{0,100}')
Write-Output "Found count: $($matches.Count)"
foreach ($m in ($matches | Select-Object -First 15)) {
    Write-Output "MATCH: $($m.Value)"
}

$events = [regex]::Matches($content, '\{[^{}]*?"eventId"\s*:\s*(\d+)[^{}]*?\}')
Write-Output "Events found: $($events.Count)"
foreach ($e in ($events | Select-Object -First 5)) {
    Write-Output "EVENT: $($e.Value)"
}
