from flask import jsonify
from app import app
from flask import request
from flask_pymongo import PyMongo
from bson.json_util import dumps
from bson.json_util import loads


mongo = PyMongo(app)

@app.route('/')
@app.route('/test', methods=['GET'])
def ping_pong():
    return jsonify('test!')

@app.route('/index')
def index():
    pass

@app.route('/api/events', methods=['GET'])
def get_events():
    # page = request.args.get('page')
    # print(page)
    # per_page = request.args.get('per_page')
    events = mongo.db.flares.find({}, {'_id': 0})
    # events = mongo.db.flares.find({}, {'_id': 0}).limit(int(per_page)).skip(page-1 * per_page)

    return jsonify({
        'status': 'success',
        'events': loads(dumps(events))
    })