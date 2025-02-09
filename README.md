# Deffi analysing tool

![Project Architecture](assets/project-details.png)

A comprehensive system for monitoring and analyzing DeFi-related opinions from Telegram using AWS services and providing a real-time dashboard interface.

## Project Components

### Core Components

#### 1. defillama.py
The heart of DeFi strategy analysis with the following workflow:
1. **Strategy Analysis**: Analyzes investment ideas through structured output to determine:
   - Tokens involved
   - Smart contracts
   - Potential rewards
   - Risk assessment
   - Complexity level
   - Strategy characteristics
2. **Protocol Integration**: 
   - Fetches protocol data from DeFiLlama API
   - Identifies and analyzes related protocols
3. **Security Analysis**:
   - Evaluates Total Value Locked (TVL)
   - Reviews protocol audits
   - Provides links to social media (X.com)
4. **Report Generation**:
   - Combines all analyses into a comprehensive report
   - Provides detailed protocol insights
   - Includes security metrics and risk assessments

#### 2. telegram_scrapper.py
- Monitors specified Telegram channels for updates
- Captures DeFi-related messages and opinions
- Forwards messages for analysis and processing

#### 3. server.py
- Flask server implementation for the DeFiLlama analysis service
- Provides REST API endpoints for the frontend
- Handles analysis requests independently from the main application

#### 4. Lambda Components (lambda_function.py & tools.py)
- Contains AWS Lambda function implementations
- Integrates with OpenAPI schema for standardized API interactions
- Handles serverless processing of messages and analysis requests

### Project Structure

The project consists of two main components:

#### 1.Python Backend + Lambda functions + Telegram Scrapper + Defi ideas analiser
- Monitors the "@defi_opinion" Telegram channel
- Processes messages using AWS Bedrock for analysis
- Integrates with various AWS services (DynamoDB, SNS, Lambda)
- Logic for comperhansive analysis of defi ideas

#### 2. Dashboard (React Frontend)
- Real-time display of processed DeFi opinions
- WebSocket server for live updates
- Integration with AWS services for data retrieval

## Prerequisites

- Python 3.x
- Node.js and npm
- AWS Account with appropriate permissions
- Telegram API credentials

## Configuration

### Environment Variables

Create a `.env` file in the root directory with the following configurations:

```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=your_aws_region
AWS_BUCKET_NAME=your_bucket_name
AWS_ENDPOINT=your_endpoint
AWS_DYNAMODB_TABLE=your_dynamodb_table
AWS_LAMBDA_FUNCTION=your_lambda_function
TELEGRAM_API_KEY=your_telegram_api_key
TELEGRAM_API_HASH=your_telegram_api_hash
OPENROUTER_API_KEY=your_openrouter_key
TELEGRAM_BOT_TOKEN=your_bot_token
```

Create a separate `.env` file in the `defi-opinions-app` directory for frontend-specific configurations.

## Installation

### Backend Setup
1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Start the Telegram bot:
```bash
python telegram_scrapper.py
```
3. Upload lambda_function.py, tools.py, defillma.py together with dependices, setup AWS Bedrock agent with openapi-schema-v1.json to call lambda functions.

4. Optional: setup flask server to serve investments analys logic via API.

### Frontend Setup
1. Navigate to the frontend directory:
```bash
cd defi-opinions-app
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```
This command will start both the React application and the WebSocket server concurrently.

## Development

The frontend application runs on port 3000 by default. The WebSocket server handles real-time updates between the backend and frontend.

### Available Scripts

Backend:
- `python telegram_scrapper.py` - Start the Telegram bot
- `python server.py` - Start the DeFiLlama analysis service

Frontend:
- `npm run dev` - Start both the React app and WebSocket server


## AWS Services Used

- AWS Bedrock - For message processing and analysis
- DynamoDB - Data storage
- SNS - Notifications
- Lambda - Serverless functions

## License

This project is licensed under the MIT License - see the LICENSE file for details.