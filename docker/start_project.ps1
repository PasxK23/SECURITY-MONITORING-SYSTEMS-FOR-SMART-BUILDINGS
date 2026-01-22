$CPUS = 4
$MEMORY = "6144mb"
Write-Host "Ξεκινάω το περιβάλλον Kubernetes με $CPUS CPUs και $MEMORY RAM..." -ForegroundColor Green
minikube start --driver=docker --cpus=$CPUS --memory=$MEMORY --driver=docker

Write-Host "Building Docker images..." -ForegroundColor Yellow

Write-Host "Σύνδεση με το Docker του Minikube..." -ForegroundColor Cyan
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

$images = @(
    @{ name = "fastapi-ids"; path = "./fastapiserver" },
    @{ name = "sniffer";       path = "./sniffer" },
    @{ name = "score-manager";  path = "./score_manager" },
    @{ name = "ban-service";    path = "./ip_ban" },
    @{ name = "subscribers";    path = "./subscribers" },
    @{ name = "ben_publishers"; path = "./ben_publishers" },
    @{ name = "attackers";      path = "./attackers" }
)

foreach ($img in $images) {
    Write-Host "Building image: $($img.name) από το φάκελο: $($img.path)..." -ForegroundColor Yellow
    
    # Χτίσιμο του image μέσα στο περιβάλλον του Minikube
    docker build -t "$($img.name):latest" $($img.path)
}

Start-Sleep -Seconds 10

Write-Host "Εφαρμογή namespace..." -ForegroundColor Cyan
kubectl apply -f emqx/namespace.yaml

Write-Host "Εφαρμογή Redis..." -ForegroundColor Cyan
kubectl apply -f emqx/k8s/redis.yaml

Write-Host "Εφαρμογή EMQX configs..." -ForegroundColor Cyan
kubectl apply -f emqx/k8s/emqx-configmap.yaml
kubectl apply -f emqx/k8s/emqx-secret.yaml
kubectl apply -f emqx/k8s/emqx-headless.yaml
kubectl apply -f emqx/k8s/emqx-service.yaml
kubectl apply -f emqx/k8s/emqx-statefulset.yaml

Write-Host "Αναμονή για να είναι έτοιμος ο EMQX..." -ForegroundColor Cyan
kubectl wait --for=condition=ready pod -l app=emqx --timeout=30s -n emqx

Write-Host "Εφαρμογή FastAPI Server..." -ForegroundColor Cyan
kubectl apply -f fastapiserver/fastapiserver.yaml

Write-Host "Εφαρμογή Sniffer..." -ForegroundColor Cyan
kubectl apply -f sniffer/daemonset.yaml

Write-Host "Εφαρμογή Score Manager..." -ForegroundColor Cyan
kubectl apply -f score_manager/manager.yaml

Write-Host "Εφαρμογή IP Ban Service..." -ForegroundColor Cyan
kubectl apply -f ip_ban/ban_service.yaml

Write-Host "Εφαρμογή Subscribers..." -ForegroundColor Cyan
kubectl apply -f subscribers/subscribers.yaml

Write-Host "Εφαρμογή Benign Publishers..." -ForegroundColor Cyan
kubectl apply -f ben_publishers/ben_publishers.yaml


Write-Host "Όλα τα services έχουν εφαρμοστεί επιτυχώς!" -ForegroundColor Green