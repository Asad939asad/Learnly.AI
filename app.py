from flask import Flask, render_template, request, jsonify
from backend.quizes import generate_quiz

app = Flask(__name__)

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/quizes")
def quizes():
    return render_template("quizes.html")

@app.route("/generate_quiz", methods=["POST"])
def generate_quiz_route():
    data = request.json
    prompt = data.get("prompt", "Generate a general knowledge quiz with 3 questions.")

    try:
        quiz_json = generate_quiz(prompt)
        return jsonify(quiz_json)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/flashcards")
def flashcards():
    return render_template("flash_cards.html")

@app.route("/slidedecks")
def slidedecks():
    return render_template("slide_decks.html")

@app.route("/books")
def books():
    return render_template("manage_books.html")

if __name__ == "__main__":
    app.run(debug=True)
