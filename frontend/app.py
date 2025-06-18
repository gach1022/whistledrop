from flask import Flask, render_template_string, request, redirect
import requests

app = Flask(__name__)

BACKEND_URL = "http://backend:5000/upload"

HTML = """
<!doctype html>
<title>WhistleDrop Upload</title>
<h1>PDF-Datei anonym hochladen</h1>
<form method=post enctype=multipart/form-data>
  <input type=file name=file required>
  <input type=submit value=Hochladen>
</form>
<p>
Das Backend erzeugt einen zufälligen symmetrischen AES-Schlüssel und verschlüsselt das Dokument. Gleichzeitig wird der AES-Schlüssel mit einem unbenutzten öffentlichen RSA-Schlüssel verschlüsselt und zusammen mit dem verschlüsselten PDF in einer Datenbank abgelegt.
</p>
{% if msg %}
  <p>{{msg}}</p>
{% endif %}
"""

@app.route('/', methods=['GET', 'POST'])
def upload():
    msg = None
    if request.method == 'POST':
        file = request.files['file']
        if file:
            files = {'file': (file.filename, file.stream, file.mimetype)}
            try:
                resp = requests.post(BACKEND_URL, files=files)
                msg = resp.json().get('message')
            except Exception as e:
                msg = f"Fehler beim Hochladen: {e}"
    return render_template_string(HTML, msg=msg)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
