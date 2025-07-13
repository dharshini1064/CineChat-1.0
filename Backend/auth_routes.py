from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import jwt
import os

# Setup
bcrypt = Bcrypt()
auth_bp = Blueprint('auth', __name__)
db = SQLAlchemy()

# JWT secret
JWT_SECRET = "cinechat_secret"  # You can make this an environment variable later

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    queries = db.relationship('QueryLog', backref='user', lazy=True)

class QueryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Routes

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "User already exists"}), 409

    hashed = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = User(username=username, password_hash=hashed)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Signup successful"}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        token = jwt.encode({"user_id": user.id}, JWT_SECRET, algorithm="HS256")
        return jsonify({"token": token})
    return jsonify({"error": "Invalid credentials"}), 401

@auth_bp.route("/store-query", methods=["POST"])
def store_query():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return jsonify({"error": "Token missing"}), 401
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = data.get("user_id")
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Invalid user"}), 403
    except Exception as e:
        return jsonify({"error": "Token invalid"}), 401

    content = request.json.get("text", "")
    if not content:
        return jsonify({"error": "Query text missing"}), 400

    log = QueryLog(text=content, user_id=user.id)
    db.session.add(log)
    db.session.commit()

    return jsonify({"message": "Query stored successfully"}), 200

@auth_bp.route("/user-queries", methods=["GET"])
def get_user_queries():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return jsonify({"error": "Token missing"}), 401
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = data.get("user_id")
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Invalid user"}), 403
    except Exception as e:
        return jsonify({"error": "Token invalid"}), 401

    results = [
        {"id": q.id, "text": q.text, "timestamp": q.timestamp}
        for q in user.queries
    ]
    return jsonify(results)
