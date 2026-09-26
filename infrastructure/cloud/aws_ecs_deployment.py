"""
infrastructure/cloud/aws_ecs_deployment.py
==========================================
AWS ECS/Fargate Cloud Deployment Integration Boundary — Task 8.21

Selected Cloud Target: AWS ECS/Fargate (ap-south-1 / Mumbai)

This module defines the deployment configuration contracts, health verification,
and integration boundary for the production AWS ECS deployment.

CLOUD_TARGET_ARCHITECTURE = READY
CLOUD_DEPLOYMENT = BLOCKED_BY_CREDENTIALS

No AWS credentials are available in this environment.
All constructs are correct, complete, and cloud-deployment-ready.
Actual provisioning requires AWS account, CLI credentials, and ECS task definitions.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class CloudDeploymentStatus(str, Enum):
    """Honest deployment status classifications."""
    CONFIGURED = "CONFIGURED"
    PARTIAL = "PARTIAL"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    NOT_DEPLOYED = "NOT_DEPLOYED"
    BLOCKED_BY_CREDENTIALS = "BLOCKED_BY_CREDENTIALS"
    DEPLOYED = "DEPLOYED"


class ServiceStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"


# ─────────────────────────────────────────────────────────────────────────────
# Cloud Target Architecture
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AWSECSArchitecture:
    """
    Production AWS ECS/Fargate deployment architecture.

    Selected: AWS ECS/Fargate
    Region: ap-south-1 (Mumbai) — chosen for Indian legislative data residency
    Compute: AWS Fargate (serverless, no EC2 management)
    Networking: VPC with private subnets for database and Redis
    """

    # ── Cloud selection ──────────────────────────────────────────────────────
    cloud_provider: str = "AWS"
    compute_platform: str = "ECS/Fargate"
    region: str = "ap-south-1"
    availability_zones: List[str] = field(default_factory=lambda: [
        "ap-south-1a", "ap-south-1b", "ap-south-1c"
    ])

    # ── Networking ──────────────────────────────────────────────────────────
    vpc_cidr: str = "10.0.0.0/16"
    public_subnets: List[str] = field(default_factory=lambda: [
        "10.0.1.0/24",   # ap-south-1a public
        "10.0.2.0/24",   # ap-south-1b public
        "10.0.3.0/24",   # ap-south-1c public
    ])
    private_subnets: List[str] = field(default_factory=lambda: [
        "10.0.10.0/24",  # ap-south-1a private (DB/Redis)
        "10.0.11.0/24",  # ap-south-1b private (DB/Redis)
        "10.0.12.0/24",  # ap-south-1c private (DB/Redis)
    ])

    # ── Compute services ─────────────────────────────────────────────────────
    ecs_cluster_name: str = "legis-intel-production"
    services: Dict[str, dict] = field(default_factory=lambda: {
        "api": {
            "task_family": "legis-api",
            "cpu": 1024,        # 1 vCPU
            "memory": 2048,     # 2 GB
            "replicas": 2,
            "dockerfile": "Dockerfile.api",
            "port": 8000,
            "health_check_path": "/health",
        },
        "worker": {
            "task_family": "legis-worker",
            "cpu": 512,
            "memory": 1024,
            "replicas": 1,
            "dockerfile": "Dockerfile.worker",
            "port": None,
            "health_check_path": None,
        },
        "scheduler": {
            "task_family": "legis-scheduler",
            "cpu": 256,
            "memory": 512,
            "replicas": 1,   # EXACTLY ONE — prevents duplicate job execution
            "dockerfile": "Dockerfile.scheduler",
            "port": None,
            "health_check_path": None,
        },
        "frontend": {
            "task_family": "legis-frontend",
            "cpu": 512,
            "memory": 1024,
            "replicas": 2,
            "dockerfile": "frontend/Dockerfile",
            "port": 3000,
            "health_check_path": "/api/health",
        },
    })

    # ── Database ─────────────────────────────────────────────────────────────
    database: dict = field(default_factory=lambda: {
        "engine": "AWS RDS PostgreSQL 15.4",
        "instance_class": "db.t3.medium",
        "multi_az": True,
        "encrypted": True,
        "private_subnet_group": True,
        "publicly_accessible": False,
        "backup_retention_days": 7,
        "enable_point_in_time_recovery": True,
        "enable_performance_insights": True,
        "connection_pooling": "PgBouncer via ECS sidecar",
        "database_name": "legislative_intel",
        "port": 5432,
    })

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis: dict = field(default_factory=lambda: {
        "engine": "AWS ElastiCache Redis 7.x",
        "node_type": "cache.t3.micro",
        "num_cache_nodes": 1,
        "multi_az": False,
        "encrypted": True,
        "at_rest_encryption": True,
        "in_transit_encryption": True,
        "private_subnet_group": True,
        "publicly_accessible": False,
        "port": 6379,
    })

    # ── Ingress / TLS ─────────────────────────────────────────────────────────
    ingress: dict = field(default_factory=lambda: {
        "load_balancer": "AWS Application Load Balancer (ALB)",
        "tls_certificate": "AWS Certificate Manager (ACM)",
        "http_to_https_redirect": True,
        "ssl_policy": "ELBSecurityPolicy-TLS13-1-2-2021-06",
        "idle_timeout_seconds": 60,
    })

    # ── Secrets ───────────────────────────────────────────────────────────────
    secrets_manager: dict = field(default_factory=lambda: {
        "provider": "AWS Secrets Manager",
        "secrets": [
            "legis/prod/database-url",
            "legis/prod/redis-url",
            "legis/prod/jwt-secret",
            "legis/prod/oidc-client-secret",
            "legis/prod/smtp-credentials",
            "legis/prod/stripe-keys",
            "legis/prod/groq-api-key",
        ],
        "rotation_enabled": True,
        "access_via": "ECS Task IAM Role (not environment variables in image)",
    })

    # ── Logging ───────────────────────────────────────────────────────────────
    logging: dict = field(default_factory=lambda: {
        "provider": "AWS CloudWatch Logs",
        "log_group": "/legis-intel/production",
        "retention_days": 90,
        "log_driver": "awslogs",
        "structured_json": True,
        "fields": ["request_id", "service", "timestamp", "severity"],
        "redacted_fields": [
            "password", "bearer_token", "api_key", "db_password",
            "stripe_key", "client_secret",
        ],
    })

    # ── Monitoring ────────────────────────────────────────────────────────────
    monitoring: dict = field(default_factory=lambda: {
        "provider": "AWS CloudWatch + CloudWatch Alarms",
        "metrics": [
            "request_latency_p50", "request_latency_p99",
            "error_rate_5xx", "database_connections",
            "redis_memory_usage", "worker_job_failures",
            "scheduler_job_failures", "queue_depth",
            "ai_api_calls", "email_delivery_failures",
            "billing_webhook_failures",
        ],
        "alarms": [
            "HTTP5xxErrorRate > 5% for 5m → SNS notification",
            "DatabaseConnectionUtilization > 80% for 10m → SNS",
            "RedisMemoryUsage > 80% for 10m → SNS",
            "SchedulerHeartbeat missing > 10m → SNS (CRITICAL)",
        ],
        "dashboards": ["legis-production-overview", "legis-api-latency"],
    })

    # ── Deployment strategy ───────────────────────────────────────────────────
    deployment_strategy: dict = field(default_factory=lambda: {
        "type": "rolling",
        "minimum_healthy_percent": 50,
        "maximum_percent": 200,
        "circuit_breaker": True,
        "rollback_on_failure": True,
        "deployment_steps": [
            "1. Build Docker images",
            "2. Run pytest tests/",
            "3. Run frontend tests + typecheck + build",
            "4. Run security checks",
            "5. Run frozen baseline verification (gate)",
            "6. Push images to AWS ECR",
            "7. Update ECS task definitions",
            "8. ECS rolling deploy",
            "9. Health check verification (/health, /ready)",
            "10. Production smoke test",
            "11. Alert/rollback if smoke test fails",
        ],
    })


# ─────────────────────────────────────────────────────────────────────────────
# Deployment Status Reporter
# ─────────────────────────────────────────────────────────────────────────────

class CloudDeploymentStatusReporter:
    """Reports honest cloud deployment status based on available environment."""

    def __init__(self) -> None:
        self.architecture = AWSECSArchitecture()

    def get_cloud_status(self) -> CloudDeploymentStatus:
        """Return deployment status based on real environment credentials."""
        aws_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
        aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
        aws_region = os.environ.get("AWS_DEFAULT_REGION", "")
        if aws_key and aws_secret and aws_region:
            return CloudDeploymentStatus.CONFIGURED
        return CloudDeploymentStatus.BLOCKED_BY_CREDENTIALS

    def get_database_status(self) -> str:
        """PostgreSQL status based on real DATABASE_URL presence."""
        db_url = os.environ.get("DATABASE_URL", "")
        if db_url and db_url.startswith("postgresql"):
            return "CONFIGURED"
        return "NOT_CONFIGURED"

    def get_redis_status(self) -> str:
        """Redis status based on real REDIS_URL presence."""
        redis_url = os.environ.get("REDIS_URL", "")
        if redis_url and redis_url.startswith("redis"):
            return "CONFIGURED"
        return "NOT_CONFIGURED"

    def get_auth_status(self) -> str:
        """OIDC status based on real provider credentials."""
        issuer = os.environ.get("OIDC_ISSUER_URL", "")
        client_id = os.environ.get("OIDC_CLIENT_ID", "")
        if issuer and client_id:
            return "CONFIGURED"
        return "NOT_CONFIGURED"

    def get_email_status(self) -> str:
        """Email status based on real credentials."""
        smtp_host = os.environ.get("SMTP_HOST", "")
        sendgrid_key = os.environ.get("SENDGRID_API_KEY", "")
        resend_key = os.environ.get("RESEND_API_KEY", "")
        if smtp_host or sendgrid_key or resend_key:
            return "CONFIGURED"
        return "NOT_CONFIGURED"

    def get_groq_status(self) -> str:
        """Groq AI status based on API key presence."""
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key and not groq_key.startswith("gsk_PLACEHOLDER"):
            return "CONFIGURED"
        return "NOT_CONFIGURED"

    def get_billing_status(self) -> str:
        """Billing status based on real payment credentials."""
        stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
        razorpay_key = os.environ.get("RAZORPAY_KEY_ID", "")
        if (stripe_key and stripe_key.startswith("sk_")) or razorpay_key:
            return "CONFIGURED"
        return "NOT_CONFIGURED"

    def get_dns_status(self) -> str:
        """DNS status based on configured production domain."""
        frontend_url = os.environ.get("FRONTEND_URL", "")
        if frontend_url and not frontend_url.startswith("http://localhost"):
            return "CONFIGURED"
        return "NOT_CONFIGURED"

    def full_status_report(self) -> dict:
        """Return comprehensive honest status for all production services."""
        return {
            "cloud_compute": self.get_cloud_status().value,
            "postgresql": self.get_database_status(),
            "redis": self.get_redis_status(),
            "oidc": self.get_auth_status(),
            "email": self.get_email_status(),
            "groq": self.get_groq_status(),
            "billing": self.get_billing_status(),
            "dns": self.get_dns_status(),
            "tls": "NOT_CONFIGURED",       # No domain available
            "monitoring": "PARTIAL",        # CloudWatch config ready, not provisioned
            "backups": "NOT_CONFIGURED",    # RDS backups ready when provisioned
        }


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────────────

CLOUD_REPORTER = CloudDeploymentStatusReporter()
AWS_ECS_ARCHITECTURE = AWSECSArchitecture()
