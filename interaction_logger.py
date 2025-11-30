"""
Interaction Logger for HelpfulBatBot

Captures all Q&A interactions for:
- Training data collection
- Pattern analysis (what do users ask about?)
- Quality improvement (which answers need work?)
- Feedback loop (developer corrections)

Data stored locally in JSON Lines format (.jsonl) for easy processing.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib
import logging

logger = logging.getLogger(__name__)


class InteractionLogger:
    """
    Logs bot interactions to local JSON Lines files.

    Each interaction is a single JSON object on one line, making it easy to:
    - Append new entries without loading the whole file
    - Stream/process large files line by line
    - Import into databases or analytics tools
    """

    def __init__(self, log_dir: str = "interactions"):
        """
        Initialize the interaction logger.

        Args:
            log_dir: Directory to store interaction logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Main interactions file
        self.interactions_file = self.log_dir / "interactions.jsonl"

        # Feedback file (developer corrections)
        self.feedback_file = self.log_dir / "feedback.jsonl"

        # Daily rotation for easier management
        self.daily_file = self.log_dir / f"interactions_{datetime.now().strftime('%Y-%m-%d')}.jsonl"

        logger.info(f"Interaction logger initialized: {self.log_dir}")

    def _generate_id(self, question: str, timestamp: str) -> str:
        """Generate a unique ID for an interaction"""
        content = f"{question}{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def log_interaction(
        self,
        question: str,
        answer: str,
        docs_used: List[Dict],
        confidence: float,
        response_time_ms: Optional[int] = None,
        channel: str = "local",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Log a single Q&A interaction.

        Args:
            question: User's question
            answer: Bot's response
            docs_used: Documents retrieved for context
            confidence: Bot's confidence score (0-1)
            response_time_ms: Time to generate response
            channel: Source channel (local, web, github, vscode)
            user_id: Optional user identifier (hashed for privacy)
            session_id: Optional session ID for conversation threading
            metadata: Additional metadata

        Returns:
            interaction_id: Unique ID for this interaction
        """
        timestamp = datetime.now().isoformat()
        interaction_id = self._generate_id(question, timestamp)

        interaction = {
            "id": interaction_id,
            "timestamp": timestamp,
            "channel": channel,
            "question": question,
            "answer": answer,
            "docs_used": [
                {
                    "file": doc.get("file", doc.get("path", "unknown")),
                    "chunk_id": doc.get("doc_id"),
                    "relevance_score": doc.get("score")
                }
                for doc in docs_used
            ],
            "confidence": confidence,
            "response_time_ms": response_time_ms,
            "user_id": user_id,
            "session_id": session_id,
            "metadata": metadata or {},
            "feedback": None  # Will be updated if feedback is provided
        }

        # Write to both main and daily files
        self._append_jsonl(self.interactions_file, interaction)
        self._append_jsonl(self.daily_file, interaction)

        logger.info(f"Logged interaction {interaction_id}: {question[:50]}...")

        return interaction_id

    def log_feedback(
        self,
        interaction_id: str,
        feedback_type: str,
        rating: Optional[int] = None,
        corrected_answer: Optional[str] = None,
        notes: Optional[str] = None,
        reviewer: Optional[str] = None
    ):
        """
        Log feedback for an interaction.

        Args:
            interaction_id: ID of the interaction being reviewed
            feedback_type: Type of feedback (thumbs_up, thumbs_down, correction, note)
            rating: Numeric rating (1-5)
            corrected_answer: Developer-provided better answer
            notes: Free-form notes about the interaction
            reviewer: Who provided the feedback
        """
        feedback = {
            "interaction_id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "feedback_type": feedback_type,
            "rating": rating,
            "corrected_answer": corrected_answer,
            "notes": notes,
            "reviewer": reviewer
        }

        self._append_jsonl(self.feedback_file, feedback)
        logger.info(f"Logged feedback for {interaction_id}: {feedback_type}")

    def _append_jsonl(self, filepath: Path, data: Dict):
        """Append a JSON object as a new line to a file"""
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def get_interactions(
        self,
        limit: int = 100,
        channel: Optional[str] = None,
        since: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve logged interactions.

        Args:
            limit: Maximum number to return
            channel: Filter by channel
            since: Filter by timestamp (ISO format)

        Returns:
            List of interaction records
        """
        interactions = []

        if not self.interactions_file.exists():
            return interactions

        with open(self.interactions_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    interaction = json.loads(line)

                    # Apply filters
                    if channel and interaction.get("channel") != channel:
                        continue
                    if since and interaction.get("timestamp", "") < since:
                        continue

                    interactions.append(interaction)
                except json.JSONDecodeError:
                    continue

        # Return most recent first
        interactions.reverse()
        return interactions[:limit]

    def get_stats(self) -> Dict:
        """Get statistics about logged interactions"""
        interactions = self.get_interactions(limit=10000)

        if not interactions:
            return {
                "total_interactions": 0,
                "channels": {},
                "avg_confidence": 0,
                "date_range": None
            }

        channels = {}
        confidences = []

        for i in interactions:
            channel = i.get("channel", "unknown")
            channels[channel] = channels.get(channel, 0) + 1
            if i.get("confidence"):
                confidences.append(i["confidence"])

        return {
            "total_interactions": len(interactions),
            "channels": channels,
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "date_range": {
                "earliest": interactions[-1].get("timestamp") if interactions else None,
                "latest": interactions[0].get("timestamp") if interactions else None
            }
        }

    def get_question_patterns(self, limit: int = 20) -> List[Dict]:
        """
        Analyze question patterns for insights.

        Returns common question types and topics.
        """
        interactions = self.get_interactions(limit=1000)

        # Simple keyword analysis
        keywords = {}
        for i in interactions:
            question = i.get("question", "").lower()

            # Extract key topics
            topics = ["mesh", "swarm", "solver", "boundary", "material",
                     "parallel", "units", "function", "variable", "equation",
                     "stokes", "advection", "diffusion", "visualization", "save"]

            for topic in topics:
                if topic in question:
                    keywords[topic] = keywords.get(topic, 0) + 1

        # Sort by frequency
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)

        return [{"topic": k, "count": v} for k, v in sorted_keywords[:limit]]

    def export_for_training(self, output_file: str = "training_data.jsonl"):
        """
        Export interactions in a format suitable for fine-tuning or RAG improvement.

        Creates a clean dataset with:
        - question
        - answer
        - context (docs used)
        - quality indicators (confidence, feedback)
        """
        interactions = self.get_interactions(limit=10000)
        output_path = self.log_dir / output_file

        training_records = []
        for i in interactions:
            record = {
                "question": i.get("question"),
                "answer": i.get("answer"),
                "context_files": [d.get("file") for d in i.get("docs_used", [])],
                "confidence": i.get("confidence"),
                "feedback": i.get("feedback"),
                "timestamp": i.get("timestamp")
            }
            training_records.append(record)

        with open(output_path, "w", encoding="utf-8") as f:
            for record in training_records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        logger.info(f"Exported {len(training_records)} records to {output_path}")
        return str(output_path)


# Singleton instance for easy import
_logger_instance = None


def get_logger(log_dir: str = "interactions") -> InteractionLogger:
    """Get or create the interaction logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = InteractionLogger(log_dir)
    return _logger_instance
