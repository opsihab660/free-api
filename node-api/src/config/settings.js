/**
 * Application settings and configuration
 */

// Load environment variables
require('dotenv').config();

// Server settings
const LOCAL_SERVER_PORT = parseInt(process.env.LOCAL_SERVER_PORT || '8002');

// API settings
const BACKEND_API_BASE_URL = process.env.BACKEND_API_BASE_URL || 'https://api.devsdocode.com/v1';
const YOUR_BACKEND_API_KEY = process.env.MY_BACKEND_API_KEY || 'ddc-temp-free-e3b73cd814cc4f3ea79b5d4437912663';
const PROVIDER_PREFIX = 'provider-4/';

// MongoDB settings
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb+srv://username:password@cluster.mongodb.net/';
const MONGODB_DB_NAME = process.env.MONGODB_DB_NAME || 'api_service_db';
const MONGODB_USER_COLLECTION = process.env.MONGODB_USER_COLLECTION || 'users';

// Model costs
const MODEL_COSTS = {
  'gpt-4.1': {
    input_cost_per_token: 0.00001,
    output_cost_per_token: 0.00003,
    comment: 'GPT-4.1 Turbo'
  },
  'gpt-4.1-mini': {
    input_cost_per_token: 0.000005,
    output_cost_per_token: 0.000015,
    comment: 'GPT-4.1 Mini'
  },
  'gpt-4.1-nano': {
    input_cost_per_token: 0.0000025,
    output_cost_per_token: 0.0000075,
    comment: 'GPT-4.1 Nano'
  },
  'gpt-4o': {
    input_cost_per_token: 0.000005,
    output_cost_per_token: 0.000015,
    comment: 'GPT-4o'
  },
  'gpt-4o-mini': {
    input_cost_per_token: 0.0000015,
    output_cost_per_token: 0.0000045,
    comment: 'GPT-4o Mini'
  },
  'o3-mini': {
    input_cost_per_token: 0.0000015,
    output_cost_per_token: 0.0000045,
    comment: 'o3-mini'
  },
  'deepseek-r1': {
    input_cost_per_token: 0.0000025,
    output_cost_per_token: 0.0000075,
    comment: 'DeepSeek R1'
  },
  'deepseek-v3': {
    input_cost_per_token: 0.0000025,
    output_cost_per_token: 0.0000075,
    comment: 'DeepSeek V3'
  },
  'llama-4-scout': {
    input_cost_per_token: 0.0000025,
    output_cost_per_token: 0.0000075,
    comment: 'Llama 4 Scout'
  },
  'llama-4-maverick': {
    input_cost_per_token: 0.000005,
    output_cost_per_token: 0.000015,
    comment: 'Llama 4 Maverick'
  },
  'mistral-large-latest': {
    input_cost_per_token: 0.000005,
    output_cost_per_token: 0.000015,
    comment: 'Mistral Large Latest'
  },
  'mistral-small': {
    input_cost_per_token: 0.0000015,
    output_cost_per_token: 0.0000045,
    comment: 'Mistral Small'
  },
  'gemini-2.5-flash-preview-04-17': {
    input_cost_per_token: 0.0000015,
    output_cost_per_token: 0.0000045,
    comment: 'Gemini 2.5 Flash Preview'
  },
  'gemini-2.5-pro-exp-03-25': {
    input_cost_per_token: 0.000005,
    output_cost_per_token: 0.000015,
    comment: 'Gemini 2.5 Pro Exp'
  },
  'default_model_for_costing': {
    input_cost_per_token: 0,
    output_cost_per_token: 0,
    comment: 'Default if model not found'
  }
};

// Model name mapping
const MODEL_NAME_MAPPING = {};
[
  'gpt-4.1', 'gpt-4.1-mini', 'gpt-4.1-nano', 'gpt-4o', 'gpt-4o-mini', 'o3-mini',
  'deepseek-r1', 'deepseek-v3', 'llama-4-scout', 'llama-4-maverick',
  'mistral-large-latest', 'mistral-small',
  'gemini-2.5-flash-preview-04-17', 'gemini-2.5-pro-exp-03-25'
].forEach(name => {
  MODEL_NAME_MAPPING[name] = `${PROVIDER_PREFIX}${name}`;
});

module.exports = {
  LOCAL_SERVER_PORT,
  BACKEND_API_BASE_URL,
  YOUR_BACKEND_API_KEY,
  PROVIDER_PREFIX,
  MONGODB_URI,
  MONGODB_DB_NAME,
  MONGODB_USER_COLLECTION,
  MODEL_COSTS,
  MODEL_NAME_MAPPING
};
