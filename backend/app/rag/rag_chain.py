import os
import logging
from typing import List, Dict, Any, Tuple
from backend.app.core.config import settings
from backend.app.rag.retriever import PermissionAwareRetriever, RetrievedChunk
from backend.app.prompts.banking_prompt import SYSTEM_BANKING_PROMPT, USER_QUERY_TEMPLATE
from backend.app.guardrails.output_guardrail import OutputGuardrail
from backend.app.schemas.chat import SourceCitation

logger = logging.getLogger("bankassist.rag_chain")

class RAGChain:
    """
    End-to-end Grounded RAG Generation Chain powered by Groq and Permission-Aware Retrieval.
    """

    @classmethod
    def call_groq_llm(cls, system_prompt: str, user_prompt: str) -> str:
        api_key = settings.GROQ_API_KEY
        if not api_key or api_key == "your_groq_api_key_here":
            logger.warning("GROQ_API_KEY is not configured. Using grounded deterministic generation fallback.")
            return cls._offline_grounded_generator(user_prompt)

        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=3000,
            )
            raw_text = response.choices[0].message.content.strip()
            # Clean thinking tags from reasoning models (e.g. Qwen / DeepSeek)
            import re
            if "<think>" in raw_text:
                if "</think>" in raw_text:
                    cleaned_text = raw_text.split("</think>")[-1].strip()
                else:
                    # Fallback if closing tag was truncated: search for draft/answer keywords or strip prefix
                    m = re.search(r"(?:Draft:|Based on|According to|Here is the answer:)(.*)", raw_text, re.DOTALL | re.IGNORECASE)
                    if m:
                        cleaned_text = m.group(0).strip()
                    else:
                        cleaned_text = re.sub(r"^<think>.*?\n\n", "", raw_text, flags=re.DOTALL).strip()
            else:
                cleaned_text = raw_text
            return cleaned_text or raw_text
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}. Falling back to grounded response builder.")
            return cls._offline_grounded_generator(user_prompt)

    @classmethod
    def _offline_grounded_generator(cls, user_prompt: str) -> str:
        """
        Offline fallback that extracts grounded bullet points directly from context without hallucinating.
        """
        if "CONTEXT FROM APPROVED BANKING DOCUMENTS:\n\n" in user_prompt or "CONTEXT FROM APPROVED BANKING DOCUMENTS:\n" not in user_prompt:
            return "I could not find sufficient information in the approved banking documents to answer this question."

        try:
            parts = user_prompt.split("USER QUESTION:")
            context_part = parts[0].replace("CONTEXT FROM APPROVED BANKING DOCUMENTS:", "").strip()
            
            if not context_part or len(context_part) < 20:
                return "I could not find sufficient information in the approved banking documents to answer this question."

            # Summarize the first relevant context block cleanly
            lines = [line.strip() for line in context_part.split("\n") if line.strip() and not line.startswith("---")]
            summary_points = []
            for line in lines[:5]:
                if len(line) > 15 and not line.lower().startswith("document:"):
                    summary_points.append(f"• {line}")

            if not summary_points:
                return "Based on the approved banking policy records:\n\n" + context_part[:350]

            return "Based on the retrieved banking documentation:\n\n" + "\n".join(summary_points)
        except Exception:
            return "I could not find sufficient information in the approved banking documents to answer this question."

    @classmethod
    def execute(
        cls,
        query: str,
        user_roles: List[str],
    ) -> Dict[str, Any]:
        """
        Executes the full RAG pipeline:
        1. Permission-aware retrieval
        2. Confidence threshold filtering
        3. Prompt synthesis
        4. LLM inference
        5. Output guardrails and citation compilation
        """
        # Step 1 & 2: Permission-Aware Retrieval with Threshold
        chunks: List[RetrievedChunk] = PermissionAwareRetriever.retrieve(
            query=query,
            user_roles=user_roles,
            top_k=settings.TOP_K,
            threshold=settings.RETRIEVAL_THRESHOLD
        )

        # Grounding Rule: No Retrieved Context = No Answer
        if not chunks:
            logger.info("No authorized chunks met the similarity threshold.")
            return {
                "answer": OutputGuardrail.FALLBACK_NO_INFO,
                "sources": [],
                "is_grounded": False,
                "event": "LOW_RETRIEVAL_SCORE",
                "chunks_count": 0
            }

        # Format Context
        context_blocks = []
        citations: List[SourceCitation] = []
        for idx, chunk in enumerate(chunks, 1):
            citations.append(chunk.to_citation())
            block = (
                f"--- [Document {idx}: {chunk.document_name} | Page {chunk.page_number} | Section: {chunk.section}] ---\n"
                f"{chunk.text}\n"
            )
            context_blocks.append(block)

        combined_context = "\n".join(context_blocks)
        user_prompt = USER_QUERY_TEMPLATE.format(context=combined_context, query=query)

        # Step 3: LLM Invocation
        raw_llm_answer = cls.call_groq_llm(
            system_prompt=SYSTEM_BANKING_PROMPT,
            user_prompt=user_prompt
        )

        # Step 4: Output Guardrails (PII scan, grounding check)
        guardrail_result = OutputGuardrail.validate_output(raw_llm_answer, citations)

        return {
            "answer": guardrail_result["sanitized_answer"],
            "sources": guardrail_result["sources"],
            "is_grounded": True,
            "event": guardrail_result.get("event", "LLM_GENERATION_SUCCESS"),
            "chunks_count": len(chunks)
        }
