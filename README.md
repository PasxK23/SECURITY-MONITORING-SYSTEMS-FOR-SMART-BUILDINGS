# SECURITY MONITORING SYSTEMS FOR SMART BUILDINGS

## Description

This project implements a security monitoring system for smart buildings using MQTT protocol, Docker, and Kubernetes. It includes components for publishing/subscribing to MQTT topics, detecting malicious activities via AI models, and managing security responses such as IP banning.

## Prerequisites

- Docker and Docker Compose
- Kubernetes (Minikube for local development)
- kubectl
- Python 3.9+
- Git

## Architecture

The system consists of the following components:

- **EMQX Broker**: MQTT message broker deployed on Kubernetes.
- **Publishers**: Benign publishers that send MQTT messages.
- **Subscribers**: Components that subscribe to MQTT topics.
- **Sniffer**: Monitors network traffic and logs data for analysis.
- **Score Manager**: Manages scoring for security events.
- **Ban Service**: Bans IPs based on detected threats.
- **Attackers**: Simulated attackers for testing.

## Setup and Running

1. Open PowerShell as administrator
2. Navigate to the project path: `cd <project_path>`
3. Set execution policy: `Set-ExecutionPolicy Bypass -Scope Process -Force`
4. Run the start script: `Get-Content ./start_project.ps1 -Encoding UTF8 | Out-String | Invoke-Expression`

## Ban Service Configuration

To run the ban-service, you need to access the EMQX dashboard:

1. Run: `minikube service emqx -n emqx`
2. Open the dashboard using the link given
2. Go to System -> API Keys -> Create
3. Copy the API Key and Secret Key to `ip_ban/ban-service.yaml` in the fields `EMQX_API_SECRET_KEY` and `EMQX_API_KEY`

## Note on Attackers

The attackers do not run from the script. If you want to run the attackers as well:

`kubectl apply -f attackers/attackers.yaml -n emqx`

## AI Model

The AI model is used for detecting malicious MQTT traffic. It is trained on datasets located in the `AI model/` folder.

To train or test the model:

1. Navigate to `AI model/`
2. Open `model_train.ipynb` in Jupyter Notebook.
3. Run the cells to train the model using the provided datasets (e.g., `mqtt_dataset_final_combined.csv`).

The model can classify traffic as benign or malicious.
