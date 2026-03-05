# ==============================================================================
# Nemo Platform — Production Environment Terraform Variables
# ==============================================================================

environment         = "production"
aws_region          = "us-west-2"
vpc_cidr            = "10.0.0.0/16"
eks_cluster_version = "1.29"

eks_node_instance_types = ["m6i.xlarge"]
eks_node_min_size       = 3
eks_node_max_size       = 20
eks_node_desired_size   = 5

db_instance_class = "db.r6g.xlarge"

redis_node_type = "cache.r6g.large"

kafka_broker_instance    = "kafka.m5.large"
opensearch_instance_type = "r6g.large.search"
opensearch_volume_size   = 100
