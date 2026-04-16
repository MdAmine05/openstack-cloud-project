terraform {
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 1.54.0"
    }
  }
}

provider "openstack" {
  auth_url    = var.auth_url
  user_name   = var.user_name
  password    = var.password
  tenant_name = var.tenant_name
  region      = var.region
}

variable "auth_url"    { default = "http://YOUR_HOST_IP/identity" }
variable "user_name"   { default = "admin" }
variable "password"    {}   # sera demandé au runtime
variable "tenant_name" { default = "demo" }
variable "region"      { default = "RegionOne" }

resource "openstack_compute_instance_v2" "centos_vm" {
  name            = "centos-terraform-vm"
  image_name      = "centos-7"
  flavor_name     = "m1.centos7"
  key_pair        = "SSH"
  security_groups = ["default"]

  network {
    name = "private"
  }
}
