# ==============================================================================
# MSK Module — Kafka
# ==============================================================================

variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "kafka_version" { type = string }
variable "broker_count" { type = number }
variable "broker_instance" { type = string }

resource "aws_security_group" "msk" {
  name_prefix = "nemo-${var.environment}-msk-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 9092
    to_port     = 9098
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_msk_cluster" "main" {
  cluster_name           = "nemo-${var.environment}"
  kafka_version          = var.kafka_version
  number_of_broker_nodes = var.broker_count

  broker_node_group_info {
    instance_type  = var.broker_instance
    client_subnets = slice(var.private_subnet_ids, 0, var.broker_count)

    storage_info {
      ebs_storage_info {
        volume_size = 100
      }
    }

    security_groups = [aws_security_group.msk.id]
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS_PLAINTEXT"
      in_cluster    = true
    }
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = "/aws/msk/nemo-${var.environment}"
      }
    }
  }
}

output "bootstrap_brokers" { value = aws_msk_cluster.main.bootstrap_brokers_tls }
output "zookeeper_connect" { value = aws_msk_cluster.main.zookeeper_connect_string }
