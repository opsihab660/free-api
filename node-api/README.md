# API Service with MongoDB Integration (Node.js)

This project is a Node.js implementation of an API service that provides OpenAI-compatible endpoints with user management and usage tracking. Data is stored in MongoDB for persistence.

## Setup Instructions

### 1. Environment Configuration

The application uses environment variables for configuration. You can set these in a `.env` file in the root directory.

Copy the example environment file:
```bash
cp .env.example .env
```

Then edit the `.env` file with your specific configuration:
```
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB_NAME=api_service_db
MONGODB_USER_COLLECTION=users

# API Service Configuration
LOCAL_SERVER_PORT=8002
BACKEND_API_BASE_URL=https://api.devsdocode.com/v1
MY_BACKEND_API_KEY=your-backend-api-key

# Node.js Environment
NODE_ENV=development
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Run the Application

For development with auto-reload:
```bash
npm run dev
```

For production:
```bash
npm start
```

The application will:
1. Connect to MongoDB using the configured URI
2. Load existing users from MongoDB
3. Store all user data and usage statistics in MongoDB

## Project Structure

The project follows a modern modular structure:

```
src/
├── api/            # API endpoints
├── auth/           # Authentication routes and models
├── config/         # Configuration and settings
├── db/             # Database operations and models
└── utils/          # Utility functions
```

## API Endpoints

The service provides the following endpoints:

- `/v1/api/chat/completions` - OpenAI-compatible chat completions endpoint
- `/auth/register` - User registration
- `/auth/login` - User login
- `/auth/keys` - API key management
- `/auth/profile` - User profile information
- `/admin/stats` - Admin statistics view

### API Documentation

The API is documented using Swagger/OpenAPI. You can access the interactive documentation at:

```
http://localhost:8002/docs
```

This provides a user-friendly interface to:
- Explore all available endpoints
- View request/response schemas
- Test API calls directly from the browser
- Understand authentication requirements

## MongoDB Integration

The application uses MongoDB for all data storage:

1. **User Management**: All user data including credentials, API keys, and profiles
2. **Usage Tracking**: Request counts, token usage, and costs
3. **Model Usage Statistics**: Per-model usage statistics

## Authentication

The API uses bearer token authentication. To authenticate requests:

1. Register a user or login to get an access token
2. Create an API key for the user
3. Include the API key in the Authorization header:
   ```
   Authorization: Bearer your_api_key
   ```

## Development

### Running Tests

```bash
npm test
```

### Debugging

For detailed logging, set the `NODE_ENV` environment variable to `development`.

## Deployment

### Deploying to Render

1. Create a new Web Service on Render
2. Connect your GitHub/GitLab/Bitbucket repository
3. Configure the following settings:
   - **Environment**: Node
   - **Build Command**: `npm install`
   - **Start Command**: `npm start`
4. Add the environment variables from your `.env` file

### Deploying to Vercel

1. Install the Vercel CLI: `npm install -g vercel`
2. Run `vercel` in the project directory
3. Follow the prompts to deploy your application

## Troubleshooting

### MongoDB Connection Issues

- Ensure your MongoDB URI is correct
- Check that your IP address is whitelisted in MongoDB Atlas
- Verify that the database and collection names match your configuration

### API Key Authentication Issues

- Ensure you're using the correct format: `Bearer your_api_key`
- Check that the API key is active in your user profile
- Verify that your user account is active

## License

This project is licensed under the ISC License.
