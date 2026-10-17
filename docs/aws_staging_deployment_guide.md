# AWS Staging Deployment Guide

This guide details the deployment architecture, configuration steps, and operational procedures for launching the **Intelligent Portfolio Creation Application** in an AWS Staging environment.

---

## 1. Architecture Overview & VPC Topology

```
+-----------------------------------------------------------------------------------+
| AWS Region: ap-south-1 (Mumbai)                                                   |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | AWS Amplify (Next.js 16 Frontend)                                           |  |
|  | - Hosted globally via AWS CDN / Edge                                        |  |
|  | - Environment: NEXT_PUBLIC_API_URL=https://api-staging.yourdomain.com        |  |
|  +-----------------------------------------------------------------------------+  |
|                                        |                                          |
|                                        v HTTPS (Port 443)                         |
|  +-----------------------------------------------------------------------------+  |
|  | VPC (10.0.0.0/16)                                                           |  |
|  |                                                                             |  |
|  |   +---------------------------------------------------------------------+   |  |
|  |   | Public Subnet (10.0.1.0/24)                                         |   |  |
|  |   |   - Application Load Balancer (ALB) / Nginx Reverse Proxy with TLS  |   |  |
|  |   |   - EC2 Instance (t4g.small or t3.medium)                           |   |  |
|  |   |     * FastAPI + LangGraph backend                                   |   |  |
|  |   |     * systemd service managed by gunicorn/uvicorn                   |   |  |
|  |   |     * IAM Role with SSM & CloudWatch permissions                    |   |  |
|  |   +---------------------------------------------------------------------+   |  |
|  |                                     |                                       |  |
|  |                                     v Private DB Subnet (Port 5432)         |  |
|  |   +---------------------------------------------------------------------+   |  |
|  |   | Private DB Subnet (10.0.2.0/24 & 10.0.3.0/24)                       |   |  |
|  |   |   - Amazon RDS PostgreSQL 16 (db.t4g.micro)                         |   |  |
|  |   |   - Inaccessible from public internet                               |   |  |
|  |   |   - Security Group only allows ingress from EC2 SG on port 5432     |   |  |
|  |   +---------------------------------------------------------------------+   |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
|  +-------------------------------------+   +-----------------------------------+  |
|  | AWS Secrets Manager / SSM Parameter |   | CloudWatch Logs & Alarms          |  |
|  | - DATABASE_URL, JWT_SECRET_KEY      |   | - Error log alarms                |  |
|  | - GEMINI_API_KEY, APP_ENV=staging   |   | - Latency & memory alarms         |  |
|  +-------------------------------------+   +-----------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Secrets & Configuration Management

Never commit production or staging secrets to source control. Use **AWS Systems Manager Parameter Store** (SecureString) or **AWS Secrets Manager**.

### Parameter Store Hierarchy (`/portfolio-app/staging/`)

| Parameter Name | Type | Description |
|---|---|---|
| `/portfolio-app/staging/DATABASE_URL` | SecureString | `postgresql://db_user:db_pass@staging-rds.czx.ap-south-1.rds.amazonaws.com:5432/portfolio_staging` |
| `/portfolio-app/staging/JWT_SECRET_KEY` | SecureString | 64-character cryptographically random secret (`openssl rand -hex 32`) |
| `/portfolio-app/staging/GEMINI_API_KEY` | SecureString | Google Gemini API Key for LangGraph nodes |
| `/portfolio-app/staging/APP_ENV` | String | `staging` (triggers strict fail-closed JWT enforcement) |
| `/portfolio-app/staging/CORS_ORIGINS` | String | `https://staging.yourdomain.amplifyapp.com,https://staging.yourdomain.com` |
| `/portfolio-app/staging/LOG_LEVEL` | String | `INFO` |

### EC2 IAM Role Permissions (`PortfolioStagingBackendRole`)
Attach policy granting:
- `ssm:GetParametersByPath` on `arn:aws:ssm:ap-south-1:<account-id>:parameter/portfolio-app/staging/*`
- `logs:CreateLogStream`, `logs:PutLogEvents` on `arn:aws:logs:ap-south-1:<account-id>:log-group:/portfolio-app/staging/*`

---

## 3. Database Setup & Restore Testing Protocol

### Provisioning Amazon RDS PostgreSQL
1. **Engine Version:** PostgreSQL 16.3+
2. **Instance Class:** `db.t4g.micro` (Burstable, ARM-based Graviton2, cost-efficient for staging).
3. **Storage:** 20 GB gp3 with storage autoscaling enabled up to 50 GB.
4. **VPC & Subnet Group:** Place RDS in private subnets across 2 AZs (`ap-south-1a`, `ap-south-1b`).
5. **Security Group:** Inbound TCP 5432 **only** from the EC2 Backend Security Group (`sg-ec2-backend`).
6. **Automated Backups:**
   - Backup retention period: 7 days.
   - Backup window: 03:00–04:00 UTC (off-peak Indian hours).
   - Point-in-time recovery (PITR) enabled.

### Database Migration & Seeding
On initial launch or CI/CD deployment:
```bash
# Run Alembic migrations against staging RDS (using canonical DATABASE_URL)
DATABASE_URL="postgresql://db_user:db_pass@staging-rds.czx.ap-south-1.rds.amazonaws.com:5432/portfolio_staging" \
  ./.venv/bin/alembic upgrade head

# Seed initial securities, listings, sectors, and benchmark data
DATABASE_URL="postgresql://db_user:db_pass@staging-rds.czx.ap-south-1.rds.amazonaws.com:5432/portfolio_staging" \
  ./.venv/bin/python -m backend.seed.seed_data
```

### Database Recovery Testing Protocol (AWS Reliability Pillar)
AWS Well-Architected Framework requires distinguishing between **Snapshot Restores** and true **Point-In-Time Recovery (PITR)**:

#### Procedure A: Manual Snapshot Restore Drill
Proves an operator can restore a specific historical point-in-time snapshot:
1. **Trigger Manual Snapshot:**
   ```bash
   aws rds create-db-snapshot \
     --db-instance-identifier portfolio-staging-rds \
     --db-snapshot-identifier staging-manual-snapshot-$(date +%Y%m%d) \
     --region ap-south-1
   ```
2. **Restore Snapshot to Temporary Drill Instance:**
   ```bash
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier drill-snapshot-test \
     --db-snapshot-identifier staging-manual-snapshot-$(date +%Y%m%d) \
     --db-instance-class db.t4g.micro \
     --vpc-security-group-ids sg-rds-private \
     --db-subnet-group-name portfolio-db-subnets \
     --publicly-accessible false \
     --region ap-south-1
   ```
3. **Validate Restored Schema & Holdings:**
   ```bash
   psql -h <drill-snapshot-test-endpoint> -U db_user -d portfolio_staging \
     -c "SELECT count(*) FROM securities; SELECT count(*) FROM portfolio_versions;"
   ```
4. **Teardown Snapshot Drill Instance:**
   ```bash
   aws rds delete-db-instance --db-instance-identifier drill-snapshot-test --skip-final-snapshot
   ```

#### Procedure B: True Point-In-Time Recovery (PITR) Drill
Proves continuous write-ahead log (WAL) restoration to an arbitrary second within the backup retention window:
1. **Identify Target Restore Time (e.g. 1 hour ago UTC):**
   ```bash
   RESTORE_TIME=$(date -u -v-1H +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "1 hour ago" +"%Y-%m-%dT%H:%M:%SZ")
   echo "Executing PITR drill to target time: $RESTORE_TIME"
   ```
2. **Execute Point-In-Time Restore Command:**
   ```bash
   aws rds restore-db-instance-to-point-in-time \
     --source-db-instance-identifier portfolio-staging-rds \
     --target-db-instance-identifier drill-pitr-test \
     --restore-time "$RESTORE_TIME" \
     --db-instance-class db.t4g.micro \
     --vpc-security-group-ids sg-rds-private \
     --db-subnet-group-name portfolio-db-subnets \
     --publicly-accessible false \
     --region ap-south-1
   ```
3. **Verify Restored Endpoint Connectivity & Audit Table Counts:**
   ```bash
   psql -h <drill-pitr-test-endpoint> -U db_user -d portfolio_staging \
     -c "SELECT count(*) AS total_tables FROM information_schema.tables WHERE table_schema='public';"
   ```
4. **Teardown PITR Drill Instance:**
   ```bash
   aws rds delete-db-instance --db-instance-identifier drill-pitr-test --skip-final-snapshot
   ```

---

## 4. Backend Deployment (FastAPI + LangGraph on EC2)

### Provisioning EC2
1. **AMI:** Ubuntu Server 24.04 LTS (HVM), **ARM64** (`aarch64`).  
   *(Strict Architecture Requirement: AWS Graviton `t4g.small` is an ARM64 processor; do not select an x86_64 AMI).*
2. **Instance Type:** `t4g.small` (2 vCPU, 2 GB RAM).
3. **Storage:** 30 GB gp3 root EBS volume.
4. **Security Group (`sg-ec2-backend`):**
   - Inbound 22: Restricted to Administrator IP or via AWS Systems Manager Session Manager (recommended, requires zero open inbound ports).
   - Inbound 443 / 80: Restricted to Application Load Balancer (or Nginx with Let's Encrypt).

### Secret Bootstrap Script (`/opt/portfolio-app/scripts/bootstrap_env.sh`)
Pulls encrypted secrets from AWS Systems Manager Parameter Store into the application environment file:
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Fetching staging secrets from AWS SSM Parameter Store..."
aws ssm get-parameters-by-path \
  --path "/portfolio-app/staging" \
  --with-decryption \
  --region ap-south-1 \
  --query "Parameters[*].[Name,Value]" \
  --output text | awk '{split($1,a,"/"); print a[4]"="$2}' > /etc/portfolio-backend.env

chmod 600 /etc/portfolio-backend.env
echo "Environment configuration successfully generated at /etc/portfolio-backend.env"
```

### Systemd Service Configuration (`/etc/systemd/system/portfolio-backend.service`)
```ini
[Unit]
Description=Intelligent Portfolio Optimization Backend API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/portfolio-app
EnvironmentFile=/etc/portfolio-backend.env
Environment="PYTHONPATH=/opt/portfolio-app"
# Single worker for 2GB RAM t4g.small to avoid memory pressure from SciPy and LLM calls
ExecStart=/opt/portfolio-app/.venv/bin/uvicorn backend.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 1 \
    --log-config /opt/portfolio-app/backend/logging.conf
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy Configuration (`/etc/nginx/sites-available/portfolio-api`)
```nginx
server {
    listen 80;
    server_name api-staging.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api-staging.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api-staging.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api-staging.yourdomain.com/privkey.pem;

    # Timeouts for LangGraph optimization execution
    proxy_connect_timeout 60s;
    proxy_read_timeout 120s;
    proxy_send_timeout 120s;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check bypass
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

---

## 5. Frontend Deployment (AWS Amplify Hosting)

1. **Connect GitHub Repository:** Link repository `main` branch to AWS Amplify console.
2. **App Framework:** Select Next.js (SSR / Static).
3. **Build Settings (`amplify.yml`):**
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: frontend/.next
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
      - frontend/.next/cache/**/*
```
4. **Environment Variables in Amplify Console:**
   - `NEXT_PUBLIC_API_URL`: `https://api-staging.yourdomain.com`

---

## 6. CloudWatch Monitoring & Cost Alerts

### CloudWatch Alarms
1. **Backend 5xx Error Rate Alarm:**
   - Metric: Nginx 5xx or FastAPI HTTP 500 responses > 5 over 5 minutes.
   - Action: Send SNS notification to DevOps email.
2. **RDS CPU Utilization Alarm:**
   - Metric: CPUUtilization > 80% for 15 minutes.
3. **EC2 Health Check Failure Alarm:**
   - Metric: StatusCheckFailed_System > 0.

### AWS Budgets & Cost Controls
1. Create a monthly cost budget in **AWS Budgets**:
   - Budget Amount: `$25.00 / month`
   - Threshold 1: 80% ($20.00) -> Email alert to Administrator.
   - Threshold 2: 100% ($25.00) -> High-priority SNS notification + trigger Lambda to stop non-essential EC2 instances.
2. Itemized Monthly Staging Cost (AWS Mumbai `ap-south-1` Pricing Calculator):
   - **EC2 `t4g.small` (ARM64, 2GB RAM):** ~$12.26 / month (or $0.00 if using first-month AWS Graviton free trial).
   - **RDS PostgreSQL `db.t4g.micro` (20GB gp3, Single-AZ):** ~$13.14 / month (or free tier eligible for first 12 months with 20GB storage).
   - **Public IPv4 Address ($0.005/hr):** ~$3.60 / month (eliminated if instance uses private subnet with AWS Systems Manager / Amplify).
   - **AWS Amplify Hosting:** ~$0.00 / month (within Free Tier: 1,000 build minutes, 5 GB storage, 15 GB served).
   - **Total Estimated Staging Cost:** ~$25.40 – $29.00 / month before Free Tier offsets; effectively **$0.00 – $5.00 / month** on active AWS Free Tier accounts.
   - *Important Operational Rule:* AWS Budget alerts notify administrators but **do not automatically shut down resources**. Configure an AWS Budget Action or CloudWatch billing alarm with an automated Lambda stop-instance target to strictly cap spending at $25.00/month.
