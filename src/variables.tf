variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "development"
}

variable "organization" {
  description = "Organization tag"
  type        = string
}

variable "project_tag" {
  description = "Project tag"
  type        = string
}

variable "azure_subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "azure_tenant_id" {
  description = ""
  type        = string
}
