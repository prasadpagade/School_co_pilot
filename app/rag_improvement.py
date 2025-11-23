"""Self-improvement and learning metrics for RAG system with continuous learning."""
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import hashlib


METRICS_FILE = "data/.rag_metrics.json"
FEEDBACK_FILE = "data/.rag_feedback.json"
LEARNING_FILE = "data/.rag_learning.json"
PROMPT_HISTORY_FILE = "data/.rag_prompt_history.json"


def load_metrics() -> Dict:
    """Load RAG performance metrics."""
    if not os.path.exists(METRICS_FILE):
        return {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "query_types": defaultdict(int),
            "common_questions": defaultdict(int),
            "response_times": [],
            "improvement_suggestions": [],
            "accuracy_trends": [],
            "confidence_scores": []
        }
    
    try:
        with open(METRICS_FILE, 'r') as f:
            data = json.load(f)
            # Convert back to defaultdict for query_types
            if "query_types" in data and isinstance(data["query_types"], dict):
                data["query_types"] = defaultdict(int, data["query_types"])
            if "common_questions" in data and isinstance(data["common_questions"], dict):
                data["common_questions"] = defaultdict(int, data["common_questions"])
            return data
    except:
        return {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "query_types": defaultdict(int),
            "common_questions": defaultdict(int),
            "response_times": [],
            "improvement_suggestions": [],
            "accuracy_trends": [],
            "confidence_scores": []
        }


def save_metrics(metrics: Dict) -> None:
    """Save RAG performance metrics."""
    os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
    
    # Convert defaultdict to regular dict for JSON
    if isinstance(metrics.get("query_types"), defaultdict):
        metrics["query_types"] = dict(metrics["query_types"])
    if isinstance(metrics.get("common_questions"), defaultdict):
        metrics["common_questions"] = dict(metrics["common_questions"])
    
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)


def load_learning_data() -> Dict:
    """Load learning data (patterns, optimizations, etc.)."""
    if not os.path.exists(LEARNING_FILE):
        return {
            "query_patterns": {},
            "successful_prompts": {},
            "failed_patterns": [],
            "optimizations": [],
            "last_optimization": None,
            "prompt_variations": {}
        }
    
    try:
        with open(LEARNING_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            "query_patterns": {},
            "successful_prompts": {},
            "failed_patterns": [],
            "optimizations": [],
            "last_optimization": None,
            "prompt_variations": {}
        }


def save_learning_data(learning: Dict) -> None:
    """Save learning data."""
    os.makedirs(os.path.dirname(LEARNING_FILE), exist_ok=True)
    with open(LEARNING_FILE, 'w') as f:
        json.dump(learning, f, indent=2)


def calculate_response_quality(answer: str, question: str) -> Tuple[float, Dict]:
    """
    Calculate quality score for a response (0-1).
    
    Returns:
        (score, analysis_dict)
    """
    score = 0.5  # Base score
    analysis = {
        "length_appropriate": False,
        "contains_keywords": False,
        "not_generic": False,
        "has_specifics": False,
        "not_error": True
    }
    
    answer_lower = answer.lower()
    question_lower = question.lower()
    
    # Check for error messages
    error_indicators = [
        "could not find", "cannot find", "does not include",
        "not available", "no information", "error"
    ]
    if any(indicator in answer_lower for indicator in error_indicators):
        analysis["not_error"] = False
        return 0.0, analysis
    
    # Length check (too short or too long is bad)
    if 50 <= len(answer) <= 2000:
        score += 0.1
        analysis["length_appropriate"] = True
    
    # Check if answer contains question keywords
    question_words = set(re.findall(r'\b\w+\b', question_lower))
    answer_words = set(re.findall(r'\b\w+\b', answer_lower))
    overlap = len(question_words.intersection(answer_words))
    if overlap >= len(question_words) * 0.3:  # At least 30% keyword overlap
        score += 0.2
        analysis["contains_keywords"] = True
    
    # Check for specific details (dates, numbers, names)
    has_dates = bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\b(january|february|march|april|may|june|july|august|september|october|november|december)\b', answer_lower))
    has_numbers = bool(re.search(r'\b\d+\b', answer))
    has_names = bool(re.search(r'\b(mr|ms|miss|mrs|dr)\.?\s+[A-Z][a-z]+\b', answer))
    
    if has_dates or has_numbers or has_names:
        score += 0.2
        analysis["has_specifics"] = True
    
    # Check if answer is generic (bad)
    generic_phrases = [
        "i don't know", "i'm not sure", "please check",
        "you may want to", "it's possible that"
    ]
    if not any(phrase in answer_lower for phrase in generic_phrases):
        score += 0.1
        analysis["not_generic"] = True
    
    return min(score, 1.0), analysis


def extract_query_pattern(question: str) -> str:
    """Extract a pattern from a question for learning."""
    # Normalize question to pattern
    pattern = question.lower()
    
    # Replace specific names with placeholders
    pattern = re.sub(r'\b(mr|ms|miss|mrs|dr)\.?\s+[A-Z][a-z]+\b', '[PERSON]', pattern)
    
    # Replace dates with placeholder
    pattern = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '[DATE]', pattern)
    pattern = re.sub(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b', '[DATE]', pattern)
    
    # Replace specific numbers with placeholder
    pattern = re.sub(r'\b\d+\b', '[NUMBER]', pattern)
    
    return pattern


def track_query(question: str, answer: str, response_time: float, success: bool = True, 
                quality_score: Optional[float] = None, auto_score: bool = True):
    """
    Track a query for learning and improvement with enhanced metrics.
    
    Args:
        question: The question asked
        answer: The answer provided
        response_time: Response time in seconds
        success: Whether the query was successful
        quality_score: Optional manual quality score (0-1)
        auto_score: If True, automatically calculate quality score
    """
    metrics = load_metrics()
    learning = load_learning_data()
    
    # Basic metrics
    metrics["total_queries"] += 1
    if success:
        metrics["successful_queries"] += 1
    else:
        metrics["failed_queries"] += 1
    
    # Calculate quality score
    if quality_score is None and auto_score:
        quality_score, quality_analysis = calculate_response_quality(answer, question)
        metrics["confidence_scores"].append({
            "timestamp": datetime.now().isoformat(),
            "score": quality_score,
            "question": question[:100],
            "analysis": quality_analysis
        })
        # Keep last 100 confidence scores
        if len(metrics["confidence_scores"]) > 100:
            metrics["confidence_scores"] = metrics["confidence_scores"][-100:]
    elif quality_score is not None:
        metrics["confidence_scores"].append({
            "timestamp": datetime.now().isoformat(),
            "score": quality_score,
            "question": question[:100]
        })
    
    # Track common questions
    question_lower = question.lower().strip()
    metrics["common_questions"][question_lower] = metrics["common_questions"].get(question_lower, 0) + 1
    
    # Extract and track query pattern
    pattern = extract_query_pattern(question)
    if pattern not in learning["query_patterns"]:
        learning["query_patterns"][pattern] = {
            "count": 0,
            "success_count": 0,
            "avg_quality": 0.0,
            "avg_response_time": 0.0,
            "examples": []
        }
    
    pattern_data = learning["query_patterns"][pattern]
    pattern_data["count"] += 1
    if success:
        pattern_data["success_count"] += 1
    
    # Update averages
    current_avg_quality = pattern_data["avg_quality"]
    pattern_data["avg_quality"] = (current_avg_quality * (pattern_data["count"] - 1) + (quality_score or 0.5)) / pattern_data["count"]
    
    current_avg_time = pattern_data["avg_response_time"]
    pattern_data["avg_response_time"] = (current_avg_time * (pattern_data["count"] - 1) + response_time) / pattern_data["count"]
    
    # Keep example questions (up to 5)
    if len(pattern_data["examples"]) < 5:
        pattern_data["examples"].append(question)
    elif success and quality_score and quality_score > 0.7:
        # Replace a lower-quality example
        pattern_data["examples"] = pattern_data["examples"][1:] + [question]
    
    # Categorize query type
    question_lower = question.lower()
    if any(word in question_lower for word in ["when", "date", "time", "schedule", "next"]):
        metrics["query_types"]["date_time"] = metrics["query_types"].get("date_time", 0) + 1
        query_category = "date_time"
    elif any(word in question_lower for word in ["what", "policy", "rule", "guideline", "can", "should"]):
        metrics["query_types"]["policy"] = metrics["query_types"].get("policy", 0) + 1
        query_category = "policy"
    elif any(word in question_lower for word in ["who", "teacher", "miss", "ms", "mr", "from"]):
        metrics["query_types"]["person"] = metrics["query_types"].get("person", 0) + 1
        query_category = "person"
    elif any(word in question_lower for word in ["where", "location", "place"]):
        metrics["query_types"]["location"] = metrics["query_types"].get("location", 0) + 1
        query_category = "location"
    else:
        metrics["query_types"]["general"] = metrics["query_types"].get("general", 0) + 1
        query_category = "general"
    
    # Track response time
    metrics["response_times"].append(response_time)
    if len(metrics["response_times"]) > 100:
        metrics["response_times"] = metrics["response_times"][-100:]
    
    # Track accuracy trend (daily)
    today = datetime.now().date().isoformat()
    if not metrics.get("accuracy_trends"):
        metrics["accuracy_trends"] = []
    
    # Find or create today's entry
    today_entry = None
    for entry in metrics["accuracy_trends"]:
        if entry.get("date") == today:
            today_entry = entry
            break
    
    if not today_entry:
        today_entry = {"date": today, "total": 0, "successful": 0, "avg_quality": 0.0}
        metrics["accuracy_trends"].append(today_entry)
    
    today_entry["total"] += 1
    if success:
        today_entry["successful"] += 1
    
    # Update average quality for today
    current_avg = today_entry["avg_quality"]
    today_entry["avg_quality"] = (current_avg * (today_entry["total"] - 1) + (quality_score or 0.5)) / today_entry["total"]
    
    # Keep last 30 days
    if len(metrics["accuracy_trends"]) > 30:
        metrics["accuracy_trends"] = metrics["accuracy_trends"][-30:]
    
    # Learn from failures
    if not success or (quality_score and quality_score < 0.5):
        learning["failed_patterns"].append({
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer[:200],
            "pattern": pattern,
            "category": query_category,
            "quality_score": quality_score
        })
        # Keep last 50 failures
        if len(learning["failed_patterns"]) > 50:
            learning["failed_patterns"] = learning["failed_patterns"][-50:]
    
    # Learn from successes
    if success and quality_score and quality_score > 0.8:
        pattern_key = f"{pattern}_{query_category}"
        if pattern_key not in learning["successful_prompts"]:
            learning["successful_prompts"][pattern_key] = []
        
        learning["successful_prompts"][pattern_key].append({
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer_preview": answer[:200],
            "quality_score": quality_score
        })
        # Keep last 10 successful examples per pattern
        if len(learning["successful_prompts"][pattern_key]) > 10:
            learning["successful_prompts"][pattern_key] = learning["successful_prompts"][pattern_key][-10:]
    
    save_metrics(metrics)
    save_learning_data(learning)
    
    # Auto-optimize if needed
    if metrics["total_queries"] % 10 == 0:  # Every 10 queries
        auto_optimize()


def auto_optimize():
    """Automatically optimize the system based on learning data."""
    learning = load_learning_data()
    metrics = load_metrics()
    
    optimizations = []
    
    # Analyze failed patterns
    if learning["failed_patterns"]:
        recent_failures = learning["failed_patterns"][-10:]  # Last 10 failures
        
        # Group by pattern
        failure_by_pattern = defaultdict(list)
        for failure in recent_failures:
            failure_by_pattern[failure["pattern"]].append(failure)
        
        # Find patterns with high failure rate
        for pattern, failures in failure_by_pattern.items():
            if len(failures) >= 3:  # 3+ failures for same pattern
                optimizations.append({
                    "type": "pattern_failure",
                    "pattern": pattern,
                    "failures": len(failures),
                    "suggestion": f"Pattern '{pattern}' has {len(failures)} recent failures. Consider improving search strategy for this pattern."
                })
    
    # Analyze quality trends
    if metrics.get("confidence_scores"):
        recent_scores = [s["score"] for s in metrics["confidence_scores"][-20:]]  # Last 20
        avg_recent = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        
        if avg_recent < 0.6:
            optimizations.append({
                "type": "quality_degradation",
                "avg_quality": avg_recent,
                "suggestion": f"Recent response quality is low ({avg_recent:.2f}). Consider reviewing prompt or data quality."
            })
    
    # Analyze response times
    if metrics.get("response_times"):
        recent_times = metrics["response_times"][-20:]
        avg_time = sum(recent_times) / len(recent_times) if recent_times else 0
        
        if avg_time > 5.0:
            optimizations.append({
                "type": "performance",
                "avg_time": avg_time,
                "suggestion": f"Response times are slow ({avg_time:.1f}s). Consider optimizing queries or caching."
            })
    
    if optimizations:
        learning["optimizations"].extend(optimizations)
        learning["last_optimization"] = datetime.now().isoformat()
        # Keep last 20 optimizations
        if len(learning["optimizations"]) > 20:
            learning["optimizations"] = learning["optimizations"][-20:]
        
        save_learning_data(learning)


def get_optimized_prompt_base(question: str) -> str:
    """
    Get an optimized prompt base based on learned patterns.
    
    Returns:
        Enhanced prompt instructions based on query pattern
    """
    learning = load_learning_data()
    pattern = extract_query_pattern(question)
    
    # Check if we have successful examples for this pattern
    question_lower = question.lower()
    
    # Determine query category
    if any(word in question_lower for word in ["when", "date", "time", "schedule", "next"]):
        category = "date_time"
        base_instruction = "Focus on extracting specific dates, times, and scheduling information. Be precise with dates and times."
    elif any(word in question_lower for word in ["what", "policy", "rule", "guideline"]):
        category = "policy"
        base_instruction = "Focus on extracting complete policy information. Include all requirements, restrictions, and details. Do not just mention that policies exist - extract the actual policy content."
    elif any(word in question_lower for word in ["who", "teacher", "miss", "ms", "mr", "from"]):
        category = "person"
        base_instruction = "Focus on identifying the person mentioned and extracting information FROM that person. Look for sender fields and email headers."
    else:
        category = "general"
        base_instruction = "Provide complete, specific information from the emails."
    
    # Check for learned optimizations for this pattern
    pattern_key = f"{pattern}_{category}"
    if pattern_key in learning["successful_prompts"]:
        # We have successful examples - use similar approach
        return base_instruction + " Use the same detailed extraction approach that worked for similar questions."
    
    # Check for known failures
    recent_failures = [f for f in learning["failed_patterns"][-20:] if f["pattern"] == pattern]
    if recent_failures:
        return base_instruction + " IMPORTANT: Previous similar questions had low quality. Search more thoroughly and extract complete information."
    
    return base_instruction


def record_feedback(question: str, answer: str, helpful: bool, user_comment: Optional[str] = None):
    """Record user feedback on a response."""
    feedback = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer": answer[:500],
        "helpful": helpful,
        "comment": user_comment
    }
    
    if not os.path.exists(FEEDBACK_FILE):
        feedback_list = []
    else:
        try:
            with open(FEEDBACK_FILE, 'r') as f:
                feedback_list = json.load(f)
        except:
            feedback_list = []
    
    feedback_list.append(feedback)
    
    # Keep last 100 feedback entries
    if len(feedback_list) > 100:
        feedback_list = feedback_list[-100:]
    
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(feedback_list, f, indent=2)
    
    # Update metrics based on feedback
    metrics = load_metrics()
    quality_score = 0.9 if helpful else 0.2
    track_query(question, answer, 0, success=helpful, quality_score=quality_score, auto_score=False)


def get_improvement_suggestions() -> List[str]:
    """Analyze metrics and generate improvement suggestions."""
    metrics = load_metrics()
    learning = load_learning_data()
    suggestions = []
    
    if metrics["total_queries"] == 0:
        return ["No queries yet. Start asking questions to generate insights!"]
    
    # Success rate
    success_rate = metrics["successful_queries"] / metrics["total_queries"] * 100
    if success_rate < 70:
        suggestions.append(f"⚠️ Low success rate ({success_rate:.1f}%). Consider improving search prompts or data quality.")
    elif success_rate > 90:
        suggestions.append(f"✅ Excellent success rate ({success_rate:.1f}%)! System is performing well.")
    
    # Quality scores
    if metrics.get("confidence_scores"):
        recent_scores = [s["score"] for s in metrics["confidence_scores"][-20:]]
        avg_quality = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        if avg_quality < 0.6:
            suggestions.append(f"📉 Low response quality ({avg_quality:.2f}). Review failed queries and improve prompts.")
        elif avg_quality > 0.8:
            suggestions.append(f"📈 High response quality ({avg_quality:.2f}). System is learning well!")
    
    # Common questions
    common = sorted(metrics["common_questions"].items(), key=lambda x: x[1], reverse=True)[:5]
    if common:
        suggestions.append(f"📊 Most common questions: {', '.join([q[:30] for q, _ in common])}")
    
    # Response times
    if metrics["response_times"]:
        avg_time = sum(metrics["response_times"]) / len(metrics["response_times"])
        if avg_time > 5.0:
            suggestions.append(f"⏱️ Average response time is {avg_time:.1f}s. Consider optimizing queries.")
        elif avg_time < 2.0:
            suggestions.append(f"⚡ Fast response times ({avg_time:.1f}s). Great performance!")
    
    # Recent optimizations
    if learning.get("optimizations"):
        recent_opt = learning["optimizations"][-3:]
        for opt in recent_opt:
            suggestions.append(f"🔧 {opt.get('suggestion', 'Optimization available')}")
    
    # Pattern analysis
    if learning.get("query_patterns"):
        low_quality_patterns = [
            (p, d) for p, d in learning["query_patterns"].items()
            if d["count"] >= 3 and d["avg_quality"] < 0.5
        ]
        if low_quality_patterns:
            suggestions.append(f"⚠️ {len(low_quality_patterns)} query patterns have low quality. Consider improving handling for these patterns.")
    
    return suggestions


def get_metrics_summary() -> Dict:
    """Get summary of RAG performance metrics."""
    metrics = load_metrics()
    learning = load_learning_data()
    
    if metrics["total_queries"] == 0:
        return {
            "total_queries": 0,
            "success_rate": 0,
            "avg_response_time": 0,
            "avg_quality_score": 0,
            "top_questions": [],
            "query_type_distribution": {},
            "improvement_suggestions": [],
            "accuracy_trend": []
        }
    
    success_rate = (metrics["successful_queries"] / metrics["total_queries"] * 100) if metrics["total_queries"] > 0 else 0
    avg_response_time = (sum(metrics["response_times"]) / len(metrics["response_times"])) if metrics["response_times"] else 0
    
    # Calculate average quality score
    avg_quality = 0.0
    if metrics.get("confidence_scores"):
        recent_scores = [s["score"] for s in metrics["confidence_scores"][-20:]]
        avg_quality = sum(recent_scores) / len(recent_scores) if recent_scores else 0
    
    top_questions = sorted(
        metrics["common_questions"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    # Calculate accuracy trend (last 7 days)
    accuracy_trend = []
    if metrics.get("accuracy_trends"):
        for entry in metrics["accuracy_trends"][-7:]:
            accuracy_trend.append({
                "date": entry["date"],
                "success_rate": (entry["successful"] / entry["total"] * 100) if entry["total"] > 0 else 0,
                "avg_quality": entry.get("avg_quality", 0)
            })
    
    return {
        "total_queries": metrics["total_queries"],
        "successful_queries": metrics["successful_queries"],
        "failed_queries": metrics["failed_queries"],
        "success_rate": round(success_rate, 1),
        "avg_response_time": round(avg_response_time, 2),
        "avg_quality_score": round(avg_quality, 2),
        "top_questions": [{"question": q, "count": c} for q, c in top_questions],
        "query_type_distribution": dict(metrics["query_types"]) if isinstance(metrics["query_types"], defaultdict) else metrics["query_types"],
        "improvement_suggestions": get_improvement_suggestions(),
        "accuracy_trend": accuracy_trend,
        "learned_patterns": len(learning.get("query_patterns", {})),
        "recent_optimizations": learning.get("optimizations", [])[-5:]
    }


def get_rag_metrics() -> Dict:
    """Get RAG performance metrics (alias for compatibility)."""
    return get_metrics_summary()


def submit_feedback(query: str, response: str, is_helpful: bool, comment: Optional[str] = None):
    """Submit feedback on RAG responses."""
    record_feedback(query, response, is_helpful, comment)
