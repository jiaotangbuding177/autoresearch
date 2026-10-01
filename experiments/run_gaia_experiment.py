"""GAIA experiment runner: test self-evolution strategies on GAIA-style tasks."""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add experiments directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evolve_lab.backends import make_backend
from evolve_lab.gaia_tasks import GAIA_TASKS


def run_gaia_experiment(backend_name: str = "openai", model: str = "glm-4-flash", 
                       seeds: list[int] = [1], output_file: str = None):
    """Run GAIA experiment with different strategies."""
    
    results = {
        "experiment": "gaia_baseline",
        "backend": backend_name,
        "model": model,
        "timestamp": datetime.now().isoformat(),
        "seeds": seeds,
        "total_tasks": len(GAIA_TASKS),
        "results": []
    }
    
    # Test baseline (no self-evolution, just direct answering)
    print(f"=== GAIA Baseline Experiment ===")
    print(f"Model: {model}")
    print(f"Total tasks: {len(GAIA_TASKS)}")
    print()
    
    backend = make_backend(backend_name, model=model)
    
    for seed in seeds:
        print(f"--- Seed {seed} ---")
        correct = 0
        total = 0
        category_stats = {}
        
        for task in GAIA_TASKS:
            # Create a simple prompt for the task
            prompt = f"""Answer the following question. Provide your answer directly without explanation.

Question: {task.question}

Answer:"""
            
            # Generate response
            response = backend._chat(prompt)
            
            # Simple evaluation: check if expected answer is in response
            # Normalize for comparison
            expected = task.expected_answer.lower().strip()
            response_lower = response.lower().strip()
            
            # Check for exact match or contains
            is_correct = (expected in response_lower or 
                         response_lower in expected or
                         expected.replace(" ", "") in response_lower.replace(" ", ""))
            
            if is_correct:
                correct += 1
            
            total += 1
            
            # Track by category
            if task.category not in category_stats:
                category_stats[task.category] = {"correct": 0, "total": 0}
            category_stats[task.category]["total"] += 1
            if is_correct:
                category_stats[task.category]["correct"] += 1
            
            status = "✓" if is_correct else "✗"
            print(f"{status} {task.id:20s} | {task.category:12s} | Expected: {expected:15s} | Got: {response[:50]}")
        
        accuracy = correct / total if total > 0 else 0
        print(f"\nSeed {seed} Results: {correct}/{total} = {accuracy:.2%}")
        print("\nBy Category:")
        for cat, stats in category_stats.items():
            cat_acc = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            print(f"  {cat:15s}: {stats['correct']}/{stats['total']} = {cat_acc:.2%}")
        print()
        
        results["results"].append({
            "seed": seed,
            "correct": correct,
            "total": total,
            "accuracy": accuracy,
            "category_stats": category_stats
        })
    
    # Overall statistics
    total_correct = sum(r["correct"] for r in results["results"])
    total_tasks = sum(r["total"] for r in results["results"])
    overall_accuracy = total_correct / total_tasks if total_tasks > 0 else 0
    
    results["overall"] = {
        "total_correct": total_correct,
        "total_tasks": total_tasks,
        "overall_accuracy": overall_accuracy
    }
    
    print(f"=== Overall Results ===")
    print(f"Total: {total_correct}/{total_tasks} = {overall_accuracy:.2%}")
    
    # Save results
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run GAIA experiment")
    parser.add_argument("--backend", default="openai", help="Backend name")
    parser.add_argument("--model", default="glm-4-flash", help="Model name")
    parser.add_argument("--seeds", default="1,2,3", help="Comma-separated seeds")
    parser.add_argument("--output", default="experiments/results/gaia_baseline.json", 
                       help="Output file")
    
    args = parser.parse_args()
    
    seeds = [int(s) for s in args.seeds.split(",")]
    
    run_gaia_experiment(
        backend_name=args.backend,
        model=args.model,
        seeds=seeds,
        output_file=args.output
    )
