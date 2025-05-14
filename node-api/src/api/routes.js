/**
 * API routes for OpenAI-compatible endpoints
 * @swagger
 * tags:
 *   name: API
 *   description: OpenAI-compatible API endpoints
 *
 * components:
 *   schemas:
 *     ChatCompletionRequest:
 *       type: object
 *       required:
 *         - model
 *         - messages
 *       properties:
 *         model:
 *           type: string
 *           description: ID of the model to use
 *           example: gpt-3.5-turbo
 *         messages:
 *           type: array
 *           description: A list of messages comprising the conversation so far
 *           items:
 *             type: object
 *             required:
 *               - role
 *               - content
 *             properties:
 *               role:
 *                 type: string
 *                 enum: [system, user, assistant, function]
 *                 description: The role of the message author
 *               content:
 *                 type: string
 *                 description: The content of the message
 *         temperature:
 *           type: number
 *           description: Sampling temperature between 0 and 2
 *           default: 1
 *         top_p:
 *           type: number
 *           description: Nucleus sampling parameter
 *           default: 1
 *         n:
 *           type: integer
 *           description: Number of chat completion choices to generate
 *           default: 1
 *         stream:
 *           type: boolean
 *           description: Whether to stream the response
 *           default: false
 *         max_tokens:
 *           type: integer
 *           description: Maximum number of tokens to generate
 *         presence_penalty:
 *           type: number
 *           description: Presence penalty parameter
 *           default: 0
 *         frequency_penalty:
 *           type: number
 *           description: Frequency penalty parameter
 *           default: 0
 */

const express = require('express');
const router = express.Router();
const asyncHandler = require('express-async-handler');
const { authenticateUserViaBearer } = require('../auth/routes');
const { updateUser } = require('../db/userRepository');
const {
  YOUR_BACKEND_API_KEY,
  BACKEND_API_BASE_URL,
  MODEL_NAME_MAPPING,
  MODEL_COSTS
} = require('../config/settings');
const { decimalJsonReplacer } = require('../utils/helpers');

// Global OpenAI client
let backendOpenaiClient = null;

/**
 * Set the backend client
 * @param {Object} client - OpenAI client
 */
function setBackendClient(client) {
  backendOpenaiClient = client;
}

/**
 * Proxy OpenAI chat completions API
 * @swagger
 * /v1/api/chat/completions:
 *   post:
 *     summary: Create a chat completion
 *     description: Creates a completion for the chat message
 *     tags: [API]
 *     security:
 *       - BearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/ChatCompletionRequest'
 *     responses:
 *       200:
 *         description: Successful response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 id:
 *                   type: string
 *                   description: Unique identifier for the completion
 *                 object:
 *                   type: string
 *                   description: Object type, always "chat.completion"
 *                 created:
 *                   type: integer
 *                   description: Unix timestamp of when the completion was created
 *                 model:
 *                   type: string
 *                   description: Model used for the completion
 *                 choices:
 *                   type: array
 *                   description: List of completion choices
 *                   items:
 *                     type: object
 *                     properties:
 *                       index:
 *                         type: integer
 *                       message:
 *                         type: object
 *                         properties:
 *                           role:
 *                             type: string
 *                             enum: [assistant]
 *                           content:
 *                             type: string
 *                       finish_reason:
 *                         type: string
 *                         enum: [stop, length, function_call, content_filter]
 *                 usage:
 *                   type: object
 *                   properties:
 *                     prompt_tokens:
 *                       type: integer
 *                     completion_tokens:
 *                       type: integer
 *                     total_tokens:
 *                       type: integer
 *       401:
 *         description: Unauthorized
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       429:
 *         description: Rate limit or quota exceeded
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       500:
 *         description: Server error
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.post('/chat/completions', authenticateUserViaBearer, asyncHandler(async (req, res) => {
  if (!backendOpenaiClient) {
    return res.status(503).json({
      error: {
        message: 'Backend API client not initialized',
        type: 'server_error'
      }
    });
  }

  // Get user data from request
  const userData = req.userData;
  const username = userData.username || 'unknown';
  const userKey = req.userKey;

  try {
    // Parse request body
    const body = req.body;

    // Get model name from request
    const modelName = body.model || 'gpt-3.5-turbo';

    // Map model name if needed
    const originalModelNameForStats = modelName;
    if (MODEL_NAME_MAPPING[modelName]) {
      body.model = MODEL_NAME_MAPPING[modelName];
    }
    const modelNameFromPayload = body.model;

    // Check if streaming is requested
    const stream = body.stream || false;

    if (stream) {
      // Set up streaming response
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');

      // Create a stream from OpenAI
      const stream = await backendOpenaiClient.chat.completions.create({
        ...body,
        stream: true
      });

      // Process each chunk
      for await (const chunk of stream) {
        // Send the chunk as a server-sent event
        res.write(`data: ${JSON.stringify(chunk)}\n\n`);
      }

      // End the stream
      res.write('data: [DONE]\n\n');
      res.end();

      // Update user statistics
      // Note: For streaming responses, we don't have accurate token counts
      // In a real implementation, you would need to track this separately
      userData.request_count = (userData.request_count || 0) + 1;

      // Update model usage statistics
      if (!userData.model_usage) userData.model_usage = {};
      if (!userData.model_usage[originalModelNameForStats]) {
        userData.model_usage[originalModelNameForStats] = {
          request_count: 0,
          input_tokens: 0,
          output_tokens: 0,
          cost: 0
        };
      }

      userData.model_usage[originalModelNameForStats].request_count += 1;

      // Update in-memory store
      global.USER_API_KEYS_STORE[userKey] = userData;

      // Save to MongoDB
      await updateUser(userKey, userData);
    } else {
      // Handle non-streaming response
      const response = await backendOpenaiClient.chat.completions.create(body);

      // Calculate token usage and cost
      const usage = response.usage || {};
      const inputTokens = usage.prompt_tokens || 0;
      const outputTokens = usage.completion_tokens || 0;

      // Get model costs
      const modelCosts = MODEL_COSTS[originalModelNameForStats] ||
                         MODEL_COSTS[modelNameFromPayload] ||
                         MODEL_COSTS.default_model_for_costing;

      const inputCostPerToken = modelCosts.input_cost_per_token || 0;
      const outputCostPerToken = modelCosts.output_cost_per_token || 0;

      // Calculate cost
      const inputCost = inputTokens * inputCostPerToken;
      const outputCost = outputTokens * outputCostPerToken;
      const totalCost = inputCost + outputCost;

      // Update user statistics
      userData.request_count = (userData.request_count || 0) + 1;
      userData.total_input_tokens = (userData.total_input_tokens || 0) + inputTokens;
      userData.total_output_tokens = (userData.total_output_tokens || 0) + outputTokens;
      userData.total_cost = (userData.total_cost || 0) + totalCost;

      // Update quota
      if (userData.quota_left !== null && userData.quota_left !== undefined) {
        userData.quota_left -= (inputTokens + outputTokens);
        if (userData.quota_left < 0) userData.quota_left = 0;
      }

      // Update model usage statistics
      if (!userData.model_usage) userData.model_usage = {};
      if (!userData.model_usage[originalModelNameForStats]) {
        userData.model_usage[originalModelNameForStats] = {
          request_count: 0,
          input_tokens: 0,
          output_tokens: 0,
          cost: 0
        };
      }

      userData.model_usage[originalModelNameForStats].request_count += 1;
      userData.model_usage[originalModelNameForStats].input_tokens += inputTokens;
      userData.model_usage[originalModelNameForStats].output_tokens += outputTokens;
      userData.model_usage[originalModelNameForStats].cost += totalCost;

      // Update in-memory store
      global.USER_API_KEYS_STORE[userKey] = userData;

      // Save to MongoDB
      await updateUser(userKey, userData);

      // Send the response
      res.json(response);
    }
  } catch (error) {
    console.error(`Error proxying request: ${error.message}`);

    // Determine the appropriate status code
    let statusCode = 500;
    let errorMessage = 'Error proxying request';
    let errorType = 'server_error';

    if (error.name === 'AuthenticationError') {
      statusCode = 401;
      errorMessage = 'Backend API authentication error';
      errorType = 'authentication_error';
    } else if (error.name === 'APIError') {
      statusCode = 500;
      errorMessage = `Backend API error: ${error.message}`;
      errorType = 'api_error';
    }

    res.status(statusCode).json({
      error: {
        message: errorMessage,
        type: errorType,
        param: null,
        code: error.code
      }
    });
  }
}));

module.exports = router;
module.exports.setBackendClient = setBackendClient;
