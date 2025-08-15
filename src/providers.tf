
terraform {
  required_version = ">= 1.10.3"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.31.0"
    }
    azapi = {
      source  = "Azure/azapi"
      version = ">=2.4.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.4"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6.2"
    }
    null = {
      source  = "hashicorp/null"
      version = ">= 3.2.3"
    }
    time = {
      source  = "hashicorp/time"
      version = ">= 0.13.0"
    }
    local = {
      source  = "hashicorp/local"
      version = ">= 2.2.3"
    }
    #  restapi = {
    #    source  = "Mastercard/restapi"
    #    version = "~> 1.19"
    #  }
  }
  #   backend "azurerm" {
  #     resource_group_name  = "rg-strisy-shared"
  #     storage_account_name = "strisysterraformstate"
  #     container_name       = "terrraformstate"
  #     key                  = "development/terraform.tfstate"
  #   }
}

provider "azurerm" {
  features {}
  alias           = "azure-default"
  subscription_id = var.azure_subscription_id
}

provider "azapi" {
  alias = "azure-default"
}

provider "azuread" {
  alias = "azure-default"
}

data "azurerm_client_config" "current" {
  provider = azurerm.azure-default
}
