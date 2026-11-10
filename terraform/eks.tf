module "eks" {

  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = "radio-platform"
  kubernetes_version = "1.34"

  enable_cluster_creator_admin_permissions = true
  endpoint_public_access                   = true

  vpc_id = module.vpc.vpc_id

  subnet_ids = module.vpc.private_subnets

  #   cluster_addons = {
  # coredns    = {}
  # kube-proxy = {}
  # vpc-cni    = {}
  #   }

  eks_managed_node_groups = {
    default = {

      instance_types = [
        "t3.micro"
      ]

      capacity_type = "ON_DEMAND"

      min_size     = 1
      max_size     = 2
      desired_size = 1
    }
  }
}