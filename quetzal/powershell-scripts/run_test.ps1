Write-Host "Starting test execution..."
$output = & python test_simple.py
Write-Host "Test output:"
$output
Write-Host "Test execution completed."
$output | Out-File -FilePath "test_simple_output.txt" 