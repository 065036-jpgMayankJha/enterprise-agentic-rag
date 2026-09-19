from crew_agents import run_query
from test_questions import TEST_QUESTIONS
import time

results = []

for i, question in enumerate(TEST_QUESTIONS, 1):
    if not question.strip():
        print(f"[{i}/{len(TEST_QUESTIONS)}] Skipping empty question (edge case noted)")
        results.append({"question": question, "status": "skipped_empty"})
        continue

    print(f"\n{'='*80}")
    print(f"[{i}/{len(TEST_QUESTIONS)}] {question}")
    print('='*80)

    try:
        start = time.time()
        result = run_query(question)
        duration = round(time.time() - start, 1)
        print(f"\n--- Completed in {duration}s ---")
        results.append({"question": question, "status": "success", "duration_s": duration, "output": str(result)})
    except Exception as e:
        print(f"\n--- FAILED: {e} ---")
        results.append({"question": question, "status": "error", "error": str(e)})

print(f"\n\n{'='*80}")
print("SUMMARY")
print('='*80)
for r in results:
    print(f"{r['status'].upper():15} | {r['question']}")

success_count = sum(1 for r in results if r['status'] == 'success')
print(f"\n{success_count}/{len(TEST_QUESTIONS)} questions completed successfully")
