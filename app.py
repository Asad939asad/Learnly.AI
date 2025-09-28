from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, make_response, session, send_file
from datetime import datetime
from langchain_core import embeddings
from werkzeug.utils import secure_filename
import os
import subprocess
import sys
import io
# UPDATED IMPORT: Import both generate_quiz and the new grade_quiz function
from backend.quizes import generate_quiz, grade_quiz 
from backend.flashcards import generate_flashcards
from backend.query_rag import query_book_rag
from rag_com.indexer import indexer
from backend.slide_decks import generate_slide_deck, create_pdf_from_slides
from backend.manage_books import query_book_content
from langchain_huggingface import HuggingFaceEmbeddings

app = Flask(__name__)
app.config['BOOKS_FOLDER'] = 'books'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
from dotenv import load_dotenv
load_dotenv()
# app.secret_key = 'your-secret-key-here'  # Required for session

# Global variables to store dashboard inputs
global_class = None
global_subjects = []
global_study_topic = None

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

@app.route('/submit_user_info', methods=['POST'])
def submit_user_info():
    global global_class, global_subjects, global_study_topic
    
    data = request.get_json()
    global_class = data.get('class')
    global_subjects = data.get('subjects', [])
    global_study_topic = data.get('study_topic')
    
    return jsonify({"status": "success"})

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
    try:
        data = request.json
        prompt = data.get("prompt")
        use_rag = bool(data.get("use_rag", False))
        book_name = data.get("book_name") if use_rag else None

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        if use_rag and not book_name:
            return jsonify({"error": "book_name is required when use_rag is True"}), 400

        print(f"Prompt: {prompt}, Use RAG: {use_rag}, Book Name: {book_name}")

        # Generate slide deck using the original function
        slide_deck_json = generate_slide_deck(embeddings, prompt, use_rag, book_name)
        print(f"SLLIDE GENERATION DONE")
        return jsonify(slide_deck_json)

    except Exception as e:
        print(f"Error generating slide deck: {str(e)}")
        import traceback
        traceback.print_exc()
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
    global global_class, global_subjects, global_study_topic
    
    # Get RAG settings from the flashcards page
    data = request.get_json()
    rag = data.get('use_rag', False)
    book_name = data.get('book_name')  # Optional parameter
    # Use global variables from dashboard
    if not all([global_class, global_subjects, global_study_topic]):
        return jsonify({
            "status": "error",
            "message": "Please fill out the study information on the dashboard first"
        }), 400
    
    # Generate flashcards using global variables
    flashcards = generate_flashcards(
        embeddings=embeddings,
        sample_query=global_study_topic,
        class_name=f"Class {global_class}",
        subjects=global_subjects,
        rag=rag,
        book_name=book_name
    )
    # print(flashcards)/
    return jsonify({
        "status": "success",
        "flashcards": flashcards
    })
    

@app.route('/query_book', methods=['POST'])
def query_book():
    data = request.get_json()
    book_name = data.get('book_name')
    query = data.get('query')
    
    if not book_name or not query:
        return jsonify({'status': 'error', 'message': 'Book name and query are required'}), 400
    
    try:
        # Use the RAG query function
        response_text = query_book_content(embeddings, book_name, query)
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

@app.route('/download_slide_deck_pdf', methods=['POST'])
def download_slide_deck_pdf():
    try:
        data = request.get_json()
        if not data or 'slide_deck' not in data:
            return jsonify({'error': 'No slide deck data provided'}), 400
            
        try:
            # Generate PDF
            pdf_data = create_pdf_from_slides(data)
            if not pdf_data:
                return jsonify({'error': 'Failed to generate PDF - empty data'}), 500
                
            # Create buffer with PDF data
            buffer = io.BytesIO(pdf_data)
            buffer.seek(0)  # Move to start of buffer
            
            # Get timestamp for filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create sanitized title from slide deck title
            title = data['slide_deck']['title']
            safe_title = "".join(x for x in title if x.isalnum() or x in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_').lower()
            
            # Send file with custom filename
            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'{safe_title}_{timestamp}.pdf'
            )
            
        except Exception as pdf_error:
            print(f"PDF Generation Error: {str(pdf_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'PDF Generation failed: {str(pdf_error)}'}), 500
            
    except Exception as e:
        print(f"Request Processing Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Request processing failed: {str(e)}'}), 500

@app.route('/logout')
def logout():
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(debug=True)