"""
Vercel deployment handler for FastAPI application
"""

from main import app

# This is the entry point for Vercel serverless function
# Vercel will look for a handler function
handler = app
