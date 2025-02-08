from flask import Flask, request, jsonify
from flask_cors import CORS
from defillama import process_invest_idea

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({'error': 'Missing message field'}), 400
        
        analysis = process_invest_idea(data['message'])
        if analysis is None:
            return jsonify({'error': 'Failed to process investment idea'}), 500
            
        return jsonify({'analysis': analysis})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)