# Learnly.AI

An intelligent learning platform that leverages AI to create personalized educational content including quizzes, flashcards, and slide decks. Built with Flask and powered by Groq's LLM API, Learnly.AI uses RAG (Retrieval-Augmented Generation) to generate content based on uploaded PDF books.

## 🚀 Features

### 📚 Book Management
- **PDF Upload & Indexing**: Upload PDF books and automatically create vector embeddings for semantic search
- **RAG Integration**: Generate content based on specific book content using Chroma vector database
- **Book Library**: Manage and organize your uploaded books

### 🧠 AI-Powered Content Generation

#### 📝 Quizzes
- **Customizable Parameters**: Set number of questions, difficulty level, and question type mix
- **Multiple Question Types**: Multiple Choice Questions (MCQ) and Short Answer Questions
- **Intelligent Grading**: Automated grading with semantic analysis for short answers using LLM
- **Real-time Feedback**: Detailed explanations and performance analytics

#### 🎴 Flashcards
- **Personalized Content**: Generate flashcards based on your study topic and class level
- **RAG Support**: Create flashcards from specific book content
- **Study Optimization**: Tailored to your subjects and academic level

#### 📊 Slide Decks
- **Professional Presentations**: Generate comprehensive slide decks on any topic
- **PDF Export**: Download presentations as professionally formatted PDFs
- **RAG Integration**: Create slides based on uploaded book content
- **Multiple Slide Types**: Title slides, paragraphs, bullet points, and numbered lists

### 🎯 Dashboard
- **Study Profile**: Set your class level, subjects, and study topics
- **Unified Interface**: Access all features from a single, intuitive dashboard
- **Progress Tracking**: Monitor your learning progress across different content types

## 🛠️ Technology Stack

- **Backend**: Flask (Python web framework)
- **AI/LLM**: Groq API with Llama 3.1 and Gemma2 models
- **Vector Database**: Chroma for embeddings and semantic search
- **Embeddings**: HuggingFace Sentence Transformers (all-MiniLM-L6-v2)
- **PDF Processing**: PyPDFLoader for document parsing
- **PDF Generation**: ReportLab for creating downloadable presentations
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Database**: SQLite for book metadata storage

## 📋 Prerequisites

- Python 3.8 or higher
- Groq API key (sign up at [groq.com](https://groq.com))
- Git (for cloning the repository)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Asad939asad/Learnly.AI
   cd Learnly.AI
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. **Initialize the database**
   ```bash
   python -c "from backend.database import init_db; init_db()"
   ```

## 🎮 Usage

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Access the application**
   Open your browser and navigate to `http://localhost:5089`

3. **Set up your study profile**
   - Go to the Dashboard
   - Enter your class level, subjects, and study topic
   - Click "Save Study Information"

4. **Upload and index books**
   - Navigate to "Manage Books"
   - Upload PDF files
   - Books will be automatically indexed for RAG functionality

5. **Generate content**
   - **Quizzes**: Create custom quizzes with your preferred settings
   - **Flashcards**: Generate study cards based on your profile or book content
   - **Slide Decks**: Create presentations and download them as PDFs

## 📁 Project Structure

```
Learnly.AI/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── books/                          # Directory for uploaded PDF books
├── chroma_index/                  # Vector database storage
├── backend/                        # Backend modules
│   ├── database.py                # SQLite database operations
│   ├── flash_cards.py             # Flashcard generation logic
│   ├── flashcards.py              # Alternative flashcard module
│   ├── manage_books.py            # Book management functions
│   ├── query_rag.py               # RAG query functionality
│   ├── quizes.py                  # Quiz generation and grading
│   └── slide_decks.py             # Slide deck generation and PDF creation
├── rag_com/                       # RAG components
│   └── indexer.py                 # PDF indexing and vector storage
├── templates/                     # HTML templates
│   ├── dashboard.html             # Main dashboard interface
│   ├── flash_cards.html           # Flashcard generation page
│   ├── manage_books.html          # Book management interface
│   ├── quizes.html                # Quiz creation and taking interface
│   └── slide_decks.html           # Slide deck generation page
└── sample_images_for_UI/          # UI assets
```

## 🔧 Configuration

### Environment Variables
- `GROQ_API_KEY`: Your Groq API key for LLM access

### Application Settings
- **Port**: Default port is 5089 (configurable in `app.py`)
- **File Upload**: Maximum file size is 16MB
- **Vector Database**: Chroma indexes stored in `chroma_index/` directory
- **Book Storage**: PDF files stored in `books/` directory

## 🎯 API Endpoints

### Core Routes
- `GET /` - Dashboard
- `POST /submit_user_info` - Save study profile
- `GET /quizes` - Quiz interface
- `POST /generate_quiz` - Generate quiz
- `POST /grade_quiz` - Grade quiz answers
- `GET /flashcards` - Flashcard interface
- `POST /generate_flashcards` - Generate flashcards
- `GET /slidedecks` - Slide deck interface
- `POST /generate_slide_deck` - Generate slide deck
- `POST /download_slide_deck_pdf` - Download slide deck as PDF
- `GET /manage_books` - Book management interface
- `POST /upload_and_index_book` - Upload and index book
- `POST /query_book` - Query book content

## 🧪 Testing

The application includes built-in error handling and validation. Test the functionality by:

1. Uploading a sample PDF book
2. Generating content with different parameters
3. Testing RAG functionality with book-specific queries
4. Verifying PDF generation and download

## 🚨 Troubleshooting

### Common Issues

1. **Missing API Key**
   - Ensure `GROQ_API_KEY` is set in your `.env` file
   - Verify the API key is valid and has sufficient credits

2. **PDF Upload Issues**
   - Check file size (max 16MB)
   - Ensure PDF is text-based (not scanned images)
   - Verify file permissions

3. **Indexing Problems**
   - Check disk space for vector database storage
   - Ensure proper permissions on `chroma_index/` directory
   - Verify PDF text extraction is working

4. **Content Generation Errors**
   - Check internet connectivity for API calls
   - Verify Groq API service status
   - Review error logs in the application console

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request




---

**Learnly.AI** - Empowering education through artificial intelligence 🚀
