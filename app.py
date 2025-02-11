from flask import Flask, request, jsonify, render_template, send_file
import sqlite3
from fpdf import FPDF
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 📂 Initialisation de la base de données SQLite (Sans colonne 'date')
def init_db():
    conn = sqlite3.connect("rapports.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rapports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            local TEXT UNIQUE,
            category TEXT,
            roomType TEXT,
            corrected TEXT,
            observations TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# 🔹 Route pour afficher l'interface HTML
@app.route("/")
def index():
    return render_template("index.html")

# 🔹 Enregistrer un rapport (mise à jour si doublon)
@app.route("/save_report", methods=["POST"])
def save_report():
    data = request.json
    conn = sqlite3.connect("rapports.db")
    cursor = conn.cursor()
    
    # Vérifier si le local existe déjà
    cursor.execute("SELECT * FROM rapports WHERE local=?", (data["local"],))
    existing_report = cursor.fetchone()

    if existing_report:
        # Mise à jour des informations si le local existe déjà
        cursor.execute("""
            UPDATE rapports SET category=?, roomType=?, corrected=?, observations=?
            WHERE local=?
        """, (data["category"], data["roomType"], data["corrected"], data["observations"], data["local"]))
    else:
        # Insérer un nouveau rapport si le local est nouveau
        cursor.execute("""
            INSERT INTO rapports (local, category, roomType, corrected, observations)
            VALUES (?, ?, ?, ?, ?)
        """, (data["local"], data["category"], data["roomType"], data["corrected"], data["observations"]))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Rapport enregistré avec succès."})

# 🔹 Récupérer tous les rapports enregistrés
@app.route("/get_reports", methods=["GET"])
def get_reports():
    conn = sqlite3.connect("rapports.db")
    cursor = conn.cursor()
    cursor.execute("SELECT local, category, roomType, corrected, observations FROM rapports")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

# 🔹 Exporter les rapports en PDF avec design amélioré
@app.route("/export_pdf", methods=["GET"])
def export_pdf():
    conn = sqlite3.connect("rapports.db")
    cursor = conn.cursor()
    cursor.execute("SELECT local, category, roomType, corrected, observations FROM rapports")
    rows = cursor.fetchall()
    conn.close()

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    # Couleurs et styles pour le titre
    pdf.set_fill_color(50, 50, 50)  # Gris foncé
    pdf.set_text_color(255, 255, 255)  # Texte blanc
    pdf.set_font("Arial", "B", 14)
    pdf.cell(280, 10, "Rapport des Salles", ln=True, align="C", fill=True)
    pdf.ln(10)

    # Entêtes du tableau avec un fond gris
    headers = ["Local", "Catégorie", "Type", "Corrigée", "Observations"]
    col_widths = [50, 50, 50, 30, 100]

    pdf.set_fill_color(100, 100, 100)  # Gris intermédiaire
    pdf.set_text_color(255, 255, 255)  # Blanc
    pdf.set_font("Arial", "B", 12)

    for header, width in zip(headers, col_widths):
        pdf.cell(width, 10, header, 1, 0, "C", fill=True)
    pdf.ln()

    # Contenu du tableau avec alternance de couleurs
    pdf.set_fill_color(240, 240, 240)  # Gris clair
    pdf.set_text_color(0, 0, 0)  # Texte noir
    pdf.set_font("Arial", "", 10)

    fill = False  # Alternance de couleurs pour les lignes
    for row in rows:
        for value, width in zip(row, col_widths):
            pdf.cell(width, 10, str(value), 1, 0, "C", fill=fill)
        pdf.ln()
        fill = not fill  # Alterne la couleur de fond

    pdf_file = "Rapports.pdf"
    pdf.output(pdf_file)
    return send_file(pdf_file, mimetype="application/pdf", as_attachment=False)

# 🔹 Lancer l'application Flask
if __name__ == "__main__":
    app.run(debug=True)
