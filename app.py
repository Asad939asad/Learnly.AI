from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from langchain_core import embeddings
from werkzeug.utils import secure_filename
import os
import subprocess
import sys
# UPDATED IMPORT: Import both generate_quiz and the new grade_quiz function
from backend.quizes import generate_quiz, grade_quiz 
from backend.flashcards import generate_flashcards
from backend.query_rag import query_book_rag
from rag_com.indexer import indexer
from backend.slide_decks import generate_slide_deck
from backend.manage_books import query_book_content
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
app = Flask(__name__)
app.config['BOOKS_FOLDER'] = 'books'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure required directories exist with proper permissions
os.makedirs(app.config['BOOKS_FOLDER'], exist_ok=True)
os.chmod(app.config['BOOKS_FOLDER'], 0o777)  # Full read/write permissions

# Ensure Chroma index directory exists with proper permissions
CHROMA_INDEX_DIR = os.path.join(os.getcwd(), 'chroma_index')
os.makedirs(CHROMA_INDEX_DIR, exist_ok=True)
os.chmod(CHROMA_INDEX_DIR, 0o777)  # Full read/write permissions

@app.route("/")
def dashboard():
    return render_template("dashboard.html", active_page='dashboard')

@app.route("/quizes")
def quizes():
    return render_template("quizes.html", active_page='quizes')

# =========================================================
# QUIZ GENERATION ROUTE (Updated to accept parameters)
# =========================================================
@app.route("/generate_quiz", methods=["POST"])
def generate_quiz_route():
    data = request.json
    
    # Safely extract all required parameters from the frontend payload
    prompt = data.get("prompt", "Generate a general knowledge quiz with 3 questions.")
    num_questions = data.get("num_questions", 10)
    difficulty = data.get("difficulty", "Medium")
    mcq_percent = data.get("mcq_percent", 70) 

    try:
        quiz_json = generate_quiz(
            prompt=prompt, 
            num_questions=num_questions, 
            difficulty=difficulty, 
            mcq_percent=mcq_percent
        )
        return jsonify(quiz_json)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================
# NEW GRADING ROUTE
# =========================================================
@app.route("/grade_quiz", methods=["POST"])
def grade_quiz_route():
    data = request.json
    quiz_data = data.get("quiz_data")
    user_answers = data.get("user_answers")
    
    if not quiz_data or not user_answers:
        return jsonify({"error": "Missing quiz data or user answers"}), 400

    try:
        # Call the new grading function
        graded_results = grade_quiz(quiz_data, user_answers)
        return jsonify(graded_results)
    except Exception as e:
        print(f"Grading Error: {str(e)}")
        return jsonify({"error": f"Failed to grade quiz: {str(e)}"}), 500
# =========================================================

@app.route("/flashcards")
def flashcards():
    books = get_available_books()
    return render_template("flash_cards.html", active_page='flashcards', books=books)

@app.route("/slidedecks")
def slidedecks():
    return render_template("slide_decks.html", active_page='slidedecks')

@app.route("/generate_slide_deck", methods=["POST"])
def generate_slide_deck_route():
    data = request.json
    prompt = data.get("prompt", "Generate a presentation on the topic of Artificial Intelligence.")

    try:
        slide_deck_json = generate_slide_deck(prompt)
        return jsonify(slide_deck_json)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/manage_books")
def manage_books():
    return render_template("manage_books.html", active_page='books')

@app.route('/list_books')
def list_books():
    books = get_available_books()
    return jsonify({
        'status': 'success',
        'books': books
    })

@app.route('/upload_book', methods=['POST'])
def upload_book():
    if 'book' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    
    file = request.files['book']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['BOOKS_FOLDER'], filename)
        file.save(file_path)
        
        return jsonify({
            'status': 'success',
            'message': 'Book uploaded successfully'
        })

@app.route('/upload_and_index_book', methods=['POST'])
def upload_and_index_book():
    if 'book' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    
    file = request.files['book']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        try:
            # Save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['BOOKS_FOLDER'], filename)
            file.save(file_path)
            print(f"Book saved to: {file_path}")
            
            # Extract book name without extension for indexing
            book_name = os.path.splitext(filename)[0]
            print(f"Indexing book: {book_name}")
            
            # Call the indexer function directly
            success = indexer(embeddings, book_name)
            
            if success:
                print("Indexing done")
                return jsonify({
                    'status': 'success',
                    'message': 'Book uploaded and indexed successfully!'
                })
            else:
                print("Indexing failed")
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to index the book'
                }), 500
                
        except Exception as e:
            print(f"Error during upload/indexing: {str(e)}")
            # If there was an error, try to clean up the uploaded file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
            return jsonify({
                'status': 'error',
                'message': f'Error during upload/indexing: {str(e)}'
            }), 500
    else:
        return jsonify({'status': 'error', 'message': 'Only PDF files are supported'}), 400

@app.route('/delete_book', methods=['POST'])
def delete_book():
    data = request.get_json()
    book_name = data.get('name')
    
    if not book_name:
        return jsonify({'status': 'error', 'message': 'No book name provided'}), 400
    
    file_path = os.path.join(app.config['BOOKS_FOLDER'], secure_filename(book_name))
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'status': 'success', 'message': 'Book deleted successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Book not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/generate_flashcards', methods=['POST'])
def create_flashcards():
    data = request.get_json()
    use_rag = data.get('use_rag', False)
    
    # For now, just return sample flashcards
    return jsonify(generate_flashcards(use_rag))

@app.route('/query_book', methods=['POST'])
def query_book():
    data = request.get_json()
    book_name = data.get('book_name')
    query = data.get('query')
    
    if not book_name or not query:
        return jsonify({'status': 'error', 'message': 'Book name and query are required'}), 400
    
    try:
        # Use the temporary query function for testing
        response_text = query_book_content(book_name, query)
        print(f"Query received - Book: {book_name}, Query: {query}")
        print(f"Response: {response_text}")
        
        return jsonify({
            'status': 'success',
            'response': response_text
        })
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error processing query: {str(e)}'
        }), 500

def get_available_books():
    books = []
    for filename in os.listdir(app.config['BOOKS_FOLDER']):
        file_path = os.path.join(app.config['BOOKS_FOLDER'], filename)
        if os.path.isfile(file_path):
            file_type = os.path.splitext(filename)[1][1:].upper()
            books.append({
                'name': filename,
                'type': file_type
            })
    return books

@app.route('/logout')
def logout():
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(debug=True)