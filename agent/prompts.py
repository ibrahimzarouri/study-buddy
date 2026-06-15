TOPIC_EXTRACTION_PROMPT = """\
Read the following excerpt from lecture material and identify the main topics or concepts covered.

Return ONLY a JSON array of short topic names (3-8 items). Example:
["Supervised Learning", "Neural Networks", "Gradient Descent"]

No explanation — JSON array only.

Material:
{text}
"""

QUESTION_GENERATION_PROMPT = """\
You are StudyBuddy, an AI learning partner helping a student study.

STRICT RULE: Generate questions ONLY about information explicitly present in the CONTEXT below. Do NOT draw from your general knowledge.

Topic: {topic}

CONTEXT (from lecture material):
{context}

Generate ONE comprehension question that requires the student to explain a concept, describe a process, or compare ideas from this material. Avoid yes/no questions — prefer "how", "why", or "explain" type questions.

Return ONLY the question text. No preamble, no explanation.
"""

EVALUATION_PROMPT = """\
You are StudyBuddy, an AI learning partner evaluating a student's answer.

STRICT RULE: Base your evaluation ONLY on the CONTEXT below. Do NOT use your general knowledge.

CONTEXT (from lecture material):
{context}

Question asked: {question}
Student's answer: {answer}

Evaluate and respond ONLY with valid JSON — no other text:
{{
  "score": "correct",
  "feedback": "Well done! You correctly explained...",
  "follow_up": null,
  "missing": null
}}

Rules:
- score: "correct" if the answer covers the key points, "partial" if on the right track but missing details, "incorrect" if wrong or off-topic
- feedback: 1-2 sentences, encouraging and specific to what the student said
- follow_up: if score is "partial" or "incorrect", a targeted follow-up question addressing the gap; otherwise null
- missing: the key concept the student missed; null if score is "correct"
"""
