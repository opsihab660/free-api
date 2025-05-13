# API Service with MongoDB Integration

This project is an API service that provides OpenAI-compatible endpoints with user management and usage tracking. Data is stored in MongoDB for persistence.

## Setup Instructions

### 1. Environment Configuration

The application uses environment variables for configuration. You can set these in a `.env` file in the root directory.

Example `.env` file:
```
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB_NAME=api_service_db
MONGODB_USER_COLLECTION=users

# API Service Configuration
LOCAL_SERVER_PORT=8002
BACKEND_API_BASE_URL=https://api.devsdocode.com/v1
MY_BACKEND_API_KEY=your-backend-api-key
```

### 2. MongoDB Setup Options

#### Option A: Local MongoDB Installation

1. Download and install MongoDB Community Edition from: https://www.mongodb.com/try/download/community
2. Start the MongoDB service
3. No changes needed to the default `.env` configuration

#### Option B: MongoDB Atlas (Cloud Service)

1. Create a free account at MongoDB Atlas: https://www.mongodb.com/cloud/atlas/register
2. Create a new cluster (the free tier is sufficient)
3. Set up a database user with password
4. Add your IP address to the IP access list
5. Get your connection string and update the `.env` file:
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   ```

### 3. Install Dependencies

```bash
pip install fastapi uvicorn pymongo python-dotenv
```

### 4. Run the Application

```bash
python main.py
```

The application will:
1. Connect to MongoDB using the configured URI
2. Load existing users from MongoDB
3. Store all user data and usage statistics in MongoDB

## Project Structure

The project follows a modern modular structure:

```
app/
├── api/            # API endpoints
├── auth/           # Authentication routes and models
├── config/         # Configuration and settings
├── db/             # Database operations
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

## MongoDB Integration

The application uses MongoDB for all data storage:

1. **User Management**: All user data including credentials, API keys, and profiles
2. **Usage Tracking**: Request counts, token usage, and costs
3. **Model Usage Statistics**: Per-model usage statistics

## Troubleshooting

- If you encounter connection issues with MongoDB, check that:
  - Your connection string is correct (for MongoDB Atlas)
  - Your IP address is in the access list (for MongoDB Atlas)
  - Your username and password are correct (for MongoDB Atlas)
  - Network connectivity to MongoDB Atlas is available

- If you see "MongoDB connection failed" in the logs, the application will not be able to store or retrieve data.
## Deployment on Render

This application can be easily deployed on Render.com:

### Option 1: Manual Deployment

1. Create a new Web Service on Render
2. Connect your GitHub/GitLab/Bitbucket repository
3. Configure the following settings:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add the following environment variables:
   - `MONGODB_URI`: Your MongoDB connection string
   - `MONGODB_DB_NAME`: Your MongoDB database name
   - `MONGODB_USER_COLLECTION`: Your MongoDB collection name
   - `BACKEND_API_BASE_URL`: Your backend API base URL
   - `MY_BACKEND_API_KEY`: Your backend API key

### Option 2: Using render.yaml (Infrastructure as Code)

1. Make sure the `render.yaml` file is in your repository
2. Go to the Render Dashboard and click "Blueprint" to create a new Blueprint Instance
3. Connect your repository
4. Render will automatically detect the `render.yaml` file and create the services
5. You'll need to manually set the secret environment variables:
   - `MONGODB_URI`: Your MongoDB connection string
   - `MY_BACKEND_API_KEY`: Your backend API key

### Important Notes for Render Deployment

- Render automatically sets the `PORT` environment variable, which the application uses
- The application is configured to listen on all interfaces (`0.0.0.0`) when deployed
- For MongoDB Atlas, make sure to add Render's IP addresses to your MongoDB Atlas IP access list
- You can find Render's IP addresses in their documentation: https://render.com/docs/static-outbound-ip-addresses
