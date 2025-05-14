/**
 * Helper functions for the application
 */

const { generateUserId, getCurrentTimestamp } = require('./security');

/**
 * Create a basic user entry with API key structure
 * @param {string} username - Username for the user
 * @param {string} apiKey - API key for the user
 * @param {boolean} active - Whether the user is active (default: true)
 * @param {number} quotaLeft - Quota left for the user (default: 500000)
 * @returns {Object} A dictionary with user data
 */
function createUserEntry(username, apiKey, active = true, quotaLeft = 500000) {
  const currentTime = getCurrentTimestamp();
  const userId = generateUserId();

  return {
    username,
    active,
    quota_left: quotaLeft,
    user_id: userId,
    api_key: {
      key: apiKey,
      name: 'Default API Key',
      created_at: currentTime,
      last_used: null,
      active
    },
    account_created_at: currentTime,
    request_count: 0,
    total_input_tokens: 0,
    total_output_tokens: 0,
    total_cost: 0.0,
    model_usage: {}
  };
}

/**
 * Custom JSON replacer that handles Decimal values
 * @param {string} key - Object key
 * @param {any} value - Value to stringify
 * @returns {any} Processed value
 */
function decimalJsonReplacer(key, value) {
  // Handle Decimal128 from MongoDB
  if (value && value.constructor && value.constructor.name === 'Decimal128') {
    return parseFloat(value.toString());
  }
  return value;
}

/**
 * Safely parse JSON with decimal support
 * @param {string} jsonString - JSON string to parse
 * @returns {Object} Parsed object
 */
function safeJsonParse(jsonString) {
  try {
    return JSON.parse(jsonString);
  } catch (error) {
    console.error(`Error parsing JSON: ${error.message}`);
    return null;
  }
}

module.exports = {
  createUserEntry,
  decimalJsonReplacer,
  safeJsonParse
};
