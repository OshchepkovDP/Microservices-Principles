from flask import Flask, request, jsonify, send_file
from minio import Minio
from minio.error import S3Error
import io
import uuid
import time
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

minio_endpoint = os.environ.get('MINIO_ENDPOINT', 'minio:9000')
access_key = os.environ.get('MINIO_ACCESS_KEY')
secret_key = os.environ.get('MINIO_SECRET_KEY')

minio_client = Minio(
    minio_endpoint,
    access_key=access_key,
    secret_key=secret_key,
    secure=False
)

def wait_for_minio():
    for attempt in range(10):
        try:
            minio_client.list_buckets()
            logger.info("MinIO is ready")
            return True
        except Exception as e:
            logger.warning(f"MinIO not ready (attempt {attempt + 1}): {e}")
            time.sleep(5)
    logger.error("MinIO never became ready")
    return False

def create_bucket():
    if not wait_for_minio():
        logger.error("Cannot connect to MinIO, bucket creation skipped")
        return False
    try:
        if not minio_client.bucket_exists("images"):
            minio_client.make_bucket("images")
            logger.info("Bucket 'images' created successfully")
        else:
            logger.info("Bucket 'images' already exists")
        return True
    except S3Error as exc:
        logger.error(f"Bucket creation error: {exc}")
        return False

create_bucket()

@app.route('/v1/upload', methods=['POST'])
def upload_file():
    # Проверяем существование бакета
    if not minio_client.bucket_exists("images"):
        logger.error("Bucket 'images' does not exist")
        return jsonify({"error": "Storage not available"}), 503

    # Получаем бинарные данные
    if not request.data:
        logger.error("No binary data provided in upload request")
        return jsonify({"error": "No file data provided"}), 400

    try:
        # Генерируем уникальное имя
        file_extension = 'jpg'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # Загружаем в MinIO
        minio_client.put_object(
            "images",
            unique_filename,
            io.BytesIO(request.data),
            length=len(request.data),
            content_type='image/jpeg'
        )

        logger.info(f"File {unique_filename} uploaded successfully")
        return jsonify({
            "filename": unique_filename,
            "size": len(request.data),
            "url": f"/images/{unique_filename}"
        }), 201
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return jsonify({"error": "Upload failed"}), 500

@app.route('/v1/images/<filename>', methods=['GET'])
def get_image(filename):
    """Получение файла из MinIO"""
    try:
        # Получаем объект из MinIO
        response = minio_client.get_object("images", filename)
        return send_file(
            io.BytesIO(response.read()),
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=filename
        )
    except S3Error as exc:
        if exc.code == 'NoSuchKey':
            logger.error(f"Image {filename} not found")
            return jsonify({"error": "Image not found"}), 404
        logger.error(f"Error retrieving image {filename}: {exc}")
        return jsonify({"error": "Internal server error"}), 500
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
