from flask import Flask, request, jsonify
import jwt
import datetime
import os
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
bcrypt = Bcrypt(app)

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
users = {}

@app.route('/v1/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data in register request")
            return jsonify({"error": "Invalid JSON"}), 400

        login = data.get('login')
        password = data.get('password')

        if not login or not password:
            logger.error(f"Missing login/password: login={login}, password={password}")
            return jsonify({"error": "Login and password required"}), 400

        if login in users:
            logger.warning(f"User {login} already exists")
            return jsonify({"error": "User already exists"}), 409

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users[login] = hashed_password
        logger.info(f"User {login} registered successfully")
        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/v1/token', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data in login request")
            return jsonify({"error": "Invalid JSON"}), 400

        login = data.get('login')
        password = data.get('password')

        if not login or not password:
            logger.error(f"Missing login/password: login={login}")
            return jsonify({"error": "Login and password required"}), 400

        if login not in users:
            logger.warning(f"Login attempt for non-existent user: {login}")
            return jsonify({"error": "Invalid credentials"}), 401

        if not bcrypt.check_password_hash(users[login], password):
            logger.warning(f"Invalid password for user: {login}")
            return jsonify({"error": "Invalid credentials"}), 401


        payload = {
            'sub': login,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        logger.info(f"Token issued for user: {login}")
        return jsonify({"token": token}), 200
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
