/**
 * Authentication routes
 * @swagger
 * tags:
 *   name: Authentication
 *   description: User authentication and API key management
 *
 * components:
 *   schemas:
 *     UserRegister:
 *       type: object
 *       required:
 *         - username
 *         - email
 *         - password
 *       properties:
 *         username:
 *           type: string
 *           description: User's unique username
 *         email:
 *           type: string
 *           format: email
 *           description: User's email address
 *         password:
 *           type: string
 *           format: password
 *           description: User's password
 *         full_name:
 *           type: string
 *           description: User's full name
 *
 *     UserLogin:
 *       type: object
 *       required:
 *         - username
 *         - password
 *       properties:
 *         username:
 *           type: string
 *           description: User's username
 *         password:
 *           type: string
 *           format: password
 *           description: User's password
 *
 *     ApiKeyCreate:
 *       type: object
 *       required:
 *         - name
 *       properties:
 *         name:
 *           type: string
 *           description: Name for the API key
 *
 *     Error:
 *       type: object
 *       properties:
 *         error:
 *           type: object
 *           properties:
 *             message:
 *               type: string
 *               description: Error message
 *             type:
 *               type: string
 *               description: Error type
 */

const express = require('express');
const router = express.Router();
const asyncHandler = require('express-async-handler');
const {
  userRegisterSchema,
  userLoginSchema,
  apiKeyCreateSchema
} = require('./models');
const {
  hashPassword,
  verifyPassword,
  generateApiKey,
  generateUserId,
  getCurrentTimestamp
} = require('../utils/security');
const {
  updateUser,
  getUserByUsername,
  getUserByApiKey,
  getUserByAccessToken
} = require('../db/userRepository');

/**
 * Authenticate user via bearer token
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next function
 */
async function authenticateUserViaBearer(req, res, next) {
  try {
    // Get authorization header
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        error: {
          message: 'API key not provided',
          type: 'authentication_error'
        }
      });
    }

    // Extract the token
    const userKey = authHeader.split(' ')[1];
    let userData = null;

    // First, try to get user from MongoDB by API key
    userData = await getUserByApiKey(userKey);

    // If not found by API key, try access token
    if (!userData) {
      userData = await getUserByAccessToken(userKey);
    }

    // If found in MongoDB, update in-memory store
    if (userData) {
      global.USER_API_KEYS_STORE[userKey] = userData;
    }

    // If not found in MongoDB, check in-memory store
    if (!userData) {
      // Check if this is a direct key in our store (could be access token or API key)
      userData = global.USER_API_KEYS_STORE[userKey];

      // If not found directly, search through all users' API key
      if (!userData) {
        for (const [key, data] of Object.entries(global.USER_API_KEYS_STORE)) {
          if (data.api_key && data.api_key.key === userKey) {
            // Found a valid key, use the parent user data
            userData = data;
            break;
          }
        }
      }
    }

    // If still not found, authentication fails
    if (!userData) {
      console.warn(`Auth failed: Invalid key ...${userKey.slice(-4)}`);
      return res.status(401).json({
        error: {
          message: 'API key not valid',
          type: 'authentication_error'
        }
      });
    }

    // Check if API key is active
    if (userData.api_key && userData.api_key.key === userKey) {
      if (!userData.api_key.active) {
        console.warn(`Auth failed: Inactive API key ...${userKey.slice(-4)} for user '${userData.username}'`);
        return res.status(403).json({
          error: {
            message: 'This API key is inactive',
            type: 'permission_error'
          }
        });
      }

      // Update last used time for this key
      const now = getCurrentTimestamp();
      userData.api_key.last_used = now;
    }

    // Check if user account is active
    if (!userData.active) {
      console.warn(`Auth failed: Inactive account for user '${userData.username}' (key ...${userKey.slice(-4)})`);
      return res.status(403).json({
        error: {
          message: 'This user account is inactive',
          type: 'permission_error'
        }
      });
    }

    // Check quota
    const currentQuota = userData.quota_left;
    if (currentQuota !== null && currentQuota !== undefined && currentQuota <= 0) {
      console.warn(`Quota exceeded for user '${userData.username}' (key ...${userKey.slice(-4)})`);
      return res.status(429).json({
        error: {
          message: 'API usage quota exceeded',
          type: 'quota_exceeded'
        }
      });
    }

    // Store user data and key in request for later use
    req.userData = userData;
    req.userKey = userKey;

    // Continue to the next middleware or route handler
    next();
  } catch (error) {
    console.error(`Authentication error: ${error.message}`);
    res.status(500).json({
      error: {
        message: 'Internal server error during authentication',
        type: 'server_error'
      }
    });
  }
}

/**
 * @swagger
 * /auth/register:
 *   post:
 *     summary: Register a new user
 *     tags: [Authentication]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/UserRegister'
 *     responses:
 *       201:
 *         description: User registered successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 access_token:
 *                   type: string
 *                   description: JWT access token
 *                 token_type:
 *                   type: string
 *                   example: bearer
 *                 user_info:
 *                   type: object
 *                   properties:
 *                     username:
 *                       type: string
 *                     email:
 *                       type: string
 *                     full_name:
 *                       type: string
 *                     quota_left:
 *                       type: integer
 *                     active:
 *                       type: boolean
 *                     user_id:
 *                       type: string
 *       400:
 *         description: Invalid input or username already exists
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
// Register a new user
router.post('/register', asyncHandler(async (req, res) => {
  // Validate request body
  const { error, value } = userRegisterSchema.validate(req.body);
  if (error) {
    return res.status(400).json({
      error: {
        message: error.details[0].message,
        type: 'validation_error'
      }
    });
  }

  // Check if username already exists in MongoDB first
  const existingUser = await getUserByUsername(value.username);
  if (existingUser) {
    return res.status(400).json({
      error: {
        message: 'Username already registered',
        type: 'duplicate_user'
      }
    });
  }

  // Also check in-memory store as a fallback
  for (const [key, data] of Object.entries(global.USER_API_KEYS_STORE)) {
    if (data.username === value.username) {
      return res.status(400).json({
        error: {
          message: 'Username already registered',
          type: 'duplicate_user'
        }
      });
    }
  }

  // Generate access token (not API key)
  const accessToken = generateApiKey('access_token');
  const now = getCurrentTimestamp();

  // Hash the password
  const hashedPassword = await hashPassword(value.password);

  // Generate a user ID
  const userId = generateUserId();

  // Create user entry without API key structure
  const newUser = {
    username: value.username,
    email: value.email,
    password_hash: hashedPassword,
    full_name: value.full_name || null,
    active: true,
    quota_left: 500000, // Default quota for new users
    request_count: 0,
    total_input_tokens: 0,
    total_output_tokens: 0,
    total_cost: 0.0,
    model_usage: {},
    user_id: userId,
    account_created_at: now,
    last_login: null,
    access_token: accessToken
  };

  // Add to in-memory store
  global.USER_API_KEYS_STORE[accessToken] = newUser;

  // Save to MongoDB
  await updateUser(accessToken, newUser);
  console.log(`User '${value.username}' registered and saved to MongoDB.`);

  // Return token and user info
  res.status(201).json({
    access_token: accessToken,
    token_type: 'bearer',
    user_info: {
      username: value.username,
      email: value.email,
      full_name: value.full_name || null,
      quota_left: 500000,
      active: true,
      user_id: userId
    }
  });
}));

/**
 * @swagger
 * /auth/login:
 *   post:
 *     summary: Login a user
 *     tags: [Authentication]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/UserLogin'
 *     responses:
 *       200:
 *         description: Login successful
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 access_token:
 *                   type: string
 *                   description: JWT access token
 *                 token_type:
 *                   type: string
 *                   example: bearer
 *                 user_info:
 *                   type: object
 *                   properties:
 *                     username:
 *                       type: string
 *                     email:
 *                       type: string
 *                     full_name:
 *                       type: string
 *                     quota_left:
 *                       type: integer
 *                     active:
 *                       type: boolean
 *                     user_id:
 *                       type: string
 *       401:
 *         description: Invalid username or password
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       403:
 *         description: User account is inactive
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
// Login a user
router.post('/login', asyncHandler(async (req, res) => {
  // Validate request body
  const { error, value } = userLoginSchema.validate(req.body);
  if (error) {
    return res.status(400).json({
      error: {
        message: error.details[0].message,
        type: 'validation_error'
      }
    });
  }

  // Find user by username
  let userKey = null;
  let userInfo = null;

  // First try to find user in MongoDB
  const mongoUser = await getUserByUsername(value.username);
  if (mongoUser && mongoUser.password_hash) {
    // Verify password
    const passwordValid = await verifyPassword(mongoUser.password_hash, value.password);
    if (passwordValid) {
      // Get access token from user document
      if (mongoUser.access_token) {
        userKey = mongoUser.access_token;
        userInfo = mongoUser;
        // Update in-memory store
        global.USER_API_KEYS_STORE[userKey] = mongoUser;
      }
    }
  }

  // If not found in MongoDB, check in-memory store
  if (!userKey || !userInfo) {
    for (const [key, data] of Object.entries(global.USER_API_KEYS_STORE)) {
      if (data.username === value.username) {
        // Verify password
        if (data.password_hash) {
          const passwordValid = await verifyPassword(data.password_hash, value.password);
          if (passwordValid) {
            userKey = key;
            userInfo = data;
            break;
          }
        }
      }
    }
  }

  if (!userKey || !userInfo) {
    return res.status(401).json({
      error: {
        message: 'Invalid username or password',
        type: 'authentication_error'
      }
    });
  }

  if (!userInfo.active) {
    return res.status(403).json({
      error: {
        message: 'User account is inactive',
        type: 'permission_error'
      }
    });
  }

  // Update last login time
  const now = getCurrentTimestamp();
  userInfo.last_login = now;
  userInfo.login_count = (userInfo.login_count || 0) + 1;

  // Update last used time for the API key if it exists
  if (userInfo.api_key) {
    userInfo.api_key.last_used = now;
  }

  // Update in-memory store
  global.USER_API_KEYS_STORE[userKey] = userInfo;

  // Save to MongoDB
  await updateUser(userKey, userInfo);
  console.log(`User '${value.username}' login updated in MongoDB.`);

  // Return token and user info
  res.json({
    access_token: userKey,
    token_type: 'bearer',
    user_info: {
      username: userInfo.username,
      email: userInfo.email || '',
      full_name: userInfo.full_name || '',
      quota_left: userInfo.quota_left,
      active: userInfo.active || true,
      user_id: userInfo.user_id || ''
    }
  });
}));

/**
 * @swagger
 * /auth/keys:
 *   post:
 *     summary: Create a new API key
 *     tags: [Authentication]
 *     security:
 *       - BearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/ApiKeyCreate'
 *     responses:
 *       200:
 *         description: API key created successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 key_id:
 *                   type: string
 *                   description: Unique identifier for the API key
 *                 name:
 *                   type: string
 *                   description: Name of the API key
 *                 key:
 *                   type: string
 *                   description: The API key value
 *                 created_at:
 *                   type: integer
 *                   description: Timestamp when the key was created
 *                 last_used:
 *                   type: integer
 *                   nullable: true
 *                   description: Timestamp when the key was last used
 *                 active:
 *                   type: boolean
 *                   description: Whether the key is active
 *       400:
 *         description: Invalid input
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       401:
 *         description: Unauthorized
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
// Create a new API key
router.post('/keys', authenticateUserViaBearer, asyncHandler(async (req, res) => {
  // Validate request body
  const { error, value } = apiKeyCreateSchema.validate(req.body);
  if (error) {
    return res.status(400).json({
      error: {
        message: error.details[0].message,
        type: 'validation_error'
      }
    });
  }

  const userData = req.userData;
  const username = userData.username;

  // Generate a new API key
  const newApiKey = generateApiKey();
  const now = getCurrentTimestamp();

  // Store the old key if it exists
  let oldKey = null;
  if (userData.api_key) {
    oldKey = userData.api_key.key;
  }

  // Update the API key in the user data
  userData.api_key = {
    key: newApiKey,
    name: value.name,
    created_at: now,
    last_used: null,
    active: true
  };

  // Update in-memory store
  global.USER_API_KEYS_STORE[req.userKey] = userData;

  // If there was an old key, add the updated user data with the new key
  if (oldKey && oldKey !== req.userKey) {
    // Remove the old key from the store
    delete global.USER_API_KEYS_STORE[oldKey];

    // Add the new key to the store
    global.USER_API_KEYS_STORE[newApiKey] = userData;
  }

  // Save to MongoDB
  await updateUser(req.userKey, userData);
  console.log(`Created new API key for user '${username}'`);

  // Return the new API key
  res.json({
    key_id: newApiKey.split('_')[1], // Just the random part
    name: value.name,
    key: newApiKey, // Include the full key in the response
    created_at: now,
    last_used: null,
    active: true
  });
}));

/**
 * @swagger
 * /auth/profile:
 *   get:
 *     summary: Get user profile information
 *     tags: [Authentication]
 *     security:
 *       - BearerAuth: []
 *     responses:
 *       200:
 *         description: User profile information
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 username:
 *                   type: string
 *                   description: User's username
 *                 email:
 *                   type: string
 *                   description: User's email address
 *                 full_name:
 *                   type: string
 *                   description: User's full name
 *                 user_id:
 *                   type: string
 *                   description: Unique user identifier
 *                 quota_left:
 *                   type: integer
 *                   description: Remaining API usage quota
 *                 request_count:
 *                   type: integer
 *                   description: Total number of API requests made
 *                 total_input_tokens:
 *                   type: integer
 *                   description: Total input tokens used
 *                 total_output_tokens:
 *                   type: integer
 *                   description: Total output tokens generated
 *                 total_cost:
 *                   type: number
 *                   description: Total cost of API usage
 *                 account_created_at:
 *                   type: integer
 *                   description: Timestamp when the account was created
 *                 last_login:
 *                   type: integer
 *                   nullable: true
 *                   description: Timestamp of last login
 *                 active:
 *                   type: boolean
 *                   description: Whether the account is active
 *                 api_key:
 *                   type: object
 *                   nullable: true
 *                   properties:
 *                     key_id:
 *                       type: string
 *                     name:
 *                       type: string
 *                     created_at:
 *                       type: integer
 *                     last_used:
 *                       type: integer
 *                       nullable: true
 *                     active:
 *                       type: boolean
 *                 model_usage:
 *                   type: object
 *                   description: Usage statistics per model
 *       401:
 *         description: Unauthorized
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
// Get user profile
router.get('/profile', authenticateUserViaBearer, asyncHandler(async (req, res) => {
  const userData = req.userData;

  // Format API key info
  let apiKeyInfo = null;
  if (userData.api_key) {
    apiKeyInfo = {
      key_id: userData.api_key.key.split('_')[1], // Just the random part
      name: userData.api_key.name,
      created_at: userData.api_key.created_at,
      last_used: userData.api_key.last_used,
      active: userData.api_key.active || true
    };
  }

  // Get model usage statistics
  const modelUsage = userData.model_usage || {};

  res.json({
    username: userData.username,
    email: userData.email || '',
    full_name: userData.full_name || '',
    user_id: userData.user_id || '',
    quota_left: userData.quota_left,
    request_count: userData.request_count || 0,
    total_input_tokens: userData.total_input_tokens || 0,
    total_output_tokens: userData.total_output_tokens || 0,
    total_cost: userData.total_cost || 0,
    account_created_at: userData.account_created_at,
    last_login: userData.last_login,
    active: userData.active || true,
    api_key: apiKeyInfo,
    model_usage: modelUsage
  });
}));

module.exports = router;
module.exports.authenticateUserViaBearer = authenticateUserViaBearer;
