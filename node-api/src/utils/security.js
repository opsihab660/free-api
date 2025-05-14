/**
 * Security utilities for authentication and authorization
 */

const bcrypt = require('bcrypt');
const crypto = require('crypto');
const { v4: uuidv4 } = require('uuid');

/**
 * Hash a password for storing
 * @param {string} password - Plain text password
 * @returns {Promise<string>} Hashed password
 */
async function hashPassword(password) {
  const saltRounds = 10;
  return await bcrypt.hash(password, saltRounds);
}

/**
 * Verify a stored password against one provided by user
 * @param {string} storedPassword - Stored hashed password
 * @param {string} providedPassword - Plain text password to verify
 * @returns {Promise<boolean>} True if password matches, false otherwise
 */
async function verifyPassword(storedPassword, providedPassword) {
  try {
    return await bcrypt.compare(providedPassword, storedPassword);
  } catch (error) {
    console.error(`Password verification error: ${error.message}`);
    return false;
  }
}

/**
 * Generate a unique API key for a user
 * @param {string} prefix - Optional prefix for the key (default: "user_key")
 * @returns {string} A unique API key string
 */
function generateApiKey(prefix = 'user_key') {
  // Format: {prefix}_{random_string}
  const randomPart = crypto.randomBytes(18).toString('base64').replace(/[+/=]/g, '');
  return `${prefix}_${randomPart}`;
}

/**
 * Generate a unique user ID
 * @returns {string} A unique user ID
 */
function generateUserId() {
  return uuidv4();
}

/**
 * Get current timestamp in ISO format with timezone
 * @returns {string} Current timestamp in ISO format
 */
function getCurrentTimestamp() {
  return new Date().toISOString();
}

module.exports = {
  hashPassword,
  verifyPassword,
  generateApiKey,
  generateUserId,
  getCurrentTimestamp
};
