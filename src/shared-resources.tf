# resource "time_sleep" "sleep30s" {
#   create_duration = "30s"
# }

resource "azurerm_resource_group" "rg" {
  provider = azurerm.azure-default
  name     = local.azure_resource_group_name
  location = local.azure_location
}

data "azurerm_resource_group" "rg_shared" {
  provider = azurerm.azure-default
  name     = local.azure_resource_group_name_shared
}


# data "azuread_group" "developer" {
#   object_id = "0c20fd34-c9af-4bc0-b4f1-e1c678cd01c1"
# }
