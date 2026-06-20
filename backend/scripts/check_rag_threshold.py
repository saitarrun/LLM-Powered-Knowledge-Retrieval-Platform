import json
import sys

THRESHOLD = 0.85

def main():
    try:
        with open("eval_results.json", "r") as f:
            results = json.load(f)
    except FileNotFoundError:
        print("Error: eval_results.json not found.")
        sys.exit(1)

    print(f"Checking against threshold of {THRESHOLD}...")
    
    passed = True
    for metric, score in results.items():
        if score < THRESHOLD:
            print(f"❌ Metric {metric} scored {score:.2f}, which is below threshold {THRESHOLD}.")
            passed = False
        else:
            print(f"✅ Metric {metric} scored {score:.2f} (Pass)")

    if not passed:
        print("\nFAILURE: One or more metrics failed to meet the required threshold.")
        sys.exit(1)
        
    print("\nSUCCESS: All RAG metrics met the quality threshold!")

if __name__ == "__main__":
    main()
