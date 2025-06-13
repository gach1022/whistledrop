import sys
import os
import psycopg2
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding


SERVERDB = {
    "dbname": "serverdb",
    "user": "serveruser",
    "password": "serverpass",
    "host": "localhost",
    "port": 5434 
}
JOURNALISTDB = {
    "dbname": "journalistdb",
    "user": "journalistuser",
    "password": "journalistpass",
    "host": "localhost",
    "port": 5433 
}

def aes_decrypt(enc_data, key):
    iv = enc_data[:16]
    ciphertext = enc_data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = sym_padding.PKCS7(128).unpadder()
    data = unpadder.update(padded) + unpadder.finalize()
    return data

def decrypt_aes_key(encrypted_aes_key, private_key_pem):
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"),
        password=None
    )
    return private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )

def main():
    if len(sys.argv) != 2:
        print("Nutzung: python decrypt_file.py <Pfad/zur/verschluesselten_Datei>")
        sys.exit(1)
    encrypted_file_path = sys.argv[1]
    if not os.path.exists(encrypted_file_path):
        print(f"Datei nicht gefunden: {encrypted_file_path}")
        sys.exit(1)

    orig_filename = os.path.basename(encrypted_file_path)
    if orig_filename.endswith('.encrypted'):
        db_filename = orig_filename[:-10]
    else:
        db_filename = orig_filename
    print(f"Suche in Datenbank nach Datei: '{db_filename}'...")

    sconn = psycopg2.connect(**SERVERDB)
    scur = sconn.cursor()
    scur.execute(
        "SELECT id, file_encrypted, aes_key_encrypted, public_key_id FROM uploads WHERE filename = %s ORDER BY uploaded_at DESC LIMIT 1",
        (db_filename,))
    upload_row = scur.fetchone()
    if not upload_row:
        print("Kein Upload-Eintrag mit diesem Dateinamen gefunden.")
        sys.exit(1)
    upload_id, file_encrypted_db, aes_key_encrypted_db, public_key_id = upload_row
    print(f"Upload-ID: {upload_id}, public_key_id: {public_key_id}")

    scur.execute(
        "SELECT public_key FROM public_keys WHERE id = %s",
        (public_key_id,))
    public_key_pem = scur.fetchone()[0]

    jconn = psycopg2.connect(**JOURNALISTDB)
    jcur = jconn.cursor()
    jcur.execute(
        "SELECT private_key FROM keypairs WHERE public_key = %s",
        (public_key_pem,))
    keypair_row = jcur.fetchone()
    if not keypair_row:
        print("Kein passender Private Key in der journalistdb gefunden!")
        sys.exit(1)
    private_key_pem = keypair_row[0]
    print("Private Key gefunden.")

    with open(encrypted_file_path, "rb") as f:
        file_encrypted = f.read()
    if file_encrypted != file_encrypted_db:
        print("Warnung: Datei auf Platte und Datei aus DB unterscheiden sich (es wird die Datei von der Platte entschlüsselt).")

    aes_key = decrypt_aes_key(aes_key_encrypted_db.tobytes(), private_key_pem)
    print("AES-Key erfolgreich entschlüsselt.")

    clear_data = aes_decrypt(file_encrypted, aes_key)
    decrypted_file_path = os.path.splitext(encrypted_file_path)[0] + "_entschluesselt" + os.path.splitext(db_filename)[1]
    with open(decrypted_file_path, "wb") as f:
        f.write(clear_data)
    print(f"Datei erfolgreich entschlüsselt und gespeichert als: {decrypted_file_path}")

    scur.close()
    sconn.close()
    jcur.close()
    jconn.close()

if __name__ == "__main__":
    main()
