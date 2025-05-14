/**
 * Authentication models
 */

const Joi = require('joi');

// User registration validation schema
const userRegisterSchema = Joi.object({
  username: Joi.string()
    .alphanum()
    .min(3)
    .max(50)
    .required()
    .messages({
      'string.alphanum': 'Username must be alphanumeric',
      'string.min': 'Username must be at least 3 characters long',
      'string.max': 'Username cannot exceed 50 characters',
      'any.required': 'Username is required'
    }),
  
  email: Joi.string()
    .email()
    .required()
    .messages({
      'string.email': 'Email must be a valid email address',
      'any.required': 'Email is required'
    }),
  
  password: Joi.string()
    .min(6)
    .required()
    .messages({
      'string.min': 'Password must be at least 6 characters long',
      'any.required': 'Password is required'
    }),
  
  full_name: Joi.string()
    .allow(null, '')
    .optional()
});

// User login validation schema
const userLoginSchema = Joi.object({
  username: Joi.string()
    .required()
    .messages({
      'any.required': 'Username is required'
    }),
  
  password: Joi.string()
    .required()
    .messages({
      'any.required': 'Password is required'
    })
});

// API key creation validation schema
const apiKeyCreateSchema = Joi.object({
  name: Joi.string()
    .min(1)
    .max(50)
    .required()
    .messages({
      'string.min': 'API key name must be at least 1 character long',
      'string.max': 'API key name cannot exceed 50 characters',
      'any.required': 'API key name is required'
    })
});

module.exports = {
  userRegisterSchema,
  userLoginSchema,
  apiKeyCreateSchema
};
