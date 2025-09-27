# backend/quizes.py

import os
import requests
import json
import datetime
from typing import Optional, Dict, Any, List

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
    (This function remains the same as the previous version)
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
    Always return the output as a JSON object in this exact schema. The 'correct_answer' and 'explanation' fields are critical for the grading system.
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
        "max_tokens": 8000
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()

    # Extract quiz JSON text
    quiz_text = data["choices"][0]["message"]["content"]

    try:
        quiz_json = json.loads(quiz_text)
        # Ensure 'generated_at' is present for completeness
        if 'metadata' in quiz_json['quiz']:
            quiz_json['quiz']['metadata']['generated_at'] = datetime.datetime.now().isoformat()
    except json.JSONDecodeError:
        raise ValueError(f"Model returned invalid JSON: {quiz_text}")

    return quiz_json

# =========================================================
# NEW GRADING FUNCTION
# =========================================================

def grade_quiz(quiz_data: Dict[str, Any], user_answers: Dict[str, str]) -> Dict[str, Any]:
    """
    Compares user answers against the correct answers and generates feedback.
    
    For short answer questions, a simple string comparison is used.
    For more advanced short answer grading (semantic comparison), 
    you would use the LLM to compare the user's answer against the correct_answer field.
    """
    graded_results: List[Dict[str, Any]] = []
    total_questions = 0
    correct_count = 0

    for q in quiz_data['quiz']['questions']:
        q_id = q['id']
        total_questions += 1
        user_answer = user_answers.get(f"answer-{q_id}", "").strip()
        correct_answer = q['correct_answer'].strip()
        is_correct = False
        
        # Simple grading logic
        if q['type'] == 'mcq':
            # Case-insensitive comparison for MCQs
            is_correct = (user_answer.lower() == correct_answer.lower())
        
        elif q['type'] == 'short_answer':
            # Case-insensitive comparison for short answers for now.
            # This should be replaced with an LLM call for semantic grading later.
            is_correct = (user_answer.lower() == correct_answer.lower())
            
        # Compile results for the question
        graded_results.append({
            'id': q_id,
            'is_correct': is_correct,
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'explanation': q['explanation']
        })
        
        if is_correct:
            correct_count += 1
            
    # Compile the final score and results
    return {
        'status': 'graded',
        'score': f"{correct_count}/{total_questions}",
        'percent': round((correct_count / total_questions) * 100) if total_questions > 0 else 0,
        'results': graded_results
    }