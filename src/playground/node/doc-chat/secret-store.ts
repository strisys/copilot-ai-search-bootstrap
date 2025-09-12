/* eslint-disable @typescript-eslint/no-empty-function */
/* eslint-disable @typescript-eslint/no-var-requires */
import { SecretClient } from '@azure/keyvault-secrets';
import { DefaultAzureCredential } from '@azure/identity';
import { getLogger } from './debug.js';
import path from 'path';

const logger = getLogger('secret-store');
const KV_KEY = 'AZURE_KEY_VAULT_NAME';

const tryLoadEnvironmentVariablesFromEnvFile = (filePath: string = ''): boolean => {
  // Attempt to get the configuration parameters from a .env file if working locally.
  let fullPath = (filePath || module.path);

  if (!fullPath) {
    return false;
  }

  if (!fullPath.includes('.env')) {
    fullPath = path.join(fullPath, '.env');
  }

  logger(`attempting to load environment variables from .env file [${fullPath}]...`);

  // https://github.com/motdotla/dotenv#options
  const configResult = require('dotenv').config({ 
    path: fullPath 
  });

  if (configResult.error) {
    logger(`failed to load environment file from '${filePath}' ${configResult.error}`);
    return false;
  }

  logger('environment variables loaded from .env file successfully!');
  return true;
}

export interface ISecretStore {
  get(name: string): Promise<string>;
  getMany(names: Array<string>): Promise<{ [key: string]: any }> ;
}

export type SecretStoreType = ('azure-key-vault');

export class SecretStoreFactory {
  public static get(type: SecretStoreType, vaultName: (string | null) = null): ISecretStore {
    if (type === 'azure-key-vault') {
      return (new SecretStore(vaultName));
    }

    throw new Error(`Failed to create SecretStore with the specified type (type:${type})`);
  }
}

class SecretStore implements ISecretStore {
  private static _client: SecretClient;
  private static _cache: { [key: string] : string} = {};
  private _vaultName: (string | null) = null;

  constructor(vaultName: (string | null) = null) {
    this._vaultName = (vaultName || null);
  }

  private toVaultUrl(vaultName: string) {
    return `https://${vaultName}.vault.azure.net`;
  }

  private tryGetKeyVaultUrl(): string {
    if (this._vaultName) {
      return this.toVaultUrl(this._vaultName);
    }

    // The environment variable for AZURE-KEY-VAULT-NAME may be passed in
    // via or set in the .env file.  If its already set do not bother with env.
    this._vaultName = process.env[KV_KEY] as string;

    if (!this._vaultName) {
      tryLoadEnvironmentVariablesFromEnvFile();
      this._vaultName = process.env[KV_KEY] as string;
    }

    if ((!this._vaultName) || (this._vaultName === 'not-set')) {
      throw new Error(`Failed to create Azure Key Vault client.  The ${KV_KEY} environment variable was not set.`);
    }

    return this.toVaultUrl(this._vaultName);
  }

  private tryGetClient(): SecretClient {
    if (SecretStore._client) {
      return SecretStore._client;
    }

    try {
      const url = this.tryGetKeyVaultUrl();
      logger(`creating Azure key vault client (${url}) ...`);
      return (SecretStore._client = new SecretClient(url, new DefaultAzureCredential()));
    }
    catch (err) {
      const message = `Failed to create Azure Key Vault client. Could not create secret client. ${err}`;
      logger(message);

      throw new Error(message);
    }
  } 

  private getCachedValue(name: string): string {
    return (process.env[name] || SecretStore._cache[name]);
  }

  private async getStoredValue(name: string): Promise<string> {
    return (SecretStore._cache[name] = (await (this.tryGetClient()).getSecret(name)).value || '');
  }

  public async get(name: string): Promise<string> {
    return (this.getCachedValue(name) || (await this.getStoredValue(name)));
  }

  public async getMany(names: Array<string>): Promise<{ [key: string]: any }> {
    let values: { [key: string]: any } = {};

    for(let x = 0; (x < names.length); x++) {
      values[names[x]] = (await this.get(names[x]));
    }
    
    return values;
  }
}