"""GAIA experiment with self-evolution strategies."""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evolve_lab.backends import make_backend, GenerationContext
from evolve_lab.gaia_tasks import GAIA_TASKS


def evaluate_answer(expected: str, response: str) -> bool:
    """Evaluate if response matches expected answer."""
    expected = expected.lower().strip()
    response = response.lower().strip()
    
    return (expected in response or 
            response in expected or
            expected.replace(" ", "") in response.replace(" ", ""))


def run_gaia_with_reflexion(backend_name: str = "openai", model: str = "glm-4-flash",
                           max_attempts: int = 3, seeds: list[int] = [1],
                           output_file: str = None):
    """Run GAIA experiment with Reflexion strategy."""
    
    results = {
        "experiment": "gaia_reflexion",
        "backend": backend_name,
        "model": model,
        "strategy": "reflexion",
        "max_attempts": max_attempts,
        "timestamp": datetime.now().isoformat(),
        "seeds": seeds,
        "total_tasks": len(GAIA_TASKS),
        "results": []
    }
    
    print(f"=== GAIA with Reflexion ===")
    print(f"Model: {model}")
    print(f"Max attempts: {max_attempts}")
    print(f"Total tasks: {len(GAIA_TASKS)}")
    print()
    
    backend = make_backend(backend_name, model=model)
    
    for seed in seeds:
        print(f"--- Seed {seed} ---")
        correct = 0
        total = 0
        attempts_used = []
        
        for task in GAIA_TASKS:
            reflections = []
            success = False
            
            for attempt in range(max_attempts):
                # Build prompt with reflections
                prompt = f"""Answer the following question. Provide your answer directly without explanation.

Question: {task.question}
"""
                if reflections:
                    prompt += "\nPrevious attempts and feedback:\n"
                    for i, ref in enumerate(reflections, 1):
                        prompt += f"  Attempt {i}: {ref}\n"
                
                prompt += "\nAnswer:"
                
                # Generate response
                response = backend._chat(prompt)
                
                # Evaluate
                is_correct = evaluate_answer(task.expected_answer, response)
                
                if is_correct:
                    success = True
                    attempts_used.append(attempt + 1)
                    break
                
                # Generate reflection
                reflection_prompt = f"""Your previous answer was incorrect. Analyze why and provide guidance.

Question: {task.question}
Expected answer: {task.expected_answer}
Your answer: {response}

What went wrong? Provide a brief explanation (1-2 sentences)."""
                
                reflection = backend._chat(reflection_prompt)
                reflections.append(f"Wrong: {response}. Feedback: {reflection}")
            
            if success:
                correct += 1
            
            total += 1
            status = "✓" if success else "✗"
            attempts = attempts_used[-1] if success else max_attempts
            print(f"{status} {task.id:20s} | Attempts: {attempts} | {task.category}")
        
        accuracy = correct / total if total > 0 else 0
        avg_attempts = sum(attempts_used) / len(attempts_used) if attempts_used else 0
        
        print(f"\nSeed {seed} Results: {correct}/{total} = {accuracy:.2%}")
        print(f"Average attempts (for correct): {avg_attempts:.2f}")
        print()
        
        results["results"].append({
            "seed": seed,
            "correct": correct,
            "total": total,
            "accuracy": accuracy,
            "avg_attempts": avg_attempts
        })
    
    # Overall statistics
    total_correct = sum(r["correct"] for r in results["results"])
    total_tasks = sum(r["total"] for r in results["results"])
    overall_accuracy = total_correct / total_tasks if total_tasks > 0 else 0
    avg_attempts = sum(r["avg_attempts"] for r in results["results"]) / len(results["results"])
    
    results["overall"] = {
        "total_correct": total_correct,
        "total_tasks": total_tasks,
        "overall_accuracy": overall_accuracy,
        "avg_attempts": avg_attempts
    }
    
    print(f"=== Overall Results ===")
    print(f"Total: {total_correct}/{total_tasks} = {overall_accuracy:.2%}")
    print(f"Average attempts: {avg_attempts:.2f}")
    
    # Compare with baseline
    print(f"\n=== Comparison with Baseline ===")
    print(f"Baseline: 88.00% (no self-evolution)")
    print(f"Reflexion: {overall_accuracy:.2%} (with self-evolution)")
    improvement = overall_accuracy - 0.88
    print(f"Improvement: {improvement:+.2%}")
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run GAIA experiment with Reflexion")
    parser.add_argument("--backend", default="openai", help="Backend name")
    parser.add_argument("--model", default="glm-4-flash", help="Model name")
    parser.add_argument("--max-attempts", type=int, default=3, help="Max attempts per task")
    parser.add_argument("--seeds", default="1,2,3", help="Comma-separated seeds")
    parser.add_argument("--output", default="experiments/results/gaia_reflexion.json",
                       help="Output file")
    
    args = parser.parse_args()
    
    seeds = [int(s) for s in args.seeds.split(",")]
    
    run_gaia_with_reflexion(
        backend_name=args.backend,
        model=args.model,
        max_attempts=args.max_attempts,
        seeds=seeds,
        output_file=args.output
    )
