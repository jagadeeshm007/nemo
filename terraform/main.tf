# ==============================================================================
# Nemo Platform — Terraform Root Module
# ==============================================================================

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  backend "s3" {
    bucket         = "nemo-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "nemo-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "nemo"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ==============================================================================
# Modules
# ==============================================================================

module "networking" {
  source = "./modules/networking"

  environment     = var.environment
  vpc_cidr        = var.vpc_cidr
  azs             = var.availability_zones
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets
}

module "eks" {
  source = "./modules/eks"

  environment         = var.environment
  cluster_name        = "${var.project_name}-${var.environment}"
  cluster_version     = var.eks_cluster_version
  vpc_id              = module.networking.vpc_id
  private_subnet_ids  = module.networking.private_subnet_ids
  node_instance_types = var.eks_node_instance_types
  node_min_size       = var.eks_node_min_size
  node_max_size       = var.eks_node_max_size
  node_desired_size   = var.eks_node_desired_size
}

module "rds" {
  source = "./modules/rds"

  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  db_name            = var.db_name
  db_username        = var.db_username
  db_instance_class  = var.db_instance_class
  db_engine_version  = "16.2"
  multi_az           = var.environment == "production"
}

module "elasticache" {
  source = "./modules/elasticache"

  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  node_type          = var.redis_node_type
  num_cache_nodes    = var.environment == "production" ? 3 : 1
}

module "msk" {
  source = "./modules/msk"

  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  kafka_version      = "3.6.0"
  broker_count       = var.environment == "production" ? 3 : 1
  broker_instance    = var.kafka_broker_instance
}

module "opensearch" {
  source = "./modules/opensearch"

  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  instance_type      = var.opensearch_instance_type
  instance_count     = var.environment == "production" ? 3 : 1
  volume_size        = var.opensearch_volume_size
}

module "monitoring" {
  source = "./modules/monitoring"

  environment    = var.environment
  cluster_name   = module.eks.cluster_name
  vpc_id         = module.networking.vpc_id
}
