$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$ghCommand = Get-Command gh -ErrorAction SilentlyContinue
$ghPath = if ($ghCommand) { $ghCommand.Source } else { Join-Path $env:TEMP 'stock-project-gh\bin\gh.exe' }
if (-not (Test-Path -LiteralPath $ghPath)) {
    throw 'Install GitHub CLI from https://cli.github.com/ and rerun this script.'
}
& $ghPath auth status
if ($LASTEXITCODE -ne 0) {
    & $ghPath auth login --hostname github.com --git-protocol https --web
    if ($LASTEXITCODE -ne 0) { throw 'GitHub login failed. Check your connection and retry.' }
}
$account = & $ghPath api user --jq .login
if ($LASTEXITCODE -ne 0 -or $account -ne 'Gjh07788509-gif') { throw 'Sign in as Gjh07788509-gif before publishing.' }
& $ghPath auth setup-git
if ($LASTEXITCODE -ne 0) { throw 'Git credential setup failed.' }
& $ghPath repo create 'Gjh07788509-gif/stock-market-analysis' --private --source . --remote origin --push --description 'Stock return and risk analysis with MySQL 8, Python and Streamlit'
if ($LASTEXITCODE -ne 0) { throw 'Repository creation or push failed. Inspect the message above before retrying.' }
Write-Output 'Published: https://github.com/Gjh07788509-gif/stock-market-analysis'
