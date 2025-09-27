# # backend/slide_decks.py

# import os
# import io
# import json
# from datetime import datetime
# from dotenv import load_dotenv
# from langchain_core import embeddings
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import letter
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
# from reportlab.lib.enums import TA_CENTER, TA_LEFT

# # LangChain / Groq imports
# from langchain_community.vectorstores import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_groq import ChatGroq

# # Load environment variables
# load_dotenv()
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# LLM_MODEL = "gemma2-9b-it"
# INDEX_FOLDER = "./chroma_index"

# # Initialize embeddings
# # embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


# # ----------------- Utility Functions -----------------
# def normalize_book_name(book_name: str) -> str:
#     """Normalize book name for folder/index usage."""
#     if book_name.lower().endswith(".pdf"):
#         book_name = book_name[:-4]
#     return book_name.replace(" ", "_")


# def load_index(embeddings, book_name: str):
#     """Load Chroma index for a book."""
#     normalized_name = normalize_book_name(book_name)
#     index_folder = os.path.join(INDEX_FOLDER, normalized_name)
#     if not os.path.exists(index_folder) or not os.listdir(index_folder):
#         raise FileNotFoundError(f"No index found for book: {book_name}")
#     return Chroma(persist_directory=index_folder, embedding_function=embeddings)


# # ----------------- Slide Deck Generation -----------------
# def generate_slide_deck(embeddings, prompt: str, use_rag: bool, book_name: str):
#     if not GROQ_API_KEY:
#         raise ValueError("Missing GROQ_API_KEY in environment")

#     llm = ChatGroq(model=LLM_MODEL, groq_api_key=GROQ_API_KEY)

#     # Retrieve RAG context if requested
#     context = []
#     if use_rag and book_name:
#         db = load_index(embeddings, book_name)
#         results = db.similarity_search(prompt, k=12)
#         context = [r.page_content for r in results]

#     # Build prompt
#     final_prompt = f"You are a presentation slide generator.\nTopic: {prompt}\n"
#     if context:
#         final_prompt += "Use the following context from the book:\n" + "\n".join(context)

#     final_prompt += """
# Return output as valid JSON in this exact schema:
# {
#   "slide_deck": {
#     "title": string,
#     "topic": string,
#     "metadata": {
#       "created_at": string,
#       "created_by": string,
#       "total_slides": number
#     },
#     "slides": [
#       {
#         "slide_id": string,
#         "slide_type": "title_slide" | "paragraph" | "unordered_list" | "ordered_list",
#         "slide_title": string,
#         "slide_content": string | [string]
#       }
#     ]
#   }
# }
# """

#     response = llm.invoke(final_prompt)

#     # Convert response to string
#     raw_text = response.content if hasattr(response, "content") else str(response)
#     raw_text = raw_text.strip()

#     # Remove ```json and ``` code fences if present
#     if raw_text.startswith("```"):
#         raw_text = "\n".join(raw_text.splitlines()[1:])  # remove first ```json line
#         if raw_text.endswith("```"):
#             raw_text = "\n".join(raw_text.splitlines()[:-1])  # remove last ``` line
#         raw_text = raw_text.strip()

#     # Parse JSON
#     try:
#         slide_deck_json = json.loads(raw_text)
#     except json.JSONDecodeError as e:
#         raise ValueError(f"LLM returned invalid JSON:\n{raw_text}\nOriginal error: {str(e)}")

#     return slide_deck_json

# # ----------------- PDF Generation -----------------
# def create_pdf_from_slides(slide_deck_data):
#     """Generate a PDF from slide deck JSON with 16:9 aspect ratio"""
#     width, height = 612, 612 * 9 / 16
#     pagesize = (width, height)

#     buffer = io.BytesIO()
#     doc = SimpleDocTemplate(
#         buffer,
#         pagesize=pagesize,
#         rightMargin=30,
#         leftMargin=30,
#         topMargin=30,
#         bottomMargin=30
#     )

#     styles = getSampleStyleSheet()
#     title_style = ParagraphStyle(
#         "CustomTitle", parent=styles["Title"], fontSize=60, leading=50,
#         alignment=TA_CENTER, spaceAfter=0, textColor=colors.HexColor("#9f3dff")
#     )
#     heading_style = ParagraphStyle(
#         "CustomHeading", parent=styles["Heading1"], fontSize=30, leading=34,
#         alignment=TA_CENTER, spaceAfter=15, textColor=colors.HexColor("#333333")
#     )
#     content_style = ParagraphStyle(
#         "CustomContent", parent=styles["Normal"], fontSize=20,
#         alignment=TA_LEFT, spaceAfter=12, leading=24, textColor=colors.HexColor("#666666")
#     )
#     list_style = ParagraphStyle(
#         "ListStyle", parent=content_style, leftIndent=30,
#         spaceAfter=10, leading=24, bulletIndent=15, spaceBefore=5
#     )

#     story = []

#     # First slide: only title
#     title = slide_deck_data["slide_deck"]["title"]
#     story.append(Spacer(1, height / 3))
#     story.append(Paragraph(title, title_style))
#     story.append(PageBreak())

#     # Content slides
#     slides = slide_deck_data["slide_deck"]["slides"]
#     for idx, slide in enumerate(slides):
#         slide_title = slide.get("slide_title", "")
#         story.append(Paragraph(slide_title.strip() or "(No Title)", heading_style))

#         approx_title_height = 50
#         remaining_height = height - approx_title_height - 60
#         story.append(Spacer(1, remaining_height / 4))

#         content = slide.get("slide_content")
#         if isinstance(content, str):
#             paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()] or ["(No content)"]
#             for para in paragraphs:
#                 story.append(Paragraph(para, content_style))
#                 story.append(Spacer(1, 10))
#         elif isinstance(content, list):
#             content_items = [item.strip() for item in content if item.strip()] or ["(No content)"]
#             for i, item in enumerate(content_items):
#                 bullet = f"• {item}" if slide["slide_type"] == "unordered_list" else f"{i+1}. {item}"
#                 story.append(Paragraph(bullet, list_style))
#                 story.append(Spacer(1, 5))
#         else:
#             story.append(Paragraph("(Invalid content)", content_style))

#         if idx < len(slides) - 1:
#             story.append(PageBreak())

#     doc.build(story)
#     pdf_bytes = buffer.getvalue()
#     buffer.close()
#     return pdf_bytes


# # ----------------- Standalone Testing -----------------
# # if __name__ == "__main__":
# #     # Test without RAG
# #     prompt = "Explore amazon ec2"
# #     try:
# #         slide_deck = generate_slide_deck(embeddings, prompt, use_rag=False, book_name=None)
# #         print("Slide deck JSON generated successfully.")
# #         pdf_data = create_pdf_from_slides(slide_deck)
# #         with open("test_slide_deck.pdf", "wb") as f:
# #             f.write(pdf_data)
# #         print("PDF saved as test_slide_deck.pdf")
# #     except Exception as e:
# #         print("Error:", e)




# backend/slide_decks.py

import os
import io
import json
from datetime import datetime
from dotenv import load_dotenv
# from langchain_core import embeddings
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# LangChain / Groq imports
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "gemma2-9b-it"
INDEX_FOLDER = "./chroma_index"

# ----------------- Utility Functions -----------------
def normalize_book_name(book_name: str) -> str:
    """Normalize book name for folder/index usage."""
    if book_name.lower().endswith(".pdf"):
        book_name = book_name[:-4]
    return book_name.replace(" ", "_")


def load_index(embeddings, book_name: str):
    """Load Chroma index for a book."""
    normalized_name = normalize_book_name(book_name)
    index_folder = os.path.join(INDEX_FOLDER, normalized_name)
    if not os.path.exists(index_folder) or not os.listdir(index_folder):
        raise FileNotFoundError(f"No index found for book: {book_name}")
    return Chroma(persist_directory=index_folder, embedding_function=embeddings)


# ----------------- Slide Deck Generation -----------------
def generate_slide_deck(embeddings, prompt: str, use_rag: bool, book_name: str):
    if not GROQ_API_KEY:
        raise ValueError("Missing GROQ_API_KEY in environment")

    llm = ChatGroq(model=LLM_MODEL, groq_api_key=GROQ_API_KEY)

    # Retrieve RAG context if requested
    context = []
    if use_rag and book_name:
        db = load_index(embeddings, book_name)
        results = db.similarity_search(prompt, k=12)
        context = [r.page_content for r in results]

    # Build prompt
    final_prompt = f"You are a presentation slide generator.\nTopic: {prompt}\n"
    if context:
        final_prompt += "Use the following context from the book:\n" + "\n".join(context)

    final_prompt += """
Return output as valid JSON in this exact schema:
{
  "slide_deck": {
    "title": string,
    "topic": string,
    "metadata": {
      "created_at": string,
      "created_by": string,
      "total_slides": number
    },
    "slides": [
      {
        "slide_id": string,
        "slide_type": "title_slide" | "paragraph" | "unordered_list" | "ordered_list",
        "slide_title": string,
        "slide_content": string | [string]
      }
    ]
  }
}
"""

    response = llm.invoke(final_prompt)

    # Convert response to string
    raw_text = response.content if hasattr(response, "content") else str(response)
    raw_text = raw_text.strip()

    # Remove ```json or ``` code fences if present
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]  # remove first ```json line
        if lines[-1].strip() == "```":
            lines = lines[:-1]  # remove last ``` line
        raw_text = "\n".join(lines).strip()

    # Parse JSON
    try:
        slide_deck_json = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON:\n{raw_text}\nOriginal error: {str(e)}")

    return slide_deck_json


# ----------------- PDF Generation -----------------
def create_pdf_from_slides(slide_deck_data):
    """Generate a PDF from slide deck JSON with 16:9 aspect ratio"""
    width, height = 612, 612 * 9 / 16
    pagesize = (width, height)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesize,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"], fontSize=60, leading=50,
        alignment=TA_CENTER, spaceAfter=0, textColor=colors.HexColor("#9f3dff")
    )
    heading_style = ParagraphStyle(
        "CustomHeading", parent=styles["Heading1"], fontSize=30, leading=34,
        alignment=TA_CENTER, spaceAfter=15, textColor=colors.HexColor("#333333")
    )
    content_style = ParagraphStyle(
        "CustomContent", parent=styles["Normal"], fontSize=20,
        alignment=TA_LEFT, spaceAfter=12, leading=24, textColor=colors.HexColor("#666666")
    )
    list_style = ParagraphStyle(
        "ListStyle", parent=content_style, leftIndent=30,
        spaceAfter=10, leading=24, bulletIndent=15, spaceBefore=5
    )

    story = []

    # First slide: only title
    title = slide_deck_data["slide_deck"]["title"]
    story.append(Spacer(1, height / 3))
    story.append(Paragraph(title, title_style))
    story.append(PageBreak())

    # Content slides
    slides = slide_deck_data["slide_deck"]["slides"]
    for idx, slide in enumerate(slides):
        slide_title = slide.get("slide_title", "")
        story.append(Paragraph(slide_title.strip() or "(No Title)", heading_style))

        approx_title_height = 50
        remaining_height = height - approx_title_height - 60
        story.append(Spacer(1, remaining_height / 4))

        content = slide.get("slide_content")
        if isinstance(content, str):
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()] or ["(No content)"]
            for para in paragraphs:
                story.append(Paragraph(para, content_style))
                story.append(Spacer(1, 10))
        elif isinstance(content, list):
            content_items = [item.strip() for item in content if item.strip()] or ["(No content)"]
            for i, item in enumerate(content_items):
                bullet = f"• {item}" if slide["slide_type"] == "unordered_list" else f"{i+1}. {item}"
                story.append(Paragraph(bullet, list_style))
                story.append(Spacer(1, 5))
        else:
            story.append(Paragraph("(Invalid content)", content_style))

        if idx < len(slides) - 1:
            story.append(PageBreak())

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# ----------------- Standalone Testing -----------------
# if __name__ == "__main__":
#     prompt = "Introduction to Machine Learning"
#     try:
#         slide_deck = generate_slide_deck(embeddings, prompt, use_rag=False, book_name=None)
#         print("Slide deck JSON generated successfully.")
#         pdf_data = create_pdf_from_slides(slide_deck)
#         with open("test_slide_deck.pdf", "wb") as f:
#             f.write(pdf_data)
#         print("PDF saved as test_slide_deck.pdf")
#     except Exception as e:
#         print("Error:", e)
