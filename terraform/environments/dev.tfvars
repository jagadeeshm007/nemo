# ==============================================================================
# Nemo Platform — Development Environment Terraform Variables
# ==============================================================================

environment         = "development"
aws_region          = "us-west-2"
vpc_cidr            = "10.0.0.0/16"
eks_cluster_version = "1.29"

eks_node_instance_types = ["m6i.large"]
eks_node_min_size       = 1
eks_node_max_size       = 3
eks_node_desired_size   = 2

db_instance_class = "db.t4g.medium"

redis_node_type = "cache.t4g.medium"

kafka_broker_instance    = "kafka.t3.small"
opensearch_instance_type = "t3.medium.search"
opensearch_volume_size   = 20
