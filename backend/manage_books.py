# def query_book_content(embeddings,book_name: str, query: str) -> str:
#     """
#     Temporary function to simulate book querying
    
#     Args:
#         book_name: Name of the book to query
#         query: User's question about the book
        
#     Returns:
#         A simulated response
#     """
#     print(f"Query received - Book: {book_name}, Query: {query}")
#     # This is a temporary response to test the UI functionality
#     return f"This is a simulated response for your query: '{query}' about the book '{book_name}'.\n\n" + \
#            "In the actual implementation, this will use the RAG system to provide real answers from the book content."

# 
# import os
# from langchain_community.vectorstores import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings

# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# # ============= SETTINGS ============
# INDEX_FOLDER = "./chroma_index"  # root folder for embeddings
# # BOOK_NAME = "sample-local-pdf"  # part of the book filename
# # QUERY = "Sed lectus"  # example query
# # ==================================


# def load_index(book_name: str, embeddings):
#     """Load an existing Chroma index for a book, error if not found"""
#     book_index_folder = os.path.join(INDEX_FOLDER, book_name.replace(" ", "_"))

#     if not os.path.exists(book_index_folder) or not os.listdir(book_index_folder):
#         raise FileNotFoundError(
#             f"No Chroma index found for '{book_name}' in {book_index_folder}. "
#             "Please create the index first."
#         )

#     print(f"Loading existing index for '{book_name}'...")
#     return Chroma(
#         persist_directory=book_index_folder,
#         embedding_function=embeddings
#     )


# def indexer(embedding, BOOK_NAME: str, QUERY: str):

#     # Step 2: Load index (must already exist)
#     db = load_index(BOOK_NAME, embeddings)

#     # Step 3: Run a query
#     if QUERY:
#         print(f"\nQuery: {QUERY}")
#         results = db.similarity_search(QUERY, k=1)
#         for i, res in enumerate(results, 1):
#             print(f"\n[{i}] ---- Retrieved Context ----\n{res.page_content}\n")

# if __name__ == "__main__":
#     indexer(embeddings, "ec2", "what is ec2?")

import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq  # ✅ Groq LLM

# Embeddings model
# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
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


def query_book_content(embeddings, book_name: str, query: str) -> str:
    """
    Query a book's Chroma index, pass context to Groq LLM,
    and return ONLY the LLM's response.
    """
    try:
        db = load_index(book_name, embeddings)
        results = db.similarity_search(query, k=2)  # retrieve top-3 chunks for richer context

        # Gather context
        context = [res.page_content for res in results]

        # Initialize Groq LLM
        llm = ChatGroq(model=LLM_MODEL, groq_api_key=GROQ_API_KEY)

        # Prepare prompt for RAG
        rag_prompt = f"""
        You are a helpful assistant answering questions about a book.  

        - If relevant context is provided, use it to guide your answer.  
        - If context is missing or insufficient, rely on your own knowledge to provide the best possible response.  
        - Always keep your response clear, concise, and accurate.  

        Context from the book (if available):  
        {context}

        User query: {query}

        Final Answer:
        """


        llm_response = llm.invoke(rag_prompt)

        # ✅ Return only the LLM response
        return llm_response.content if hasattr(llm_response, "content") else str(llm_response)

    except Exception as e:
        return f"Error: {str(e)}"


# # Run standalone (for testing)
# if __name__ == "__main__":
#     result = query_book_content(embeddings, "ec2.pdf", "what is ec2?")
#     print(result)
