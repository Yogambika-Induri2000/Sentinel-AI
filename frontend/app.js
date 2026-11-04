const API_BASE = 'http://127.0.0.1:8000';
const responseBox = document.getElementById('responseBox');

function setResponse(message) {
  responseBox.textContent = message;
}

async function apiRequest(endpoint, payload) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || 'Request failed');
  }

  return data;
}

document.getElementById('vectorBtn').addEventListener('click', async () => {
  try {
    setResponse('Running vector search...');
    const query = document.getElementById('vectorQuery').value.trim();
    const result = await apiRequest('/api/v1/search/vector', { query });
    setResponse(JSON.stringify(result, null, 2));
  } catch (error) {
    setResponse(`Error: ${error.message}`);
  }
});

document.getElementById('sqlBtn').addEventListener('click', async () => {
  try {
    setResponse('Running SQL query...');
    const sql = document.getElementById('sqlQuery').value.trim();
    const result = await apiRequest('/api/v1/search/sql', { sql });
    setResponse(JSON.stringify(result, null, 2));
  } catch (error) {
    setResponse(`Error: ${error.message}`);
  }
});

document.getElementById('agentBtn').addEventListener('click', async () => {
  try {
    setResponse('Running agent query...');
    const prompt = document.getElementById('agentPrompt').value.trim();
    const openaiKey = document.getElementById('openaiKey').value.trim();

    if (!prompt) {
      throw new Error('Please enter a prompt for the agent.');
    }

    if (!openaiKey) {
      throw new Error('Please provide an OpenAI API key before running the agent query.');
    }

    const result = await apiRequest('/api/v1/agent/query', {
      prompt,
      openai_api_key: openaiKey
    });
    setResponse(JSON.stringify(result, null, 2));
  } catch (error) {
    setResponse(`Error: ${error.message}`);
  }
});
