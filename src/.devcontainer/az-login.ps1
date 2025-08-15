#!/usr/bin/env pwsh

function Update-GitFromAzureAccount {
    param (
        [Parameter(Mandatory)]
        $account
    )

    $email = $account.user.name
    $name = $email.Split("@")[0]

    git config --global user.name $name
    git config --global user.email $email
    git config --global credential.useHttpPath true

    Write-Host "Git configured with:"
    Write-Host "  user.name  = $name"
    Write-Host "  user.email = $email"
}

Write-Host "Starting Azure CLI login process..."

# Check if Azure CLI is installed
try {
    $azVersion = az version --output json 2>$null | ConvertFrom-Json
    Write-Host "Azure CLI version: $($azVersion.'azure-cli')"
}
catch {
    Write-Error "Azure CLI is not installed or not accessible"
    exit 1
}

# Check if already logged in
try {
    $currentAccount = az account show --output json 2>$null | ConvertFrom-Json
    
    if ($currentAccount) {
        Write-Host "Already logged in to Azure as: $($currentAccount.user.name)"
        Write-Host "Subscription: $($currentAccount.name) ($($currentAccount.id))"
        
        Write-Host "Refreshing Azure token..."
        az account get-access-token --output none
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Azure login verified and token refreshed successfully!"
            Update-GitFromAzureAccount -account $currentAccount
            exit 0
        }
    }
}
catch {
    Write-Host "No existing Azure login found or token expired"
}

# Attempt device code login
Write-Host "Initiating Azure device code login..."
Write-Host "This will open a browser or provide a device code for authentication"

try {
    az login
    
    if ($LASTEXITCODE -eq 0) {
        $account = az account show --output json | ConvertFrom-Json
        
        Write-Host "Successfully logged in to Azure!"
        Write-Host "Account: $($account.user.name)"
        Write-Host "Subscription: $($account.name) ($($account.id))"
        Write-Host "Tenant: $($account.tenantId)"

        Update-GitFromAzureAccount -account $account
    }
    else {
        Write-Error "Azure login failed"
        exit 1
    }
}
catch {
    Write-Error "An error occurred during Azure login: $_"
    exit 1
}
