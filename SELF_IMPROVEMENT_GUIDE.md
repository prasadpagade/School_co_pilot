# RAG Self-Improvement & High Accuracy Guide

## Overview

The RAG system now includes **automatic self-improvement** capabilities that continuously learn from queries and feedback to maintain high accuracy. The system tracks patterns, learns from successes and failures, and automatically optimizes itself.

## How It Works

### 1. **Automatic Quality Scoring**
Every response is automatically scored (0-1) based on:
- **Length appropriateness** (not too short/long)
- **Keyword relevance** (answer contains question keywords)
- **Specificity** (has dates, numbers, names)
- **Error detection** (no "could not find" messages)

### 2. **Pattern Learning**
The system learns query patterns by:
- **Normalizing questions** to patterns (e.g., "What is the birthday policy from Ms. Lobeda?" → "what is the [TOPIC] policy from [PERSON]?")
- **Tracking success rates** per pattern
- **Identifying low-quality patterns** for improvement
- **Learning from successful examples**

### 3. **Adaptive Prompting**
Prompts are automatically optimized based on:
- **Query category** (date/time, policy, person, location, general)
- **Historical success** for similar patterns
- **Known failure patterns** (extra instructions added)

### 4. **Continuous Optimization**
Every 10 queries, the system:
- Analyzes recent failures
- Identifies quality degradation
- Generates optimization suggestions
- Tracks accuracy trends

### 5. **Feedback Integration**
User feedback directly improves the system:
- **Helpful feedback** → High quality score (0.9)
- **Not helpful** → Low quality score (0.2)
- **Comments** → Stored for pattern analysis

## Features

### Automatic Metrics Tracking

```python
# Tracked automatically:
- Total queries
- Success rate
- Average response time
- Quality scores
- Query type distribution
- Common questions
- Accuracy trends (daily)
- Learned patterns
```

### Quality Scoring

Responses are scored on:
- ✅ **Length** (50-2000 chars ideal)
- ✅ **Keyword overlap** (30%+ question keywords in answer)
- ✅ **Specificity** (dates, numbers, names present)
- ✅ **No generic phrases** ("I don't know", etc.)
- ✅ **No error messages**

### Pattern Recognition

The system learns:
- **Query patterns** (normalized question structures)
- **Success patterns** (what works well)
- **Failure patterns** (what needs improvement)
- **Category-specific optimizations**

## Maintaining High Accuracy

### 1. **Automatic Quality Monitoring**

The system tracks:
- **Daily accuracy trends** (last 30 days)
- **Quality score trends** (last 20 responses)
- **Success rate** (should be >70%)
- **Response quality** (should be >0.6)

### 2. **Automatic Alerts**

You'll get suggestions when:
- ⚠️ Success rate drops below 70%
- ⚠️ Quality scores drop below 0.6
- ⚠️ Response times exceed 5 seconds
- ⚠️ Specific patterns have high failure rates

### 3. **Self-Optimization**

The system automatically:
- Identifies failing patterns (3+ failures)
- Suggests improvements
- Adjusts prompts based on learned patterns
- Tracks optimization history

### 4. **Feedback Loop**

User feedback directly improves accuracy:
- **Positive feedback** → Reinforces successful patterns
- **Negative feedback** → Flags patterns for improvement
- **Comments** → Provide context for failures

## API Endpoints

### Get Metrics
```bash
GET /rag/metrics
```

Returns:
```json
{
  "total_queries": 150,
  "success_rate": 85.3,
  "avg_response_time": 2.4,
  "avg_quality_score": 0.78,
  "top_questions": [...],
  "query_type_distribution": {...},
  "improvement_suggestions": [...],
  "accuracy_trend": [...],
  "learned_patterns": 45,
  "recent_optimizations": [...]
}
```

### Submit Feedback
```bash
POST /rag/feedback
Content-Type: application/json

{
  "query": "What is the birthday policy?",
  "response": "...",
  "is_helpful": true,
  "comment": "Very helpful!"
}
```

## UI Integration

Add feedback buttons to your UI:

```javascript
// After displaying answer
function addFeedbackButtons(question, answer) {
    const feedbackDiv = document.createElement('div');
    feedbackDiv.innerHTML = `
        <button onclick="submitFeedback('${question}', '${answer}', true)">👍 Helpful</button>
        <button onclick="submitFeedback('${question}', '${answer}', false)">👎 Not Helpful</button>
    `;
    // Add to chat
}

async function submitFeedback(query, response, isHelpful) {
    await fetch('/rag/feedback', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            query: query,
            response: response,
            is_helpful: isHelpful
        })
    });
}
```

## Best Practices

### 1. **Regular Monitoring**
Check metrics weekly:
```bash
curl http://localhost:8000/rag/metrics
```

### 2. **Provide Feedback**
Always provide feedback for:
- ✅ Excellent answers (reinforces good patterns)
- ❌ Poor answers (flags issues for improvement)

### 3. **Review Suggestions**
Check `improvement_suggestions` regularly:
- Address low success rates
- Fix slow response times
- Improve failing patterns

### 4. **Data Quality**
Ensure:
- ✅ Emails are properly ingested
- ✅ Attachments are transcribed
- ✅ Markdown files are up-to-date
- ✅ Files are uploaded to Gemini

## How Accuracy Improves Over Time

1. **Initial State**: System uses base prompts
2. **Learning Phase**: Tracks patterns, scores quality
3. **Optimization**: Identifies failures, adjusts prompts
4. **Refinement**: Learns from feedback, improves patterns
5. **Maturity**: High accuracy maintained automatically

## Example Learning Flow

```
Query: "What is the birthday policy?"
↓
Pattern: "what is the [TOPIC] policy?"
↓
Quality Score: 0.85 (high)
↓
Success: ✅
↓
Pattern learned as successful
↓
Future similar queries use optimized prompt
```

## Monitoring Dashboard

View metrics in real-time:
- Success rate trends
- Quality score trends
- Common questions
- Failed patterns
- Optimization suggestions

## Troubleshooting

### Low Accuracy
1. Check `improvement_suggestions` in metrics
2. Review `failed_patterns` in learning data
3. Provide feedback on poor responses
4. Check data quality (emails ingested correctly?)

### Slow Performance
1. Check `avg_response_time` in metrics
2. Review caching (responses cached?)
3. Check file sizes (too large?)
4. Review API rate limits

### Quality Degradation
1. Check `accuracy_trend` (last 7 days)
2. Review recent `confidence_scores`
3. Check for new query patterns
4. Review optimization suggestions

## Files

- `app/rag_improvement.py` - Self-improvement logic
- `data/.rag_metrics.json` - Performance metrics
- `data/.rag_feedback.json` - User feedback
- `data/.rag_learning.json` - Learned patterns

## Summary

The RAG system is now **self-intelligent** and **continuously improving**:

✅ **Automatic quality scoring** for every response
✅ **Pattern learning** from successes and failures
✅ **Adaptive prompting** based on learned patterns
✅ **Continuous optimization** every 10 queries
✅ **Feedback integration** for direct improvement
✅ **Accuracy monitoring** with automatic alerts
✅ **Trend tracking** for long-term improvement

The system gets smarter with every query and maintains high accuracy automatically!

