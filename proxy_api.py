from flask import Flask, request, Response
import requests
import json

app = Flask(__name__)

# Configuration - you could also move this to a config file
TARGET_BASE_URL = "https://api.target-service.com"  # Replace with your target service URL

# Helper function to forward requests
def forward_request(method, path, headers=None, data=None, params=None):
    # Remove hop-by-hop headers that shouldn't be forwarded
    headers = headers.copy() if headers else {}
    excluded_headers = {
        'content-length', 'host', 'connection', 
        'keep-alive', 'proxy-authenticate', 
        'proxy-authorization', 'te', 'trailers', 
        'transfer-encoding', 'upgrade'
    }
    for header in excluded_headers:
        headers.pop(header, None)

    # Construct the target URL
    target_url = f"{TARGET_BASE_URL}/{path}"

    try:
        # Make the request to the target service
        response = requests.request(
            method=method,
            url=target_url,
            headers=headers,
            data=data if data else None,
            params=params if params else None,
            timeout=30  # Add timeout to prevent hanging
        )
        
        # Prepare the response to return to the client
        return Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )
    except requests.exceptions.RequestException as e:
        # Handle errors from the target service
        error_message = {"error": str(e)}
        return Response(
            json.dumps(error_message),
            status=500,
            mimetype='application/json'
        )

# Route handler for all methods
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    # Get the request method
    method = request.method.lower()
    
    # Get request components
    headers = dict(request.headers)
    data = request.get_data()
    params = request.args
    
    # Forward the request and return the response
    return forward_request(
        method=method,
        path=path,
        headers=headers,
        data=data,
        params=params
    )

# Handle root path
@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_root():
    return proxy('')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return Response(
        json.dumps({"error": "Not found"}),
        status=404,
        mimetype='application/json'
    )

@app.errorhandler(405)
def method_not_allowed(error):
    return Response(
        json.dumps({"error": "Method not allowed"}),
        status=405,
        mimetype='application/json'
    )

if __name__ == '__main__':
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True  # Set to False in production
    )
