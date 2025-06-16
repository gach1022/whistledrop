from flask import Flask, request, jsonify, send_file, render_template_string
import os
import psycopg2
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
import secrets
import io

app = Flask(__name__)

SERVER_DB_URL = os.environ.get('SERVER_DB_URL')

def get_server_conn():
    return psycopg2.connect(SERVER_DB_URL)

def get_unused_public_key():
    with get_server_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, public_key FROM public_keys WHERE used = FALSE LIMIT 1;")
            return cur.fetchone()

def mark_public_key(key_id):
    with get_server_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE public_keys SET used = TRUE WHERE id = %s;", (key_id,))
            conn.commit()

def save_upload(filename, file_encrypted, aes_key_encrypted, public_key_id):
    with get_server_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO uploads (filename, file_encrypted, aes_key_encrypted, public_key_id) VALUES (%s, %s, %s, %s);",
                (filename, psycopg2.Binary(file_encrypted), psycopg2.Binary(aes_key_encrypted), public_key_id)
            )
            conn.commit()

def aes_encrypt(data, key):
    padder = sym_padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded_data) + encryptor.finalize()
    return iv + ct

def rsa_encrypt_key(aes_key, public_key_pem):
    public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
    encrypted = public_key.encrypt(
        aes_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return encrypted

START_HTML = """
<!doctype html>
<title>WhistleDrop Login</title>
<h1>Willkommen bei WhistleDrop</h1>
<form action="/admin" method="get">
    <button type="submit">Login</button>
</form>
"""

@app.route('/', methods=['GET'])
def startseite():
    return render_template_string(START_HTML)

ADMIN_HTML = """
<!doctype html>
<title>Verschlüsselte Uploads</title>
<h1>Verschlüsselte Uploads</h1>
<table border=1 cellpadding=6>
  <tr>
    <th>ID</th>
    <th>Dateiname</th>
    <th>Upload-Zeit</th>
    <th>Download</th>
  </tr>
  {% for u in uploads %}
  <tr>
    <td>{{u.id}}</td>
    <td>{{u.filename}}</td>
    <td>{{u.uploaded_at}}</td>
    <td>
      <a href="/download/{{u.id}}">Download</a>
    </td>
  </tr>
  {% endfor %}
</table>
"""

@app.route('/admin', methods=['GET'])
def admin_uploads():
    uploads = []
    with get_server_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, filename, uploaded_at
                FROM uploads
                ORDER BY uploaded_at DESC;
            """)
            for row in cur.fetchall():
                upload = {
                    "id": row[0],
                    "filename": row[1],
                    "uploaded_at": row[2].isoformat() if row[2] else None
                }
                uploads.append(upload)
    return render_template_string(ADMIN_HTML, uploads=uploads)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file uploaded!'}), 400

    public_key_row = get_unused_public_key()
    if not public_key_row:
        return jsonify({'error': 'No unused public key available!'}), 500

    public_key_id, public_key_pem = public_key_row

    aes_key = secrets.token_bytes(32) 
    file_bytes = file.read()
    encrypted_file = aes_encrypt(file_bytes, aes_key)
    encrypted_aes_key = rsa_encrypt_key(aes_key, public_key_pem)
    save_upload(file.filename, encrypted_file, encrypted_aes_key, public_key_id)
    mark_public_key(public_key_id)

    return jsonify({'status': 'success', 'message': 'Datei verschlüsselt und gespeichert!'})

@app.route('/download/<int:upload_id>', methods=['GET'])
def download(upload_id):
    with get_server_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT filename, file_encrypted, aes_key_encrypted FROM uploads WHERE id = %s;", (upload_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({'error': 'Datei nicht gefunden!'}), 404
            filename, file_encrypted, aes_key_encrypted = row

            response = send_file(
                io.BytesIO(file_encrypted),
                download_name=f"{filename}.encrypted",
                as_attachment=True,
                mimetype='application/octet-stream'
            )
            response.headers['X-Encrypted-AES-Key'] = aes_key_encrypted.hex()
            return response

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
