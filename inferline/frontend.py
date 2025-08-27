import requests
from flask import Flask, render_template_string
from datetime import datetime
import os
from urllib.parse import quote, unquote

app = Flask(__name__)

# Get API backend URL from environment or default to localhost
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'https://inferline.cloudrift.ai')

def get_models():
    """Fetch models from the API backend"""
    try:
        response = requests.get(f"{API_BASE_URL}/models", timeout=10)
        response.raise_for_status()
        data = response.json()['data']
        return data
    except Exception as e:
        print(f"Error fetching models: {e}")
        print(f"API_BASE_URL: {API_BASE_URL}")
        return []

@app.route('/')
def home():
    """Frontend homepage showing available models"""
    models = get_models()
    
    # Create model cards HTML
    model_cards = ""
    for model in models:
        provider_name = getattr(model, 'provider_name', model.get('owned_by', 'unknown'))
        model_cards += f"""
        <div class="model-card">
            <h3>{model['id']}</h3>
            <p><strong>Provider:</strong> {provider_name}</p>
            <p><strong>Description:</strong> {model.get('description', 'No description available')}</p>
            <p><strong>Context Length:</strong> {model.get('context_length', 'Unknown'):,}</p>
            <a href="/model/{quote(model['id'], safe='')}" class="btn">View API Instructions</a>
        </div>
        """
    
    if not models:
        model_cards = "<p class='no-models'>No models currently available. Providers will register models when they connect.</p>"
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>InferLine API - Available Models</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 30px;
            }
            .header h1 {
                margin: 0;
                font-size: 2.5em;
            }
            .header p {
                margin: 10px 0 0 0;
                font-size: 1.2em;
                opacity: 0.9;
            }
            .models-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .model-card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .model-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
            }
            .model-card h3 {
                margin: 0 0 15px 0;
                color: #333;
                font-size: 1.4em;
            }
            .model-card p {
                margin: 8px 0;
                color: #666;
            }
            .btn {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 15px;
                transition: transform 0.2s;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
            .no-models {
                text-align: center;
                color: #666;
                font-style: italic;
                padding: 40px;
            }
            .footer {
                text-align: center;
                margin-top: 40px;
                padding: 20px;
                color: #666;
                border-top: 1px solid #ddd;
            }
            .api-links {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .api-links h3 {
                margin: 0 0 15px 0;
                color: #333;
            }
            .api-links a {
                display: inline-block;
                margin: 5px 10px 5px 0;
                padding: 8px 15px;
                background: #f8f9fa;
                color: #495057;
                text-decoration: none;
                border-radius: 5px;
                border: 1px solid #dee2e6;
            }
            .api-links a:hover {
                background: #e9ecef;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>InferLine API</h1>
            <p>OpenAI-compatible API server for LLM inference routing</p>
        </div>
        
        <div class="api-links">
            <h3>API Endpoints</h3>
            <a href="/api/docs" target="_blank">API Documentation</a>
            <a href="/api/models" target="_blank">Models JSON</a>
            <a href="/api/queue/stats" target="_blank">Queue Stats</a>
            <a href="/api/health" target="_blank">Health Check</a>
        </div>
        
        <h2>Available Models ({{ model_count }})</h2>
        <div class="models-grid">
            {{ model_cards|safe }}
        </div>
        
        <div class="footer">
            <p>InferLine API Server - Real-time model availability based on connected providers</p>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html_template, model_cards=model_cards, model_count=len(models))


@app.route('/model/<path:model_id>')
def model_detail(model_id):
    """Show detailed information and API usage instructions for a specific model"""
    # Decode the URL-encoded model ID
    decoded_model_id = unquote(model_id)
    models = get_models()
    
    # Debug: Print available models and the requested model ID
    import sys
    print(f"Requested model ID: '{decoded_model_id}'", file=sys.stderr)
    print(f"Available models: {[m['id'] for m in models]}", file=sys.stderr)

    model = next((m for m in models if m['id'] == decoded_model_id), None)
    if model is None:
        # More detailed error message for debugging
        return f"""
        <h1>Model Not Found</h1>
        <p>The requested model '{decoded_model_id}' is not currently available.</p>
        <p><strong>Available models:</strong></p>
        <ul>{''.join([f'<li>{m["id"]}</li>' for m in models])}</ul>
        <a href='/'>← Back to Models</a>
        """, 404
    
    provider_name = getattr(model, 'provider_name', model.get('owned_by', 'unknown'))
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>InferLine API - {{ model.id }}</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 30px;
            }
            .back-link {
                display: inline-block;
                color: white;
                text-decoration: none;
                margin-bottom: 10px;
                opacity: 0.9;
            }
            .back-link:hover {
                opacity: 1;
            }
            .model-info {
                background: white;
                padding: 25px;
                border-radius: 10px;
                margin-bottom: 25px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .code-block {
                background: #2d3748;
                color: #e2e8f0;
                padding: 20px;
                border-radius: 8px;
                overflow-x: auto;
                margin: 15px 0;
                font-family: 'Courier New', monospace;
            }
            .section {
                background: white;
                padding: 25px;
                border-radius: 10px;
                margin-bottom: 25px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .section h3 {
                margin: 0 0 20px 0;
                color: #333;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            .param-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }
            .param-table th, .param-table td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            .param-table th {
                background-color: #f8f9fa;
                font-weight: bold;
            }
            .highlight {
                background-color: #fff3cd;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #ffc107;
                margin: 15px 0;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <a href="/" class="back-link">← Back to Models</a>
            <h1>{{ decoded_model_id }}</h1>
            <p>API Usage Instructions</p>
        </div>
        
        <div class="model-info">
            <h3>Model Information</h3>
            <p><strong>Model ID:</strong> {{ decoded_model_id }}</p>
            <p><strong>Provider:</strong> {{ provider_name }}</p>
            <p><strong>Description:</strong> {{ model.description }}</p>
            <p><strong>Context Length:</strong> {{ "{:,}".format(model.context_length) }} tokens</p>
            <p><strong>Max Output Length:</strong> {{ "{:,}".format(model.max_output_length) }} tokens</p>
            <p><strong>Created:</strong> {{ created_date }}</p>
        </div>
        
        <div class="section">
            <h3>cURL Example</h3>
            <div class="code-block">curl -X POST "{{ base_url }}/api/completions" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "{{ decoded_model_id }}",
    "prompt": "Hello, how are you?",
    "max_tokens": 100,
    "temperature": 0.7
  }'</div>
        </div>
        
        <div class="section">
            <h3>Python Example</h3>
            <div class="code-block">import requests

url = "{{ base_url }}/api/completions"
headers = {"Content-Type": "application/json"}
data = {
    "model": "{{ decoded_model_id }}",
    "prompt": "Hello, how are you?",
    "max_tokens": 100,
    "temperature": 0.7
}

response = requests.post(url, headers=headers, json=data)
print(response.json())</div>
        </div>
        
        <div class="section">
            <h3>JavaScript Example</h3>
            <div class="code-block">const response = await fetch("{{ base_url }}/api/completions", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "{{ decoded_model_id }}",
    prompt: "Hello, how are you?",
    max_tokens: 100,
    temperature: 0.7
  })
});

const result = await response.json();
console.log(result);</div>
        </div>
        
        <div class="section">
            <h3>Request Parameters</h3>
            <table class="param-table">
                <tr>
                    <th>Parameter</th>
                    <th>Type</th>
                    <th>Required</th>
                    <th>Description</th>
                </tr>
                <tr>
                    <td>model</td>
                    <td>string</td>
                    <td>Yes</td>
                    <td>The model ID to use for completion</td>
                </tr>
                <tr>
                    <td>prompt</td>
                    <td>string</td>
                    <td>Yes</td>
                    <td>The text prompt to complete</td>
                </tr>
                <tr>
                    <td>max_tokens</td>
                    <td>integer</td>
                    <td>No</td>
                    <td>Maximum number of tokens to generate (default: 16)</td>
                </tr>
                <tr>
                    <td>temperature</td>
                    <td>float</td>
                    <td>No</td>
                    <td>Sampling temperature (0.0 to 2.0, default: 1.0)</td>
                </tr>
                <tr>
                    <td>top_p</td>
                    <td>float</td>
                    <td>No</td>
                    <td>Nucleus sampling parameter (default: 1.0)</td>
                </tr>
                <tr>
                    <td>stop</td>
                    <td>string or array</td>
                    <td>No</td>
                    <td>Stop sequences where generation should end</td>
                </tr>
            </table>
        </div>
        
        <div class="highlight">
            <strong>Note:</strong> This is a queued inference system. Requests may take some time to process depending on provider availability and queue status. Check <a href="/api/queue/stats" target="_blank">queue statistics</a> for current load.
        </div>
    </body>
    </html>
    """
    
    created_date = datetime.fromtimestamp(model.get('created', 0)).strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template_string(
        html_template,
        model=model,
        decoded_model_id=decoded_model_id,
        provider_name=provider_name,
        base_url=FRONTEND_BASE_URL,
        created_date=created_date
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)