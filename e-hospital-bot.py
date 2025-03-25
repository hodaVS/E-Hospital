from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from openai import OpenAI
import json

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def chat_with_gpt(prompt, messages, model="gpt-4"):
    messages.append({"role": "user", "content": prompt})
    
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=5000,
        temperature=0
    )
    return completion.choices[0].message.content.strip()

# System message for prescription formatting
conversation_history = [
    {
        "role": "system",
        "content": """You are a helpful assistant that generates prescriptions. Always return the prescription in the following JSON format. 
        Warn doctor in Description if you suspect any drug conflicts. If any information is missing, use 'None' as the value.
        {
            "Prescriptions": [
                {
                    "DiagnosisInformation": { 
                        "Diagnosis": "<diagnosis>", 
                        "Medicine": "<medicine>" 
                    },
                    "MedicationDetails": {
                        "Dose": "<dose>",
                        "DoseUnit": "<dose unit>",
                        "DoseRoute": "<dose route>",
                        "Frequency": "<frequency>",
                        "FrequencyDuration": "<frequency duration>",
                        "FrequencyUnit": "<frequency unit>",
                        "Quantity": "<quantity>",
                        "QuantityUnit": "<quantity unit>",
                        "Refill": "<refill>",
                        "Pharmacy": "<pharmacy>"
                    },
                    "Description": "<description>"
                }
            ]
        }"""
    }
]

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('text')
    
    if not user_input:
        return jsonify({"error": "No text provided"}), 400

    try:
        # Get response from OpenAI
        gpt_response = chat_with_gpt(user_input, conversation_history)
        
        # Basic JSON validation
        try:
            prescription = json.loads(gpt_response)
            
            # Ensure all fields are present
            for p in prescription.get("Prescriptions", []):
                p.setdefault("DiagnosisInformation", {"Diagnosis": None, "Medicine": None})
                p.setdefault("MedicationDetails", {
                    "Dose": None,
                    "DoseUnit": None,
                    "DoseRoute": None,
                    "Frequency": None,
                    "FrequencyDuration": None,
                    "FrequencyUnit": None,
                    "Quantity": None,
                    "QuantityUnit": None,
                    "Refill": None,
                    "Pharmacy": None
                })
                p.setdefault("Description", None)
                
            return jsonify({"response": prescription})
            
        except json.JSONDecodeError:
            return jsonify({
                "error": "Failed to parse prescription",
                "response": gpt_response
            }), 400
            
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "An error occurred while processing your request"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)