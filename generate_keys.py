import psycopg2
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

serverdb = psycopg2.connect(
    dbname="serverdb", user="serveruser", password="serverpass", host="localhost", port=5434)
journalistdb = psycopg2.connect(
    dbname="journalistdb", user="journalistuser", password="journalistpass", host="localhost", port=5433)

ANZAHL = 4  

for i in range(ANZAHL):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_bytes = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_bytes = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with serverdb.cursor() as cur:
        cur.execute(
            "INSERT INTO public_keys (public_key, used) VALUES (%s, FALSE)", (public_bytes.decode("utf-8"),))
    with journalistdb.cursor() as cur:
        cur.execute(
            "INSERT INTO keypairs (public_key, private_key) VALUES (%s, %s)",
            (public_bytes.decode("utf-8"), private_bytes.decode("utf-8"))
        )

serverdb.commit()
journalistdb.commit()
serverdb.close()
journalistdb.close()

print(f"{ANZAHL} Schlüsselpaare erfolgreich erstellt!")
