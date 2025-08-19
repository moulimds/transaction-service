param (
    [string]$method,
    [string]$endpoint,
    [string]$body = ""
)

$baseUrl = "http://127.0.0.1:8000"

if ($method -ieq "get") {
    Invoke-WebRequest "$baseUrl$endpoint" -UseBasicParsing
}
elseif ($method -ieq "post") {
    Invoke-WebRequest "$baseUrl$endpoint" -Method POST -ContentType "application/json" -Body $body -UseBasicParsing
}
elseif ($method -ieq "put") {
    Invoke-WebRequest "$baseUrl$endpoint" -Method PUT -ContentType "application/json" -Body $body -UseBasicParsing
}
elseif ($method -ieq "delete") {
    Invoke-WebRequest "$baseUrl$endpoint" -Method DELETE -UseBasicParsing
}
else {
    Write-Host "Unsupported method: $method"
}
