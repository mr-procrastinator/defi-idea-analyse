import { SNSClient, SubscribeCommand } from "@aws-sdk/client-sns";
import { WebSocketServer } from 'ws';
import dotenv from 'dotenv';
import http from 'http';
import fetch from 'node-fetch';

// Load environment variables
dotenv.config({ path: '../.env' });

const PORT = 8080;
const SNS_TOPIC_ARN = process.env.REACT_APP_SNS_TOPIC_ARN;

// Initialize SNS client
const snsClient = new SNSClient({
  region: process.env.REACT_APP_AWS_REGION,
  credentials: {
    accessKeyId: process.env.REACT_APP_AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.REACT_APP_AWS_SECRET_ACCESS_KEY,
  }
});

// Create HTTP server
const server = http.createServer();

// Create WebSocket server
const wss = new WebSocketServer({ server });

// Store connected clients
const clients = new Set();

// Handle WebSocket connections
wss.on('connection', (ws) => {
  console.log('Client connected');
  clients.add(ws);

  ws.on('close', () => {
    console.log('Client disconnected');
    clients.delete(ws);
  });

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
});

// Handle SNS messages
const handleSNSMessage = async (message) => {
  try {
    // Replace single quotes with double quotes for valid JSON
    const formattedMessage = message.replace(/'/g, '"');
    const parsedMessage = JSON.parse(formattedMessage);
    
    // Broadcast message to all connected clients
    const messageStr = JSON.stringify(parsedMessage);
    console.log('Broadcasting message:', messageStr);
    console.log('Clients len:', clients.size);
    clients.forEach((client) => {
      //if (client.readyState === WebSocketServer.OPEN) {
        console.log('Sending message to client ', client.readyState);
        client.send(messageStr);
      //}
    });
  } catch (error) {
    console.error('Error handling SNS message:', error);
  }
};

// Create HTTP endpoint for SNS
server.on('request', async (req, res) => {
  if (req.method === 'POST' && req.url === '/sns') {
    let body = '';
    
    req.on('data', (chunk) => {
      body += chunk;
    });

    req.on('end', async () => {
      try {
        const message = JSON.parse(body);
        console.log('Received message:', message);
        // Handle SNS subscription confirmation
        if (message.Type === 'SubscriptionConfirmation') {
          console.log('Received subscription confirmation. Confirming subscription...');
          try {
            const response = await fetch(message.SubscribeURL);
            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
            console.log('Successfully confirmed SNS subscription');
          } catch (error) {
            console.error('Error confirming subscription:', error);
          }
          res.writeHead(200);
          res.end('Subscription confirmed');
          return;
        }

        // Handle SNS message
        if (message.Type === 'Notification') {
          handleSNSMessage(message.Message);
        }

        res.writeHead(200);
        res.end('Message processed');
      } catch (error) {
        console.error('Error processing SNS message:', error);
        res.writeHead(400);
        res.end('Error processing message');
      }
    });
  } else {
    res.writeHead(404);
    res.end();
  }
});

// Subscribe to SNS topic
const subscribeToSNS = async () => {
  try {
    const subscribeCommand = new SubscribeCommand({
      TopicArn: SNS_TOPIC_ARN,
      Protocol: 'https', 
      Endpoint: process.env.REACT_APP_AWS_REGION, // Your server's endpoint to receive SNS messages
    });

    const response = await snsClient.send(subscribeCommand);
    console.log('Successfully subscribed to SNS topic:', response.SubscriptionArn);
  } catch (error) {
    console.error('Error subscribing to SNS topic:', error);
  }
};

// Start server
server.listen(PORT, () => {
  console.log(`WebSocket server is running on port ${PORT}`);
  subscribeToSNS();
});

// Handle shutdown
process.on('SIGINT', () => {
  wss.close(() => {
    console.log('WebSocket server closed');
    process.exit(0);
  });
});
