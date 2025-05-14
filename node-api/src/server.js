/**
 * Main application entry point
 * @swagger
 * /:
 *   get:
 *     summary: Welcome endpoint
 *     description: Returns welcome message and API information
 *     responses:
 *       200:
 *         description: Welcome message with API version and docs URL
 */

const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const swaggerUi = require('swagger-ui-express');
const swaggerSpec = require('./config/swagger');
const { connectToMongoDB } = require('./db/mongodb');
const { loadAllUsers } = require('./db/userRepository');
const { setBackendClient } = require('./api/routes');
const { OpenAI } = require('openai');
const config = require('./config/settings');

// Import routes
const authRoutes = require('./auth/routes');
const apiRoutes = require('./api/routes');

// Create Express app
const app = express();

// Configure middleware
app.use(express.json());
app.use(cors());
app.use(morgan('dev'));

// Initialize global user store
global.USER_API_KEYS_STORE = {};

// Connect to MongoDB and initialize app
async function initializeApp() {
  try {
    // Connect to MongoDB
    const mongodbConnected = await connectToMongoDB();

    if (mongodbConnected) {
      console.log('MongoDB connection established successfully.');

      // Load user data from MongoDB
      const mongoUsers = await loadAllUsers();

      if (mongoUsers && Object.keys(mongoUsers).length > 0) {
        // Only update the in-memory store if it's empty or has fewer users
        if (!global.USER_API_KEYS_STORE || Object.keys(mongoUsers).length > Object.keys(global.USER_API_KEYS_STORE).length) {
          global.USER_API_KEYS_STORE = mongoUsers;
          console.log(`Loaded ${Object.keys(mongoUsers).length} users from MongoDB into in-memory store.`);
        } else {
          console.log(`In-memory store already has ${Object.keys(global.USER_API_KEYS_STORE).length} users. Not overwriting with ${Object.keys(mongoUsers).length} from MongoDB.`);
        }
      }
    } else {
      console.error('MongoDB connection failed. Application will not be able to store data.');
    }

    // Initialize OpenAI client
    if (config.YOUR_BACKEND_API_KEY) {
      const backendClient = new OpenAI({
        apiKey: config.YOUR_BACKEND_API_KEY,
        baseURL: config.BACKEND_API_BASE_URL
      });

      // Set the backend client in the API module
      setBackendClient(backendClient);
      console.log(`Startup: OpenAI backend client configured for ${config.BACKEND_API_BASE_URL}.`);
    } else {
      console.error('FATAL: MY_BACKEND_API_KEY not set. Backend client NOT initialized.');
    }

    // Register routes
    app.use('/auth', authRoutes);
    app.use('/v1/api', apiRoutes);

    // Swagger documentation
    app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec, {
      explorer: true,
      customCss: '.swagger-ui .topbar { display: none }',
      swaggerOptions: {
        docExpansion: 'list',
        filter: true,
        showRequestDuration: true,
      }
    }));

    // Root endpoint
    app.get('/', (req, res) => {
      res.json({
        message: 'Welcome to the API Service',
        version: '1.0.0',
        docs_url: '/docs'
      });
    });

    /**
     * @swagger
     * /admin/stats:
     *   get:
     *     summary: Get admin statistics
     *     description: Returns statistics about the API service
     *     tags: [Admin]
     *     responses:
     *       200:
     *         description: Admin statistics
     *         content:
     *           application/json:
     *             schema:
     *               type: object
     *               properties:
     *                 users_count:
     *                   type: integer
     *                   description: Number of registered users
     *                 message:
     *                   type: string
     *                   description: Status message
     */
    // Admin stats endpoint
    app.get('/admin/stats', (req, res) => {
      // If MongoDB is available, refresh the in-memory store first
      // This is a simplified version - in a real app, you'd want to authenticate this endpoint
      res.json({
        users_count: Object.keys(global.USER_API_KEYS_STORE).length,
        message: 'Admin stats endpoint'
      });
    });

    // Error handling middleware
    app.use((err, req, res, next) => {
      console.error(err.stack);
      res.status(500).json({
        error: {
          message: 'An internal server error occurred',
          detail: process.env.NODE_ENV === 'development' ? err.message : undefined
        }
      });
    });

    // Start the server
    const PORT = process.env.PORT || config.LOCAL_SERVER_PORT;
    app.listen(PORT, '0.0.0.0', () => {
      const localUrl = `http://127.0.0.1:${PORT}`;
      console.log(`Server running at ${localUrl}`);
      console.log(`OpenAI SDK Base URL: '${localUrl}/v1/api'`);

      // MongoDB connection info
      console.log(`MongoDB URI: '${config.MONGODB_URI.replace(/\/\/([^:]+):([^@]+)@/, '//***:***@')}'`);

      // Print API keys
      console.log('API Keys (Authorization: Bearer <key>):');
      for (const [key, data] of Object.entries(global.USER_API_KEYS_STORE)) {
        console.log(`  - Key: ${key.slice(0, 8)}... (User: ${data.username}, Active: ${data.active || true}, Quota: ${data.quota_left || 'N/A'})`);
      }

      if (!config.YOUR_BACKEND_API_KEY) {
        console.log('WARNING: MY_BACKEND_API_KEY is not set. Backend calls will fail.');
      }
    });
  } catch (error) {
    console.error('Failed to initialize application:', error);
    process.exit(1);
  }
}

// Initialize the application
initializeApp();

// Export app for testing
module.exports = app;
