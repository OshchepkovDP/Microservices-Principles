import secrets
import os

def generate_secrets():
    secret_key = secrets.token_hex(32)  # 64-символьный ключ
    minio_access_key = 'minioadmin'
    minio_secret_key = secrets.token_hex(16)  # 32-символьный пароль для MinIO

    with open('.env', 'w') as f:
        f.write(f'SECRET_KEY={secret_key}\n')
        f.write(f'MINIO_ACCESS_KEY={minio_access_key}\n')
        f.write(f'MINIO_SECRET_KEY={minio_secret_key}\n')

    print("Секретные ключи успешно сгенерированы и сохранены в .env")
    print(f"SECRET_KEY: {secret_key}")
    print(f"MINIO_SECRET_KEY: {minio_secret_key}")

if __name__ == '__main__':
    generate_secrets()
