/**
 * User repository for database operations
 */

const User = require('./models/User');
const { decimal128ToNumber } = require('./mongodb');

/**
 * Load all users from MongoDB and format them for the application
 * @returns {Promise<Object>} Dictionary of users with keys as API keys or access tokens
 */
async function loadAllUsers() {
  try {
    const users = await User.find({}).lean();
    const usersDict = {};

    for (const user of users) {
      // Remove MongoDB _id field
      delete user._id;
      
      // Convert Decimal128 to regular numbers
      const processedUser = decimal128ToNumber(user);

      // Use API key as the dictionary key if available
      if (processedUser.api_key && processedUser.api_key.key) {
        usersDict[processedUser.api_key.key] = processedUser;
      }

      // Also add access token as a key if available
      if (processedUser.access_token) {
        usersDict[processedUser.access_token] = processedUser;
      }
    }

    console.log(`Loaded ${Object.keys(usersDict).length} users from MongoDB`);
    return usersDict;
  } catch (error) {
    console.error(`Error loading users from MongoDB: ${error.message}`);
    return {};
  }
}

/**
 * Save all users to MongoDB
 * @param {Object} usersDict - Dictionary of users
 * @returns {Promise<boolean>} True if successful, false otherwise
 */
async function saveUsers(usersDict) {
  try {
    let updateCount = 0;
    let insertCount = 0;

    for (const [key, userData] of Object.entries(usersDict)) {
      // Make a copy to avoid modifying the original
      const userDoc = { ...userData };

      // Determine if this is an API key or access token
      let query = {};
      
      if (userDoc.api_key && key === userDoc.api_key.key) {
        // This is an API key
        query = { 'api_key.key': key };
      } else {
        // This is an access token
        userDoc.access_token = key;
        query = { access_token: key };
      }

      // Check if user exists
      const existingUser = await User.findOne(query).lean();

      if (existingUser) {
        // Update existing user
        await User.updateOne(query, userDoc);
        updateCount++;
      } else {
        // Insert new user
        await User.create(userDoc);
        insertCount++;
      }
    }

    console.log(`Saved users to MongoDB: ${updateCount} updated, ${insertCount} inserted`);
    return true;
  } catch (error) {
    console.error(`Error saving users to MongoDB: ${error.message}`);
    return false;
  }
}

/**
 * Update a specific user in MongoDB
 * @param {string} userKey - API key or access token
 * @param {Object} userData - User data to update
 * @returns {Promise<boolean>} True if successful, false otherwise
 */
async function updateUser(userKey, userData) {
  try {
    // Determine if this is an API key or access token
    let query = {};
    
    if (userData.api_key && userKey === userData.api_key.key) {
      // This is an API key
      query = { 'api_key.key': userKey };
    } else {
      // This is an access token
      userData.access_token = userKey;
      query = { access_token: userKey };
    }

    // Update or insert the user
    await User.updateOne(query, userData, { upsert: true });
    
    console.log(`Updated user with key ending in ...${userKey.slice(-4)}`);
    return true;
  } catch (error) {
    console.error(`Error updating user in MongoDB: ${error.message}`);
    return false;
  }
}

/**
 * Get a user by username
 * @param {string} username - Username to search for
 * @returns {Promise<Object|null>} User object or null if not found
 */
async function getUserByUsername(username) {
  try {
    const user = await User.findOne({ username }).lean();
    
    if (user) {
      delete user._id;
      return decimal128ToNumber(user);
    }
    
    return null;
  } catch (error) {
    console.error(`Error getting user by username: ${error.message}`);
    return null;
  }
}

/**
 * Get a user by API key
 * @param {string} apiKey - API key to search for
 * @returns {Promise<Object|null>} User object or null if not found
 */
async function getUserByApiKey(apiKey) {
  try {
    const user = await User.findOne({ 'api_key.key': apiKey }).lean();
    
    if (user) {
      delete user._id;
      return decimal128ToNumber(user);
    }
    
    return null;
  } catch (error) {
    console.error(`Error getting user by API key: ${error.message}`);
    return null;
  }
}

/**
 * Get a user by access token
 * @param {string} accessToken - Access token to search for
 * @returns {Promise<Object|null>} User object or null if not found
 */
async function getUserByAccessToken(accessToken) {
  try {
    const user = await User.findOne({ access_token: accessToken }).lean();
    
    if (user) {
      delete user._id;
      return decimal128ToNumber(user);
    }
    
    return null;
  } catch (error) {
    console.error(`Error getting user by access token: ${error.message}`);
    return null;
  }
}

module.exports = {
  loadAllUsers,
  saveUsers,
  updateUser,
  getUserByUsername,
  getUserByApiKey,
  getUserByAccessToken
};
