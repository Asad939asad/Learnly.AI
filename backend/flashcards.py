# def generate_flashcards(use_rag=False):
#     """
#     Generate sample flashcards. This function will be enhanced later with actual RAG implementation.
#     """
#     sample_cards = [
#         {
#             "question": "What is the capital of France?",
#             "answer": "Paris"
#         },
#         {
#             "question": "What is the largest planet in our solar system?",
#             "answer": "Jupiter"
#         },
#         {
#             "question": "Who wrote 'Romeo and Juliet'?",
#             "answer": "William Shakespeare"
#         }
#     ]
    
#     return {
#         "status": "success",
#         "flashcards": sample_cards
#     }



# def generate_flashcards(use_rag=False):
#     """
#     Generate sample flashcards. This function will be enhanced later with actual RAG implementation.
#     """
#     sample_cards = [
#         {
#             "question": "What is the capital of France?",
#             "answer": "Paris"
#         },
#         {
#             "question": "What is the largest planet in our solar system?",
#             "answer": "Jupiter"
#         },
#         {
#             "question": "Who wrote 'Romeo and Juliet'?",
#             "answer": "William Shakespeare"
#         }
#     ]
    
#     return {
#         "status": "success",
#         "flashcards": sample_cards
#     }



import os
import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq  # ✅ Groq LLM

from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ============= SETTINGS ============
INDEX_FOLDER = "./chroma_index"  # root folder for embeddings
GROQ_API_KEY = os.getenv("GROQ_API_KEY") # ✅ direct key
LLM_MODEL = "gemma2-9b-it"  # fast + good for RAG
# ==================================



def normalize_book_name(book_name: str) -> str:
    """Remove .pdf extension (if present) and normalize spaces/underscores."""
    if book_name.lower().endswith(".pdf"):
        book_name = book_name[:-4]
    return book_name.replace(" ", "_")


def load_index(book_name: str, embeddings):
    """Load an existing Chroma index for a book, error if not found."""
    normalized_name = normalize_book_name(book_name)
    book_index_folder = os.path.join(INDEX_FOLDER, normalized_name)

    if not os.path.exists(book_index_folder) or not os.listdir(book_index_folder):
        raise FileNotFoundError(
            f"No Chroma index found for '{book_name}' in {book_index_folder}. "
            "Please create the index first."
        )

    print(f"Loading existing index for '{book_name}'...")
    return Chroma(
        persist_directory=book_index_folder,
        embedding_function=embeddings
    )


def generate_flashcards(embeddings, sample_query: str, class_name: str, subjects: list, rag: bool, book_name: str = None):
    """
    Generate 10 flashcards in JSON format.
    - If rag=True, retrieve context from Chroma index for each question.
    - If rag=False, generate directly from LLM.
    """
    try:
        # ✅ Initialize Groq LLM
        llm = ChatGroq(model=LLM_MODEL, groq_api_key=GROQ_API_KEY)

        # Step 1: Generate 10 questions
        question_prompt = f"""
        You are a teacher. Generate exactly 10 short and clear flashcard-style questions
        for students in {class_name} on the topic "{sample_query}".
        Subjects: {", ".join(subjects)}.

        Only return a JSON array of questions in this format:
        [
          "Question 1?",
          "Question 2?",
          ...
        ]
        """
        question_response = llm.invoke(question_prompt)
        questions = []

        if hasattr(question_response, "content"):
            try:
                import json
                questions = json.loads(question_response.content)
            except:
                # fallback: split by lines if JSON parsing fails
                questions = [q.strip("- ").strip() for q in question_response.content.split("\n") if q.strip()]
        else:
            questions = [q.strip("- ").strip() for q in str(question_response).split("\n") if q.strip()]

        flashcards = []

        # Step 2: For each question, generate short answer
        for q in questions[:10]:  # ensure max 10
            context = []
            if rag and book_name:
                db = load_index(book_name, embeddings)
                results = db.similarity_search(q, k=2)
                context = [res.page_content for res in results]

            answer_prompt = f"""
            You are a teacher answering a flashcard question.

            Question: {q}

            Context from the book (if available):
            {context if rag else "No RAG context. Use your own knowledge."}

            Provide a short answer (1 lines only).
            """
            answer_response = llm.invoke(answer_prompt)
            answer = answer_response.content if hasattr(answer_response, "content") else str(answer_response)

            flashcards.append({
                "question": q,
                "answer": answer.strip()
            })

        return flashcards

    except Exception as e:
        return {"status": "error", "message": str(e)}


# Run standalone (for testing)
# if __name__ == "__main__":
#     result = generate_flashcards(
#         embeddings,
#         sample_query="Photosynthesis basics",
#         class_name="Grade 6",
#         subjects=["Biology", "Science"],
#         rag=False,  # set to False to skip RAG
#         book_name="ec2.pdf"
#     )
#     import json
#     print(json.dumps(result, indent=2))
