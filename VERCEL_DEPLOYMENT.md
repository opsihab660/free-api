# Deploying to Vercel

This guide explains how to deploy this FastAPI application to Vercel.

## Prerequisites

1. A Vercel account (sign up at [vercel.com](https://vercel.com))
2. Vercel CLI installed (optional, for local testing)
   ```
   npm install -g vercel
   ```

## Deployment Steps

### 1. Push Your Code to a Git Repository

Make sure your code is pushed to a Git repository (GitHub, GitLab, or Bitbucket).

### 2. Import Your Project in Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your Git repository
3. Configure your project:
   - Framework Preset: Other
   - Build Command: Leave empty (configured in vercel.json)
   - Output Directory: Leave empty (configured in vercel.json)
   - Install Command: `pip install -r requirements.txt`

### 3. Configure Environment Variables

Add the following environment variables in the Vercel dashboard:

- `MONGODB_URI`: Your MongoDB connection string
- `MONGODB_DB_NAME`: Your MongoDB database name
- `MONGODB_USER_COLLECTION`: Your MongoDB collection name
- `BACKEND_API_BASE_URL`: Your backend API base URL
- `MY_BACKEND_API_KEY`: Your backend API key

### 4. Deploy

Click "Deploy" and wait for the deployment to complete.

## Understanding the Vercel Configuration

The `vercel.json` file contains the configuration for deploying to Vercel:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "vercel_app.py",
      "use": "@vercel/python"
    }
  ],
  "rewrites": [
    { "source": "/docs", "destination": "/vercel_app.py" },
    { "source": "/redoc", "destination": "/vercel_app.py" },
    { "source": "/openapi.json", "destination": "/vercel_app.py" },
    { "source": "/v1/api/:path*", "destination": "/vercel_app.py" },
    { "source": "/auth/:path*", "destination": "/vercel_app.py" },
    { "source": "/admin/:path*", "destination": "/vercel_app.py" },
    { "source": "/(.*)", "destination": "/vercel_app.py" }
  ],
  "env": {
    "PYTHONUNBUFFERED": "1"
  }
}
```

This configuration:
1. Specifies that `vercel_app.py` is the entry point for the application
2. Sets up rewrites to route all requests to the FastAPI application
3. Configures environment variables

## Troubleshooting

If you encounter 404 errors:

1. Check the Vercel deployment logs for any errors
2. Ensure all routes are properly configured in the `vercel.json` file
3. Verify that the `vercel_app.py` file is correctly importing and exposing the FastAPI app
4. Make sure all required environment variables are set in the Vercel dashboard

## Local Testing with Vercel CLI

To test your deployment locally:

1. Install Vercel CLI: `npm install -g vercel`
2. Run `vercel dev` in your project directory
3. Access your application at the provided local URL

## Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vercel Python Runtime](https://vercel.com/docs/functions/runtimes/python)
