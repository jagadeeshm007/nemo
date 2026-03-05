# ==============================================================================
# ElastiCache Module — Redis
# ==============================================================================

variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "node_type" { type = string }
variable "num_cache_nodes" { type = number }

resource "aws_elasticache_subnet_group" "main" {
  name       = "nemo-${var.environment}"
  subnet_ids = var.private_subnet_ids
}

resource "aws_security_group" "redis" {
  name_prefix = "nemo-${var.environment}-redis-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "nemo-${var.environment}"
  description          = "Nemo ${var.environment} Redis cluster"
  node_type            = var.node_type
  num_cache_clusters   = var.num_cache_nodes
  engine               = "redis"
  engine_version       = "7.1"
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  automatic_failover_enabled = var.num_cache_nodes > 1

  snapshot_retention_limit = 3
}

output "endpoint" { value = aws_elasticache_replication_group.main.primary_endpoint_address }
