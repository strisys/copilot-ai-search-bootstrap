variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "development"
}

variable "azure_subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "azure_tenant_id" {
  description = ""
  type        = string
}

variable "azure_client_id" {
  description = ""
  type        = string
}

variable "azure_client_secret" {
  description = ""
  type        = string
}