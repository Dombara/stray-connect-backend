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

        # Classify the report
        category = classify_report(description)

        # Find the most similar report
        most_similar_description = description_compare(description)

        # Retrieve the most similar report from the database
        similar_report = db.reports.find_one({"description": most_similar_description})

        if similar_report:
            similar_report_data = {
                "location": similar_report.get("location"),
                "description": similar_report.get("description"),
                "animal_type": similar_report.get("animal_type"),
                "condition": similar_report.get("condition"),
                "category": similar_report.get("category"),
                "image_url": f"/get-image/{similar_report.get('image_id')}" if similar_report.get("image_id") else None
            }
        else:
            similar_report_data = None  # No similar report found

        response_data = {
            "location": location,
            "description": description,
            "animal_type": animal_type,
            "condition": condition,
            "category": category,
            "most_similar_report": similar_report_data  # Returning full data of most similar report
        }

        return jsonify(response_data), 200
    except Exception as e:
        print(f"Error in report route: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/insert-animals', methods=['POST'])
def insert_animals():
    try:
        animals = request.json
        db.animals.insert_one(animals)
        return jsonify({"message": "Animals inserted successfully"}), 200
    except Exception as e:
        print(f"Error in insert_animals route: {str(e)}")
        return jsonify({"error": str(e)}), 500
    




@app.route('/insert-reports', methods=['POST'])
def insert_reports():
    try:
        # Extract form data
        location = request.form.get("location")
        description = request.form.get("description")
        animal_type = request.form.get("animal_type")
        condition = request.form.get("condition")

        # Check for missing fields
        if not all([location, description, animal_type, condition]):
            return jsonify({"error": "Missing required fields"}), 400

        # Handle image upload
        image = request.files.get("photo")
        image_id = None
        if image:
            image_id = fs.put(image.read(), filename=image.filename, content_type=image.content_type)

        # Prepare report data
        report_data = {
            "location": location,
            "description": description,
            "animal_type": animal_type,
            "condition": condition,
            "image_id": str(image_id) if image_id else None  # Store image_id if available
        }

        # Insert report into MongoDB
        db.reports.insert_one(report_data)

        return jsonify({
            "message": "Report inserted successfully",
            "report": report_data  # Return the inserted report details
        }), 200

    except Exception as e:
        print(f"Error in insert_reports route: {str(e)}")
        return jsonify({"error": str(e)}), 500







@app.route('/get-animals', methods=['GET'])
def get_animals():
    try:
        animals = list(db.animals.find({}, {"_id": 0}))
        return jsonify(animals), 200
    except Exception as e:
        print(f"Error in get_animals route: {str(e)}")
        return jsonify({"error": str(e)}), 500
    


@app.route('/get-reports', methods=['GET'])
def get_reports():
    try:
        reports = list(db.reports.find({}, {"_id": 0}))
        return jsonify(reports), 200
    except Exception as e:
        print(f"Error in get_reports route: {str(e)}")
        return jsonify({"error": str(e)}), 500






# @app.route('/get-lost-and-found', methods=['GET'])
# def get_lost_and_found():
#     try:
#         # Fetch all reports with category "Lost Pet Report"
#         lost_and_found = list(db.reports.find({"category": "Lost Pet Report"}, {"_id": 0}))
#         return jsonify(lost_and_found), 200
#     except Exception as e:
#         print(f"Error in get_lost_and_found route: {str(e)}")
#         return jsonify({"error": str(e)}), 500
    


# app.post("/post-lost-pet", async (req, res) => {
#   try {
#     const { name, ownername, type, description, lastseen, contact, photo } = req.body;
#     if (!name || !ownername || !type || !description || !lastseen || !contact) {
#       return res.status(400).json({ error: "All fields except photo are required." });
#     }

#     const newPet = new Pet({ name, ownername, type, description, lastseen, contact, photo });
#     await newPet.save();

#     res.status(201).json({ message: "Lost pet reported successfully!", pet: newPet });
#   } catch (error) {
#     console.error("Error saving pet data:", error);
#     res.status(500).json({ error: "Internal Server Error" });
#   }
# });



@app.route('insert-lost-and-found', methods=['POST'])
def insert_lost_and_found():
    try:
        # Extract form data
        owner_name = request.form.get("owner_name")
        pet_name = request.form.get("pet_name")
        breed = request.form.get("breed")
        location = request.form.get("location")
        description = request.form.get("description")
        animal_type = request.form.get("animal_type")
        last_seen = request.form.get("last_seen")
        contact = request.form.get("contact")
        # image = request.files.get("photo")

        if not all([owner_name, pet_name, breed, location, description, animal_type, last_seen, contact]):
            return jsonify({"error": "Missing required fields"}), 400
        
        image=request.files.get("photo")
        image_id=None

        if image:
            image_id=fs.put(image.read(),filename=image.filename,content_type=image.content_type)

        lost_pet_data = {
            "pet_name": pet_name,
            "owner_name": owner_name,
            "animal_type": animal_type,
            "description": description,
            "last_seen": last_seen,
            "contact": contact,
            "breed": breed,
            "location": location,
            "image_id": str(image_id) if image_id else None  # Store image_id if available
        }

        db.lost_and_found.insert_one(lost_pet_data)

        return jsonify({
            "message": "Lost & Found report inserted successfully",
            "report": lost_pet_data  # Return the inserted data
        }), 200

        
    except Exception as e:
        print(f"Error in insert_lost_and_found route: {str(e)}")
        return jsonify({"error": str(e)}), 500











@app.route('get-lost-and-found', methods=['GET'])
def get_lost_and_found():
    try:
        lost_and_found_data = db.lost_and_found.find()
        return jsonify({"lost_and_found": list(lost_and_found_data)}), 200
    except Exception as e:
        print(f"Error in get_lost_and_found route: {str(e)}")
        return jsonify({"error": str(e)}), 500



        # name, ownername, type, description, lastseen, contact, photo 












# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)  # Prevents WinError 10038

