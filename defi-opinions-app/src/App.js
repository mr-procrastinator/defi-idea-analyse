import React, { useEffect, useState } from 'react';
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, ScanCommand } from "@aws-sdk/lib-dynamodb";
import { AWS_CONFIG } from './config.js';
import './App.css';

// Initialize DynamoDB client with explicit credentials
const client = new DynamoDBClient({
  region: AWS_CONFIG.region,
  credentials: {
    accessKeyId: process.env.REACT_APP_AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.REACT_APP_AWS_SECRET_ACCESS_KEY,
  }
});

const ddbDocClient = DynamoDBDocumentClient.from(client);

// Helper function to format text with line breaks
const formatOpinionText = (text) => {
  return text.split('\n').map((line, i) => (
    <React.Fragment key={i}>
      {line}
      <br />
    </React.Fragment>
  ));
};

function App() {
  const [opinions, setOpinions] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);

  const fetchOpinions = async () => {
    try {
      const result = await ddbDocClient.send(new ScanCommand({
        TableName: "defi_ideas"
      }));

      // Transform array of items into object with opinionId as key
      const opinionsMap = {};
      if (result.Items) {
        result.Items.forEach(item => {
          opinionsMap[item.opinionId] = item.opinions || [];
        });
      }

      setOpinions(opinionsMap);
      setError(null);
    } catch (err) {
      console.error('Error fetching opinions:', err);
      setError('Failed to load opinions. Please check AWS credentials and permissions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOpinions();

    // Connect to WebSocket server
    const ws = new WebSocket('ws://localhost:8080');

    ws.onopen = () => {
      console.log('Connected to WebSocket server');
      setWsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Received new data:', data);
        if (data.opinionId) {
          console.log('Received new opinion:', data);
          fetchOpinions();
        }
      } catch (err) {
        console.error('Error processing WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsConnected(false);
    };

    ws.onclose = () => {
      console.log('Disconnected from WebSocket server');
      setWsConnected(false);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  if (loading) {
    return (
      <div className="App">
        <div className="loading">Loading opinions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="App">
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  // Sort opinion IDs in reverse order
  const sortedOpinionIds = Object.keys(opinions).sort((a, b) => b.localeCompare(a));

  return (
    <div className="App">
      <h1>DeFi Opinions Dashboard</h1>
      <div className="connection-status">
        {wsConnected ? (
          <span className="status connected">Live updates enabled</span>
        ) : (
          <span className="status disconnected">Live updates disconnected</span>
        )}
      </div>
      <div className="opinions-list">
        {sortedOpinionIds.map(opinionId => (
          <div key={opinionId} className="opinion-item">
            <h3>Opinion ID: {opinionId}</h3>
            <ul>
              {/* Display opinions in reverse order with preserved formatting */}
              {[...opinions[opinionId]].reverse().map((opinion, index) => (
                <li key={`${opinionId}-${index}`} className="opinion-text">
                  {formatOpinionText(opinion)}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;