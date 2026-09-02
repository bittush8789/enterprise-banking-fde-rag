# ☸️ AWS EKS Kubernetes Deployment Guide — BankAssist AI (Pinecone Branch)

This runbook details the end-to-end steps to deploy **BankAssist AI** (with Pinecone Serverless Vector DB and MySQL) onto an **Amazon Elastic Kubernetes Service (AWS EKS)** cluster.

---

## 📋 Architecture Overview on EKS

```text
[ Internet / Banking Staff ]
             │
             ▼
[ AWS Application Load Balancer (ALB) ]
             │ (TLS 443 / SSL Redirect)
             ▼
[ Ingress Controller (AWS Load Balancer Controller) ]
             │
             ▼
[ ClusterIP Service: bankassist-backend-service ]
             │
   ┌─────────┴─────────┐ (HPA: 2 to 10 Pods)
   ▼                   ▼
[ Pod: Backend-1 ]  [ Pod: Backend-2 ]
   │                   │
   ├─► [ Pinecone Serverless Cloud Vector DB ]
   │
   ├─► [ Groq Cloud API (qwen/qwen3.6-27b) ]
   │
   └─► [ ClusterIP Service: bankassist-mysql ] ──► [ EBS gp3 Persistent Volume ]
```

---

## 🛠️ Prerequisites

Ensure you have the following CLI tools installed and configured:
1. **AWS CLI** (`aws configure`)
2. **eksctl** (`eksctl version`)
3. **kubectl** (`kubectl version --client`)
4. **Helm 3** (`helm version`)
5. **Docker** (`docker version`)

---

## 🚀 Step-by-Step Deployment Runbook

### Step 1: Create Amazon ECR Repository & Push Docker Image

```bash
# 1. Set variables
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REPO_NAME="bankassist-ai"
export IMAGE_TAG="latest"

# 2. Create ECR repository
aws ecr create-repository \
  --repository-name ${ECR_REPO_NAME} \
  --region ${AWS_REGION} \
  --image-scanning-configuration scanOnPush=true

# 3. Authenticate Docker with Amazon ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# 4. Build and tag the Docker image
docker build -t ${ECR_REPO_NAME}:${IMAGE_TAG} -f docker/Dockerfile .
docker tag ${ECR_REPO_NAME}:${IMAGE_TAG} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:${IMAGE_TAG}

# 5. Push image to Amazon ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:${IMAGE_TAG}
```

*Update `k8s/backend-deployment.yaml` with your full image URI (`${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/bankassist-ai:latest`).*

---

### Step 2: Provision the AWS EKS Cluster with `eksctl`

```bash
eksctl create cluster \
  --name bankassist-cluster \
  --region us-east-1 \
  --version 1.30 \
  --nodegroup-name bankassist-nodes \
  --node-type t3.xlarge \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 6 \
  --managed \
  --with-oidc
```

Configure your local `kubectl` context:
```bash
aws eks update-kubeconfig --region us-east-1 --name bankassist-cluster
```

---

### Step 3: Install AWS Load Balancer Controller & EBS CSI Driver

```bash
# 1. Install AWS EBS CSI Driver (for MySQL PVC persistence)
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster bankassist-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve \
  --role-only

eksctl create addon \
  --name aws-ebs-csi-driver \
  --cluster bankassist-cluster \
  --service-account-role-arn arn:aws:iam::${AWS_ACCOUNT_ID}:role/ebs-csi-controller-sa \
  --force

# 2. Install AWS Load Balancer Controller via Helm
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=bankassist-cluster \
  --set serviceAccount.create=true
```

---

### Step 4: Configure Secrets & Deploy Kubernetes Manifests

```bash
# 1. Create the dedicated Namespace
kubectl apply -f k8s/namespace.yaml

# 2. Apply ConfigMap
kubectl apply -f k8s/configmap.yaml

# 3. Configure Secrets (Update with your Groq API Key and Pinecone API Key)
kubectl apply -f k8s/secret.yaml

# 4. Deploy MySQL Database (Storage & Pod)
kubectl apply -f k8s/mysql-pvc.yaml
kubectl apply -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/mysql-service.yaml

# 5. Deploy FastAPI Backend with Pinecone RAG Engine
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml

# 6. Apply Ingress (ALB) and Horizontal Pod Autoscaler (HPA)
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

---

### Step 5: Verification & Status Monitoring

Check the status of all cluster resources:
```bash
# View all pods in the namespace
kubectl get pods -n bankassist-ai -o wide

# Check services
kubectl get svc -n bankassist-ai

# Check Horizontal Pod Autoscaler
kubectl get hpa -n bankassist-ai

# Get the AWS Application Load Balancer DNS Name
kubectl get ingress -n bankassist-ai
```

Once the ALB is provisioned (approx. 2-3 minutes), open the `ADDRESS` URL in your browser:
```text
http://k8s-bankassi-bankassi-xxxxxxxxxx.us-east-1.elb.amazonaws.com
```

---

### Step 6: Pod Scaling & Real-time Logs

```bash
# Stream live logs from backend pods
kubectl logs -f -l app.kubernetes.io/name=bankassist-backend -n bankassist-ai

# Test pod scaling manually
kubectl scale deployment bankassist-backend --replicas=5 -n bankassist-ai
```

---

## 🧹 Teardown & Clean-up

To avoid unnecessary AWS cloud charges:
```bash
kubectl delete -f k8s/
eksctl delete cluster --name bankassist-cluster --region us-east-1
```
