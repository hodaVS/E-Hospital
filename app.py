from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from openai import OpenAI
import json


# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes



# Function to chat with GPT
def chat_with_gpt(prompt, messages, model="gpt-4"):
    messages.append({"role": "user", "content": prompt})

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=5000,
        temperature=0
    )
    gpt_response = completion.choices[0].message.content.strip()

    messages.append({"role": "assistant", "content": gpt_response})

    return gpt_response

conversation_history = [
    {
        "role": "system",
        "content": "You are a helpful assistant that generates prescriptions. Always return the prescription in the following JSON format: (Warn doctor in Description if you suspect any drug conflicts). If any information is missing, use 'None' as the value for that field."
                   "{ "
                   "\"Prescriptions\": [ "
                   "{ "
                   "\"DiagnosisInformation\": { \"Diagnosis\": \"<diagnosis>\", \"Medicine\": \"<medicine>\" }, "
                   "\"MedicationDetails\": { "
                   "\"Dose\": \"<dose>\", "
                   "\"DoseUnit\": \"<dose unit>\", "
                   "\"DoseRoute\": \"<dose route>\", "
                   "\"Frequency\": \"<frequency>\", "
                   "\"FrequencyDuration\": \"<frequency duration>\", "
                   "\"FrequencyUnit\": \"<frequency unit>\", "
                   "\"Quantity\": \"<quantity>\", "
                   "\"QuantityUnit\": \"<quantity unit>\", "
                   "\"Refill\": \"<refill>\", "
                   "\"Pharmacy\": \"<pharmacy>\" "
                   "}, "
                   "\"Description\": \"<description>\" "
                   "} ] "
                   "}"
    }
]

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('text')
    if not user_input:
        return jsonify({"error": "No text provided"}), 400

    try:
        # Define a system message to instruct OpenAI to return structured JSON
        system_message = {
            "role": "system",
            "content": "You are a helpful assistant that generates prescriptions. Always return the prescription in the following JSON format: (Warn doctor in Description if you suspect any drug conflicts). If any information is missing, use 'None' as the value for that field."
                       "{ "
                       "\"Prescriptions\": [ "
                       "{ "
                       "\"DiagnosisInformation\": { \"Diagnosis\": \"<diagnosis>\", \"Medicine\": \"<medicine>\" }, "
                       "\"MedicationDetails\": { "
                       "\"Dose\": \"<dose>\", "
                       "\"DoseUnit\": \"<dose unit>\", "
                       "\"DoseRoute\": \"<dose route>\", "
                       "\"Frequency\": \"<frequency>\", "
                       "\"FrequencyDuration\": \"<frequency duration>\", "
                       "\"FrequencyUnit\": \"<frequency unit>\", "
                       "\"Quantity\": \"<quantity>\", "
                       "\"QuantityUnit\": \"<quantity unit>\", "
                       "\"Refill\": \"<refill>\", "
                       "\"Pharmacy\": \"<pharmacy>\" "
                       "}, "
                       "\"Description\": \"<description>\" "
                       "} ] "
                       "}"
        }

        # Send the user input to OpenAI
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[system_message, {"role": "user", "content": user_input}],
            max_tokens=500,  # Increased token limit
            temperature=0.1
        )

        # Extract the response from OpenAI
        gpt_response = completion.choices[0].message.content.strip()
        print("OpenAI Response:", gpt_response)  # Log the OpenAI response

        # Fix malformed JSON (e.g., replace hyphens in numeric fields with strings)
        gpt_response = gpt_response.replace('1-2', '"1-2"')  # Example fix for "1-2"

        # Check if the response is a complete JSON object
        if not gpt_response.strip().endswith("}"):
            print("OpenAI response is incomplete. Returning default response.")
            return jsonify({
                "response": {
                    "Prescriptions": [
                        {
                            "DiagnosisInformation": {"Diagnosis": None, "Medicine": None},
                            "MedicationDetails": {
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
                            },
                            "Description": "Please try again with proper prescription content."
                        }
                    ]
                }
            })

        # Parse the response into a JSON object
        try:
            prescription = json.loads(gpt_response)

            # Ensure all fields are present, filling in 'None' for missing fields
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
        except json.JSONDecodeError as e:
            print("Failed to parse OpenAI response as JSON. Returning default response.")
            return jsonify({
                "response": {
                    "Prescriptions": [
                        {
                            "DiagnosisInformation": {"Diagnosis": None, "Medicine": None},
                            "MedicationDetails": {
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
                            },
                            "Description": "Please try again with proper prescription content."
                        }
                    ]
                }
            })

    except Exception as e:
        print("Error in /chat endpoint. Returning default response.")
        return jsonify({
            "response": {
                "Prescriptions": [
                    {
                        "DiagnosisInformation": {"Diagnosis": None, "Medicine": None},
                        "MedicationDetails": {
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
                        },
                        "Description": "Please try again with proper prescription content."
                    }
                ]
            }
        })





if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
