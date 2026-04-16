<<<<<<< HEAD
# openstack-cloud-project
=======
# OpenStack Cloud Computing Project

Projet réalisé dans le cadre du cours **Cloud et Edge Computing** (Prof. C. EL AMRANI).

## Description

Ce projet couvre trois parties :

### Partie 1 — OpenStack / DevStack
- Déploiement d'OpenStack via DevStack dans VirtualBox
- Création d'une VM IaaS basée sur CirrOS
- Développement d'une application SaaS Flask (CloudForge)

### Partie 2 — Infrastructure as Code avec Terraform
- Provisionnement automatique d'une VM CentOS via Terraform
- Configuration du provider OpenStack

### Partie 3 — SLA et Supervision
- Définition d'un SLA avec objectif de disponibilité 99.5%
- Script Python de monitoring interagissant avec Nova, Keystone, Neutron
- Exécution automatique toutes les 5 minutes via cron

## Stack technique

- OpenStack (DevStack) — Nova, Neutron, Glance, Keystone, Horizon
- Python 3 + Flask
- Terraform v1.14
- Ubuntu 22.04 / VirtualBox

## Structure
├── terraform/        # Configuration Terraform (main.tf)
├── sla-monitor/      # Script Python de supervision SLA
├── saas-app/         # Application Flask CloudForge
└── devstack/         # Configuration DevStack (local.conf)
## Environnement

- VirtualBox VM : Ubuntu Server 22.04
- IP DevStack : 192.168.56.10
- Dashboard Horizon : http://192.168.56.10/dashboard
>>>>>>> 140aacc (Initial commit - OpenStack Cloud Project (DevStack + Terraform + SLA))
