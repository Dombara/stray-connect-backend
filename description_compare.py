from sentence_transformers import SentenceTransformer, util
from pymongo import MongoClient

# Initialize MongoDB connection once (not inside function)
MONGO_URI = "mongodb+srv://yash:yash@cluster0.jdcnv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.get_database('stray-db')

# Initialize model once
model = SentenceTransformer("all-MiniLM-L6-v2")

def description_compare(data):
    try:
        print("Comparing description:", data)

        # Fetch all descriptions from the 'animals' collection
        descriptions = [doc["description"] for doc in db.animals.find({}, {"description": 1})]

        if not descriptions:
            print("No existing descriptions in the database.")
            return None  # Return None if no descriptions exist

        # Encode descriptions
        des1_embedding = model.encode(data["description"])
        embeddings = model.encode(descriptions)

        # Ensure embeddings are not empty before computing similarity
        if embeddings.shape[0] == 0:
            print("No embeddings found. Returning None.")
            return None

        # Compute similarity scores
        similarities = util.cos_sim(des1_embedding, embeddings)

        # Find the most similar description
        best_match_index = similarities.argmax().item()  # Convert tensor index to int
        most_similar_description = descriptions[best_match_index]

        print(f"Most Similar Description: {most_similar_description}")

        return most_similar_description

    except Exception as e:
        print(f"Error in description_compare: {str(e)}")
        return None
