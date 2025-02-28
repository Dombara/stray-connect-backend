from flask import Flask, request, jsonify, send_file
from flask_cors import CORS 
from pymongo import MongoClient
from gridfs import GridFS
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
from bson import ObjectId
import io

# MongoDB connection
MONGO_URI = "mongodb+srv://yash:yash@cluster0.jdcnv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.get_database('stray-db')
fs = GridFS(db)

# Load NLP Models
description_model = SentenceTransformer("all-MiniLM-L6-v2")
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Predefined categories for classification
categories = ["Lost Pet Report", "Adoption Inquiry", "Stray Animal Sighting", "Volunteering", "Medical Assistance"]

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Function to classify a report
def classify_report(description):
    try:
        result = classifier(description, categories)
        return result["labels"][0]  # Get the highest-confidence category
    except Exception as e:
        print(f"Error in classification: {str(e)}")
        return "Uncategorized"

# Function to compare descriptions and find the most similar report
def description_compare(description):
    try:
        print("Comparing description:", description)

        # Fetch all descriptions from the 'reports' collection
        reports = list(db.reports.find({}, {"description": 1}))
        descriptions = [doc["description"] for doc in reports if "description" in doc]

        # If no descriptions exist, return "No similar reports found."
        if not descriptions:
            print("No existing descriptions in the database.")
            return "No similar reports found."

        # Encode descriptions
        input_embedding = description_model.encode(description)
        existing_embeddings = description_model.encode(descriptions)

        # Compute similarity scores
        similarities = util.cos_sim(input_embedding, existing_embeddings)

        # Find the most similar description
        best_match_index = similarities.argmax().item()
        most_similar_description = descriptions[best_match_index]

        print(f"Most Similar Description: {most_similar_description}")
        return most_similar_description

    except Exception as e:
        print(f"Error in description_compare: {str(e)}")
        return "No similar reports found."

# Route to report a stray animal
@app.route('/report', methods=['POST'])
def report():
    try:
        location = request.form.get("location")
        description = request.form.get("description")
        animal_type = request.form.get("animal_type")
        condition = request.form.get("condition")
        
        if not all([location, description, animal_type, condition]):
            return jsonify({"error": "Missing required fields"}), 400
        
        image = request.files.get("photo")
        image_id = None
        if image:
            image_id = fs.put(image.read(), filename=image.filename, content_type=image.content_type)

        # Classify the report
        category = classify_report(description)

        # Find the most similar report
        most_similar_description = description_compare(description)

        # Retrieve the most similar report from the database
        similar_report = db.reports.find_one({"description": most_similar_description})

        similar_image_id = similar_report.get("image_id") if similar_report else None

        report_data = {
            "location": location,
            "description": description,
            "animal_type": animal_type,
            "condition": condition,
            "category": category,
            "most_similar_description": most_similar_description,
            "image_id": str(image_id) if image_id else None
        }

        # Insert into reports collection
        # result = db.reports.insert_one(report_data)

        return jsonify({
            "message": "Reported successfully",
            # "report_id": str(result.inserted_id),
            "most_similar_description": most_similar_description,
            "similar_image_id": str(similar_image_id) if similar_image_id else None,
            "image_id": str(image_id) if image_id else None
        }), 201
    except Exception as e:
        print(f"Error in report route: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Route to fetch all reports
@app.route('/get-reports', methods=['GET'])
def get_reports():
    try:
        reports = list(db.reports.find({}, {"_id": 0}))
        return jsonify({"reports": reports}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get an animal's image by ID
@app.route('/get-image/<image_id>', methods=['GET'])
def get_image(image_id):
    try:
        image_data = fs.get(ObjectId(image_id))
        return send_file(io.BytesIO(image_data.read()), mimetype=image_data.content_type)
    except Exception as e:
        return jsonify({"error": "Image not found"}), 404

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)  # Prevents WinError 10038
