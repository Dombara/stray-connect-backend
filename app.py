from flask import Flask
from pymongo import MongoClient
import os

MONGO_URI="mongodb+srv://yash:yash@cluster0.jdcnv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

app=Flask(__name__)
client=MongoClient(MONGO_URI)
db=client.get_database('stray-db')



@app.route('/start',methods=['GET'])
def start():
    return "Welcome to Stray-connect"






if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)