# backend/quizes.py

import os
import requests
import json
from typing import Optional, Dict, Any

# Ensure this is set in your environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def generate_quiz(
    prompt: str,
    num_questions: int,
    difficulty: str,
    mcq_percent: int,
    rag_context: Optional[str] = None # Added for future RAG integration
) -> Dict[str, Any]:
    """
    Calls the Groq LLM to generate a quiz based on user-defined parameters.
    """
    if not GROQ_API_KEY:
        raise ValueError("Missing GROQ_API_KEY environment variable")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Calculate question mix
    num_mcq = round(num_questions * (mcq_percent / 100))
    num_short_answer = num_questions - num_mcq
    
    # === Future RAG Integration Placeholder ===
    rag_instruction = ""
    if rag_context:
        rag_instruction = f"Base the quiz strictly on the following context. Do not use external knowledge: {rag_context}\n\n"
    # ========================================

    # Construct the dynamic system prompt
    system_prompt = f"""
    You are a professional quiz generator. Your task is to create a quiz based on the user's request.
    
    # Quiz Generation Requirements
    1. The quiz must have exactly {num_questions} questions.
    2. The difficulty level must be **{difficulty}**.
    3. The question mix must be: 
       - Approximately {num_mcq} Multiple Choice Questions (MCQ)
       - Approximately {num_short_answer} Short Answer Questions
    4. Ensure the Short Answer questions require a concise, single correct answer for future automated grading.
    5. {rag_instruction}

    # Output Format
    Always return the output as a JSON object in this exact schema. The 'correct_answer' and 'explanation' fields are critical for the future grading system.
    {{
      "quiz": {{
        "title": string,
        "topic": string,
        "metadata": {{
          "difficulty": "{difficulty}",
          "num_questions": {num_questions},
          "generated_at": string (ISO8601 datetime)
        }},
        "questions": [
          {{
            "id": string (unique ID for the question),
            "type": "mcq" | "short_answer",
            "question": string,
            "options": [string] (only if type='mcq' and must have 4 options),
            "correct_answer": string (the exact correct option text for mcq, or the exact expected answer for short_answer),
            "explanation": string (A detailed explanation of the correct answer, which will be used for feedback/improvement areas.)
          }}
        ]
      }}
    }}
    Do not include any text before or after the JSON. Return only valid JSON.
    """

    payload = {
        "model": "llama-3.1-8b-instant",  # Use your preferred Groq model
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a quiz for the topic: {prompt}"}
        ],
        "temperature": 0.7,
        "max_tokens": 80000
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()

    # Extract quiz JSON text
    quiz_text = data["choices"][0]["message"]["content"]

    try:
        # Note: We keep this field, which is crucial for the future grading feature
        quiz_json = json.loads(quiz_text)
    except json.JSONDecodeError:
        raise ValueError(f"Model returned invalid JSON: {quiz_text}")

    return quiz_json