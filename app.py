from flask import Flask , request,jsonify, send_file
from pymongo import MongoClient
import gridfs
import os

MONGO_URI="mongodb+srv://yash:yash@cluster0.jdcnv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

app=Flask(__name__)
client=MongoClient(MONGO_URI)
db=client.get_database('stray-db')

fs = gridfs.GridFS(db)


@app.route('/start',methods=['GET'])
def start():
    return "Welcome to Stray-connect"








@app.route('/report',methods=['POST'])
def report():

    location = request.form.get("location")
    description = request.form.get("description")
    animal_type = request.form.get("animal_type")
    condition = request.form.get("condition")



    if 'image' in request.files:
        image = request.files['image']
        image_id = fs.put(image, filename=image.filename)  # Store image in GridFS
    else:
        image_id = None
    


    report = db.reports.insert_one({
        "location": location,
        "description": description,
        "animal_type": animal_type,
        "condition": condition,
        "image_id": str(image_id) if image_id else None
    })
    





    return "Reported",200






















if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)