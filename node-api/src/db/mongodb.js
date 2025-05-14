/**
 * MongoDB client module for handling database operations.
 * This module provides functions to connect to MongoDB and perform CRUD operations.
 */

const mongoose = require('mongoose');
const config = require('../config/settings');

// Global MongoDB client
let client = null;
let db = null;

/**
 * Connect to MongoDB and initialize collections
 * @returns {Promise<boolean>} True if connection successful, false otherwise
 */
async function connectToMongoDB() {
  try {
    // Create MongoDB connection
    await mongoose.connect(config.MONGODB_URI, {
      dbName: config.MONGODB_DB_NAME
    });

    // Store the connection
    client = mongoose.connection.getClient();
    db = mongoose.connection.db;

    console.log(`Connected to MongoDB at ${config.MONGODB_URI}, database: ${config.MONGODB_DB_NAME}`);
    return true;
  } catch (error) {
    console.error(`Failed to connect to MongoDB: ${error.message}`);
    return false;
  }
}

/**
 * Close the MongoDB connection
 */
async function closeMongoDB() {
  if (mongoose.connection.readyState !== 0) {
    await mongoose.connection.close();
    console.log('MongoDB connection closed');
  }
}

/**
 * Convert Decimal128 to regular numbers for JavaScript
 * @param {Object} doc - MongoDB document
 * @returns {Object} Document with Decimal128 converted to numbers
 */
function decimal128ToNumber(doc) {
  if (!doc) return doc;
  
  const result = { ...doc };
  
  for (const key in result) {
    if (result[key] && typeof result[key] === 'object') {
      if (result[key]._bsontype === 'Decimal128') {
        result[key] = parseFloat(result[key].toString());
      } else {
        result[key] = decimal128ToNumber(result[key]);
      }
    }
  }
  
  return result;
}

/**
 * Convert JavaScript numbers to MongoDB Decimal128
 * @param {Object} doc - Document with numbers
 * @returns {Object} Document with numbers converted to Decimal128
 */
function numberToDecimal128(doc) {
  if (!doc) return doc;
  
  const result = { ...doc };
  
  for (const key in result) {
    if (result[key] !== null && typeof result[key] === 'object') {
      result[key] = numberToDecimal128(result[key]);
    } else if (typeof result[key] === 'number') {
      // In Mongoose, we'll use the schema to handle this conversion
      // This function is kept for compatibility with the Python version
      result[key] = result[key];
    }
  }
  
  return result;
}

module.exports = {
  connectToMongoDB,
  closeMongoDB,
  decimal128ToNumber,
  numberToDecimal128
};
