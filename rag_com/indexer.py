import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ============= SETTINGS ============
INDEX_FOLDER = "./chroma_index"  # root folder for embeddings
# BOOK_NAME = "sample-local-pdf"  # part of the book filename
# QUERY = "Sed lectus"  # example query
# ==================================


def load_index(book_name: str, embeddings):
    """Load an existing Chroma index for a book, error if not found"""
    book_index_folder = os.path.join(INDEX_FOLDER, book_name.replace(" ", "_"))

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


def indexer(embeddings, BOOK_NAME: str, QUERY: str):

    # Step 2: Load index (must already exist)
    db = load_index(BOOK_NAME, embeddings)

    # Step 3: Run a query
    if QUERY:
        print(f"\nQuery: {QUERY}")
        results = db.similarity_search(QUERY, k=1)
        for i, res in enumerate(results, 1):
            print(f"{res.page_content}")

# if __name__ == "__main__":
    # indexer(embeddings, "ec2", "what is ec2?")
