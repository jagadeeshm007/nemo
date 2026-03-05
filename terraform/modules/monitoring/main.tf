# ==============================================================================
# Monitoring Module — CloudWatch, Prometheus remote write
# ==============================================================================

variable "environment" { type = string }
variable "cluster_name" { type = string }
variable "vpc_id" { type = string }

resource "aws_cloudwatch_log_group" "eks" {
  name              = "/aws/eks/${var.cluster_name}/cluster"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "application" {
  name              = "/nemo/${var.environment}/application"
  retention_in_days = 14
}

resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "nemo-${var.environment}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EKS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "EKS cluster CPU utilization is above 80%"

  dimensions = {
    ClusterName = var.cluster_name
  }
}

resource "aws_cloudwatch_metric_alarm" "high_memory" {
  alarm_name          = "nemo-${var.environment}-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/EKS"
  period              = 300
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "EKS cluster memory utilization is above 85%"

  dimensions = {
    ClusterName = var.cluster_name
  }
}
