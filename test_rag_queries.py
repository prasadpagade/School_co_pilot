"""Test script to verify RAG queries are working correctly."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import config
from app.rag_chat import ask_school_question
import time

# Test queries
TEST_QUERIES = [
    "What is the birthday policy from Ms. Lobeda?",
    "What are the dress code guidelines?",
    "When is the next martial arts class?",
    "What are the latest announcements from Miss Lobeda?",
    "What treats can be brought for birthdays?",
]

def test_rag_queries():
    """Test multiple RAG queries."""
    print("🧪 Testing RAG Queries")
    print("=" * 80)
    
    if not config.FILE_SEARCH_STORE_NAME:
        print("❌ ERROR: FILE_SEARCH_STORE_NAME not set in .env")
        return
    
    results = []
    
    for i, question in enumerate(TEST_QUERIES, 1):
        print(f"\n📋 Test {i}/{len(TEST_QUERIES)}: {question}")
        print("-" * 80)
        
        try:
            start_time = time.time()
            answer = ask_school_question(question, config.FILE_SEARCH_STORE_NAME, use_cache=False)
            response_time = time.time() - start_time
            
            print(f"⏱️  Response time: {response_time:.2f}s")
            print(f"📝 Answer ({len(answer)} chars):")
            print(answer[:500] + ("..." if len(answer) > 500 else ""))
            
            # Check if answer is actually correct
            is_correct = True
            issues = []
            
            # Check for "not found" responses
            if "could not find" in answer.lower() or "cannot find" in answer.lower() or "does not include" in answer.lower():
                is_correct = False
                issues.append("Information not found")
            
            # Check for wrong information (e.g., wrong person, wrong topic)
            question_lower = question.lower()
            answer_lower = answer.lower()
            
            if "birthday" in question_lower and "birthday" not in answer_lower and "treat" not in answer_lower:
                is_correct = False
                issues.append("Birthday question but answer doesn't mention birthday/treats")
            
            if "lobeda" in question_lower or "lobita" in question_lower:
                if "lobeda" not in answer_lower and "lobita" not in answer_lower and "ananya" in answer_lower:
                    is_correct = False
                    issues.append("Wrong person mentioned (Ananya instead of Lobeda)")
            
            if "dress code" in question_lower:
                # For dress code, check if answer mentions it AND provides some details
                # (not just "I found mentions" without actual guidelines)
                if "dress code" not in answer_lower:
                    is_correct = False
                    issues.append("Dress code question but answer doesn't mention dress code")
                elif "i found mentions" in answer_lower and len(answer) < 500:
                    # Answer mentions dress code but might not have full details
                    # This is acceptable if it references where to find it
                    pass  # Accept this as it's providing references
            
            if is_correct:
                print("✅ PASSED: Answer seems correct")
                results.append({"question": question, "status": "passed", "answer": answer})
            else:
                print(f"❌ FAILED: {', '.join(issues)}")
                results.append({"question": question, "status": "failed", "answer": answer, "issues": issues})
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({"question": question, "status": "error", "error": str(e)})
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    
    passed = sum(1 for r in results if r.get("status") == "passed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    errors = sum(1 for r in results if r.get("status") == "error")
    
    print(f"✅ Passed: {passed}/{len(TEST_QUERIES)}")
    print(f"❌ Failed: {failed}/{len(TEST_QUERIES)}")
    print(f"⚠️  Errors: {errors}/{len(TEST_QUERIES)}")
    
    if failed > 0:
        print("\n❌ Failed Queries:")
        for r in results:
            if r.get("status") == "failed":
                print(f"  - {r['question']}")
                print(f"    Answer: {r['answer'][:100]}...")
    
    return results

if __name__ == "__main__":
    test_rag_queries()

