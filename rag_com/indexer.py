import os
import glob
import sys
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# ============= SETTINGS ============
BOOKS_FOLDER = "./books"         # folder where your books are stored
INDEX_FOLDER = "./chroma_index"  # root folder for embeddings
# BOOK_NAME = "ec2"  # part of the book filename
# ==================================


def find_book(book_name: str, folder: str):
    """Search for a PDF file in a folder"""
    pattern = f"{folder}/**/*{book_name}*.pdf"
    matches = glob.glob(pattern, recursive=True)
    return matches[0] if matches else None


def load_book(path: str):
    """Load a PDF into LangChain documents (page by page)"""
    loader = PyPDFLoader(path)
    return loader.load()

def indexer(embeddings, BOOK_NAME: str):
    # Step 1: Find the book
    book_path = find_book(BOOK_NAME, BOOKS_FOLDER)
    if not book_path:
        print(f"No PDF found with name containing '{BOOK_NAME}' in {BOOKS_FOLDER}")
        return False
    print(f"Found book: {book_path}")

    # Step 2: Load book (pages)
    docs = load_book(book_path)
    print(f"Loaded {len(docs)} pages from PDF")

    if not docs:
        print("No text extracted from PDF (might be scanned images).")
        return False

    # Step 3: Split each page into max 100-token chunks
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=100,    # max 100 tokens
        chunk_overlap=20   # allow some overlap
    )
    chunks = splitter.split_documents(docs)
    print(f"Split {len(docs)} pages into {len(chunks)} chunks (≤100 tokens each)")

    # Step 4: Initialize embeddings
    # embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Step 5: Save each book in its own folder
    book_index_folder = os.path.join(INDEX_FOLDER, BOOK_NAME.replace(" ", "_"))
    
    # Ensure the book index folder exists and has proper permissions
    os.makedirs(book_index_folder, exist_ok=True)
    os.chmod(book_index_folder, 0o777)  # Full read/write permissions
    
    try:
        db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=book_index_folder
        )
        db.persist()
        print(f"Index for '{BOOK_NAME}' saved in {book_index_folder}")
        return True
    except Exception as e:
        print(f"Error creating index: {str(e)}")
        return False


# def main():
#     if len(sys.argv) > 1:
#         book_name = sys.argv[1]
#         success = indexer(book_name)
#         if not success:
#             sys.exit(1)
#         print("Indexing done")
#     else:
#         print("Usage: python indexer.py <book_name>")
#         sys.exit(1)

# if __name__ == "__main__":
#     main()
