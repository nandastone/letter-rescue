## Hosting for wr.polarquake.com: a Cloudflare Pages project plus its custom
## domain and DNS record. Builds are uploaded by CI (see .github/workflows),
## not built by Cloudflare, so the project has no build or source config.
##
##   cd infra
##   cp terraform.tfvars.example terraform.tfvars   # fill in your IDs
##   tofu init && tofu apply
##
## The API token needs: Account > Cloudflare Pages > Edit, and
## Zone > DNS > Edit on polarquake.com.

terraform {
  required_version = ">= 1.6"
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token with Pages:Edit and DNS:Edit"
  type        = string
  sensitive   = true
}

variable "account_id" {
  description = "Cloudflare account ID"
  type        = string
}

variable "zone_id" {
  description = "Zone ID for polarquake.com"
  type        = string
}

variable "project_name" {
  description = "Pages project name (also its *.pages.dev subdomain)"
  type        = string
  default     = "letter-rescue"
}

variable "hostname" {
  description = "Public hostname for the game"
  type        = string
  default     = "wr.polarquake.com"
}

resource "cloudflare_pages_project" "game" {
  account_id        = var.account_id
  name              = var.project_name
  production_branch = "main"
}

resource "cloudflare_pages_domain" "game" {
  account_id   = var.account_id
  project_name = cloudflare_pages_project.game.name
  name         = var.hostname
}

# Pages serves the custom domain through this CNAME; proxying is required.
resource "cloudflare_dns_record" "game" {
  zone_id = var.zone_id
  name    = var.hostname
  type    = "CNAME"
  content = cloudflare_pages_project.game.subdomain
  ttl     = 1 # Automatic; required when proxied.
  proxied = true
}

output "pages_subdomain" {
  description = "The project's *.pages.dev address"
  value       = cloudflare_pages_project.game.subdomain
}

output "game_url" {
  value = "https://${var.hostname}/"
}
