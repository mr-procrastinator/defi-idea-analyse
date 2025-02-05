export const AWS_CONFIG = {
  region: process.env.REACT_APP_AWS_REGION || 'eu-central-1',
  // We're setting credentials directly in App.js to avoid object extensibility issues
  apiVersion: 'latest'
};

// Check if required environment variables are set
if (!process.env.REACT_APP_AWS_ACCESS_KEY_ID || !process.env.REACT_APP_AWS_SECRET_ACCESS_KEY) {
  console.error('Missing required AWS credentials in environment variables');
}