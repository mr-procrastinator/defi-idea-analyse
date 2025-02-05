# DeFi Opinions Dashboard

A React application that displays and updates DeFi opinions in real-time using AWS DynamoDB and SNS.

## Features

- Real-time display of DeFi opinions from DynamoDB
- Live updates through SNS notifications
- Responsive design for all screen sizes
- Error handling and loading states

## Setup

1. Clone the repository
2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the root directory with the following variables:
```env
REACT_APP_AWS_REGION=eu-central-1
REACT_APP_AWS_ACCESS_KEY_ID=your_access_key
REACT_APP_AWS_SECRET_ACCESS_KEY=your_secret_key
REACT_APP_SNS_TOPIC_ARN=arn:aws:sns:eu-central-1:035586480742:defi-opinions-topic
```

4. Start the development server:
```bash
npm start
```

## Environment Variables

- `REACT_APP_AWS_REGION`: AWS region where your services are located
- `REACT_APP_AWS_ACCESS_KEY_ID`: AWS access key with permissions for DynamoDB and SNS
- `REACT_APP_AWS_SECRET_ACCESS_KEY`: AWS secret key
- `REACT_APP_SNS_TOPIC_ARN`: ARN of the SNS topic for real-time updates

## AWS Services Used

- **DynamoDB**: Stores the opinions data
- **SNS**: Handles real-time updates when new opinions are added

## Development

The app is built using:
- React 18
- AWS SDK v3
- AWS Amplify
- Server-Sent Events for real-time updates

## Project Structure

```
src/
  ├── App.js           # Main application component
  ├── App.css          # Styles for the application
  ├── index.js         # Application entry point
  └── config.js        # AWS configuration
```

## Security Considerations

- In a production environment, implement proper AWS credentials management
- Consider using AWS Cognito for user authentication
- Implement proper CORS and security headers
- Use environment variables for sensitive information

## License

MIT