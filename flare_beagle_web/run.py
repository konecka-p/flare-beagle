from flask import jsonify
from app import app
from flask_cors import CORS

CORS(app, resources=r'/api/events', allow_headers='Content-Type')

events = [
    {'date_start': 0,
     'date_end': '1',
     'area': '1',
     'ap': '1',
     'duration': '1992'},
    {'date_start': 0,
     'date_end': '1',
     'area': '1',
     'ap': '1',
     'duration': '1'},
    {'date_start': 0,
     'date_end': '1',
     'area': '1',
     'ap': '1',
     'duration': '1992'}
]
# events = mongo.db.flares.find({}, {'_id': 0}).limit(1)

if __name__ == '__main__':
    app.run()
