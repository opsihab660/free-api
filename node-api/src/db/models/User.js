/**
 * User model for MongoDB
 */

const mongoose = require('mongoose');
const Schema = mongoose.Schema;

// API Key schema
const ApiKeySchema = new Schema({
  key: { 
    type: String, 
    required: true,
    index: true,
    unique: true,
    sparse: true
  },
  name: { 
    type: String, 
    required: true,
    default: 'Default API Key'
  },
  created_at: { 
    type: String, 
    required: true 
  },
  last_used: { 
    type: String, 
    default: null 
  },
  active: { 
    type: Boolean, 
    default: true 
  }
});

// Model usage schema
const ModelUsageSchema = new Schema({
  request_count: { 
    type: Number, 
    default: 0 
  },
  input_tokens: { 
    type: Number, 
    default: 0 
  },
  output_tokens: { 
    type: Number, 
    default: 0 
  },
  cost: { 
    type: mongoose.Schema.Types.Decimal128, 
    default: 0 
  }
}, { _id: false, strict: false });

// User schema
const UserSchema = new Schema({
  username: { 
    type: String, 
    required: true, 
    unique: true,
    index: true
  },
  email: { 
    type: String, 
    required: true 
  },
  password_hash: { 
    type: String, 
    required: true 
  },
  full_name: { 
    type: String, 
    default: null 
  },
  active: { 
    type: Boolean, 
    default: true 
  },
  quota_left: { 
    type: Number, 
    default: 500000 
  },
  request_count: { 
    type: Number, 
    default: 0 
  },
  total_input_tokens: { 
    type: Number, 
    default: 0 
  },
  total_output_tokens: { 
    type: Number, 
    default: 0 
  },
  total_cost: { 
    type: mongoose.Schema.Types.Decimal128, 
    default: 0 
  },
  model_usage: { 
    type: Map, 
    of: ModelUsageSchema,
    default: {} 
  },
  user_id: { 
    type: String, 
    required: true,
    unique: true,
    index: true
  },
  account_created_at: { 
    type: String, 
    required: true 
  },
  last_login: { 
    type: String, 
    default: null 
  },
  login_count: { 
    type: Number, 
    default: 0 
  },
  access_token: { 
    type: String, 
    required: true,
    unique: true,
    index: true
  },
  api_key: { 
    type: ApiKeySchema, 
    default: null 
  }
}, {
  timestamps: true,
  strict: false // Allow additional fields
});

// Create the model
const User = mongoose.model('User', UserSchema, 'users');

module.exports = User;
