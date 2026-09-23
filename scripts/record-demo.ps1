$ErrorActionPreference = "Stop"

$env:Path += ";C:\Program Files (x86)\GnuWin32\bin"

$K3D = "C:\Users\rtwma\AppData\Local\Microsoft\WinGet\Packages\k3d.k3d_Microsoft.Winget.Source_8wekyb3d8bbwe\k3d.exe"
$NAMESPACE = "tidewater"

Write-Host ""
Write-Host "===== 1. START LOCAL SERVICES =====" -ForegroundColor Cyan
make up
make status

Write-Host ""
Write-Host "===== 2. VERIFY KUBERNETES CLUSTER =====" -ForegroundColor Cyan
kubectl get nodes
kubectl get pods -n $NAMESPACE

Write-Host ""
Write-Host "===== 3. IMPORT RELEASE IMAGES =====" -ForegroundColor Cyan
& $K3D image import settle-api:1.9.0 -c tidewater
& $K3D image import settle-api:1.9.1-rc -c tidewater

Write-Host ""
Write-Host "===== 4. DEPLOY GOOD RELEASE 1.9.0 =====" -ForegroundColor Cyan
kubectl -n $NAMESPACE set image deployment/settle-api settle-api=settle-api:1.9.0
kubectl -n $NAMESPACE rollout status deployment/settle-api --timeout=120s

Write-Host ""
Write-Host "===== 5. VERIFY 1.9.0 =====" -ForegroundColor Cyan
kubectl -n $NAMESPACE get deployment settle-api -o wide
kubectl -n $NAMESPACE get pods -l app=settle-api

Write-Host ""
Write-Host "===== 6. DEPLOY FAULTY 1.9.1-RC =====" -ForegroundColor Yellow
kubectl -n $NAMESPACE set image deployment/settle-api settle-api=settle-api:1.9.1-rc

Write-Host ""
Write-Host "===== 7. AUTOMATIC VERIFICATION =====" -ForegroundColor Cyan

$rollbackRequired = $false

try {
    kubectl -n $NAMESPACE rollout status deployment/settle-api --timeout=60s
}
catch {
    $rollbackRequired = $true
}

$badPods = kubectl -n $NAMESPACE get pods -l app=settle-api --no-headers |
    Select-String "CrashLoopBackOff|Error"

if ($badPods) {
    $rollbackRequired = $true
}

if ($rollbackRequired) {

    Write-Host ""
    Write-Host "!!! ALERT: DEPLOYMENT VERIFICATION FAILED !!!" -ForegroundColor Red
    Write-Host "Signal: rollout timeout / unhealthy pod / CrashLoopBackOff" -ForegroundColor Red
    Write-Host "Automatic rollback started..." -ForegroundColor Red

    kubectl -n $NAMESPACE rollout undo deployment/settle-api

    kubectl -n $NAMESPACE rollout status deployment/settle-api --timeout=120s

    Write-Host ""
    Write-Host "!!! ALERT RESOLVED: PREVIOUS VERSION RESTORED !!!" -ForegroundColor Green
}

Write-Host ""
Write-Host "===== 8. FINAL STATE =====" -ForegroundColor Cyan
kubectl -n $NAMESPACE get deployment settle-api -o wide
kubectl -n $NAMESPACE get pods -l app=settle-api

Write-Host ""
Write-Host "===== DEMO COMPLETE =====" -ForegroundColor Green