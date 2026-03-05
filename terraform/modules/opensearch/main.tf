# ==============================================================================
# OpenSearch Module — Elasticsearch-compatible search
# ==============================================================================

variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "instance_type" { type = string }
variable "instance_count" { type = number }
variable "volume_size" { type = number }

resource "aws_security_group" "opensearch" {
  name_prefix = "nemo-${var.environment}-opensearch-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  ingress {
    from_port   = 9200
    to_port     = 9200
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}

resource "aws_opensearch_domain" "main" {
  domain_name    = "nemo-${var.environment}"
  engine_version = "OpenSearch_2.13"

  cluster_config {
    instance_type          = var.instance_type
    instance_count         = var.instance_count
    zone_awareness_enabled = var.instance_count > 1

    dynamic "zone_awareness_config" {
      for_each = var.instance_count > 1 ? [1] : []
      content {
        availability_zone_count = min(var.instance_count, 3)
      }
    }
  }

  ebs_options {
    ebs_enabled = true
    volume_size = var.volume_size
    volume_type = "gp3"
  }

  vpc_options {
    subnet_ids         = slice(var.private_subnet_ids, 0, min(var.instance_count, 3))
    security_group_ids = [aws_security_group.opensearch.id]
  }

  encrypt_at_rest { enabled = true }
  node_to_node_encryption { enabled = true }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-PFS-2023-10"
  }
}

output "endpoint" { value = aws_opensearch_domain.main.endpoint }
output "dashboard_endpoint" { value = aws_opensearch_domain.main.dashboard_endpoint }
