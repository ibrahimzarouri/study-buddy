import json
import os
import re

from openai import OpenAI

from agent.prompts import EVALUATION_PROMPT, QUESTION_GENERATION_PROMPT, TOPIC_EXTRACTION_PROMPT
from tools.rag import RAGIndex


def _strip_thinking(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _parse_json(text: str):
    text = _strip_thinking(text)
    text = re.sub(r"```(?:json)?\s*", "", text).strip("`").strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    for pat in (r"\{[\s\S]*\}", r"\[[\s\S]*\]"):
        m = re.search(pat, text)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return None


class StudyBuddyAgent:
    def __init__(self, text: str, rag: RAGIndex):
        self.text = text
        self.rag = rag
        self.client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL", "https://chat-ai.academiccloud.de/v1"),
        )
        self.model = os.getenv("MODEL", "qwen3-coder-30b-a3b-instruct")
        self.current_question: str | None = None
        self.current_topic: str | None = None
        self.follow_up_count: int = 0
        self.max_follow_ups: int = 2

    def _complete(self, messages: list) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return resp.choices[0].message.content or ""

    def extract_topics(self) -> list[str]:
        sample = self.text[:4000]
        raw = self._complete(
            [{"role": "user", "content": TOPIC_EXTRACTION_PROMPT.format(text=sample)}]
        )
        parsed = _parse_json(raw)
        if isinstance(parsed, list):
            return [str(t) for t in parsed if t][:8]
        # Fallback: pull non-empty lines that look like topic names
        lines = [
            l.strip().strip('",-[]').strip()
            for l in _strip_thinking(raw).splitlines()
            if l.strip()
        ]
        return [l for l in lines if 3 < len(l) < 80][:8] or ["Main Content"]

    def start_topic(self, topic: str) -> str:
        self.current_topic = topic
        self.follow_up_count = 0
        context = self.rag.retrieve(topic, k=4)
        prompt = QUESTION_GENERATION_PROMPT.format(topic=topic, context=context)
        q = _strip_thinking(self._complete([{"role": "user", "content": prompt}]))
        self.current_question = q
        return q

    def evaluate_answer(self, student_answer: str) -> dict:
        context = self.rag.retrieve(
            f"{self.current_question} {student_answer}", k=5
        )
        prompt = EVALUATION_PROMPT.format(
            context=context,
            question=self.current_question,
            answer=student_answer,
        )
        raw = self._complete(
            [{"role": "user", "content": prompt}]
        )
        parsed = _parse_json(raw)

        if not isinstance(parsed, dict):
            parsed = {
                "score": "partial",
                "feedback": _strip_thinking(raw)[:300] or "Please try again with more detail.",
                "follow_up": "Can you elaborate on that?",
                "missing": None,
            }

        # Enforce follow-up limit before deciding to show one
        if self.follow_up_count >= self.max_follow_ups:
            parsed["follow_up"] = None

        if parsed.get("follow_up") and parsed.get("score") in ("partial", "incorrect"):
            self.follow_up_count += 1
            self.current_question = parsed["follow_up"]

        return parsed

    def next_question(self) -> str:
        self.follow_up_count = 0
        context = self.rag.retrieve(self.current_topic or "", k=4)
        prompt = QUESTION_GENERATION_PROMPT.format(
            topic=self.current_topic or "the material",
            context=context,
        )
        q = _strip_thinking(self._complete([{"role": "user", "content": prompt}]))
        self.current_question = q
        return q
