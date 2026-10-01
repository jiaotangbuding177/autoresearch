"""Run experiments on MMLU benchmark (Multi-task Language Understanding)."""

import json
import sys
from pathlib import Path
from datetime import datetime
from datasets import load_dataset

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evolve_lab.backends import make_backend


def evaluate_mmlu_answer(choices: list, expected_idx: int, predicted: str) -> bool:
    """Evaluate MMLU answer by matching predicted choice with correct choice."""
    # Get the correct choice text
    correct_choice = choices[expected_idx]
    
    # Try to extract choice letter (A, B, C, D) from predicted response
    import re
    
    # Look for choice letter at the beginning or as a standalone answer
    predicted_upper = predicted.upper().strip()
    
    # Check if response starts with a choice letter
    for i, letter in enumerate(['A', 'B', 'C', 'D']):
        if predicted_upper.startswith(letter) or predicted_upper.startswith(f"{letter}.") or predicted_upper.startswith(f"{letter} "):
            return i == expected_idx
    
    # Check if response contains the exact correct choice text
    if correct_choice.lower() in predicted.lower():
        return True
    
    # Try to find any choice letter in the response
    for i, letter in enumerate(['A', 'B', 'C', 'D']):
        if letter in predicted_upper:
            # Found a letter, check if it's the first one
            first_letter_pos = predicted_upper.find(letter)
            for j, other_letter in enumerate(['A', 'B', 'C', 'D']):
                if j != i and predicted_upper.find(other_letter) < first_letter_pos and predicted_upper.find(other_letter) >= 0:
                    # Found another letter before this one
                    return j == expected_idx
            return i == expected_idx
    
    return False


def run_mmlu_experiment(backend_name: str = "openai", model: str = "glm-4-flash",
                       max_samples: int = 100, seeds: list[int] = [1],
                       output_file: str = None):
    """Run MMLU experiment with baseline and reflexion."""
    
    print("Loading MMLU dataset...")
    dataset = load_dataset("cais/mmlu", "all")
    test_data = dataset["test"]
    
    # Limit to max_samples if specified
    if max_samples and max_samples < len(test_data):
        test_data = test_data.select(range(max_samples))
    
    print(f"Loaded {len(test_data)} test examples")
    
    backend = make_backend(backend_name, model=model)
    
    results = {
        "experiment": "mmlu_benchmark",
        "backend": backend_name,
        "model": model,
        "timestamp": datetime.now().isoformat(),
        "max_samples": max_samples,
        "seeds": seeds,
        "results": []
    }
    
    for seed in seeds:
        print(f"\n=== Seed {seed} ===")
        
        # Baseline: Direct answering
        print("\n--- Baseline (Direct) ---")
        baseline_correct = 0
        
        for i, example in enumerate(test_data):
            question = example["question"]
            choices = example["choices"]
            expected = example["answer"]
            subject = example["subject"]
            
            # Format choices
            choices_text = "\n".join([f"{chr(65+j)}. {choice}" for j, choice in enumerate(choices)])
            
            prompt = f"""Answer the following multiple choice question.

Subject: {subject}

Question: {question}

Choices:
{choices_text}

Answer (just the letter A, B, C, or D):"""
            
            response = backend._chat(prompt)
            is_correct = evaluate_mmlu_answer(choices, expected, response)
            
            if is_correct:
                baseline_correct += 1
            
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{len(test_data)}, Correct: {baseline_correct}/{i+1} = {baseline_correct/(i+1):.2%}")
        
        baseline_accuracy = baseline_correct / len(test_data)
        print(f"\nBaseline accuracy: {baseline_correct}/{len(test_data)} = {baseline_accuracy:.2%}")
        
        # Reflexion: With self-evolution
        print("\n--- Reflexion (Self-evolution, max 3 attempts) ---")
        reflexion_correct = 0
        reflexion_attempts = []
        
        for i, example in enumerate(test_data):
            question = example["question"]
            choices = example["choices"]
            expected = example["answer"]
            subject = example["subject"]
            
            choices_text = "\n".join([f"{chr(65+j)}. {choice}" for j, choice in enumerate(choices)])
            
            reflections = []
            success = False
            attempts = 0
            
            for attempt in range(3):  # Max 3 attempts
                attempts += 1
                
                prompt = f"""Answer the following multiple choice question.

Subject: {subject}

Question: {question}

Choices:
{choices_text}
"""
                if reflections:
                    prompt += "\nPrevious attempts and feedback:\n"
                    for j, ref in enumerate(reflections, 1):
                        prompt += f"  Attempt {j}: {ref}\n"
                
                prompt += "\nAnswer (just the letter A, B, C, or D):"
                
                response = backend._chat(prompt)
                is_correct = evaluate_mmlu_answer(choices, expected, response)
                
                if is_correct:
                    success = True
                    break
                
                # Generate reflection
                correct_letter = chr(65 + expected)
                reflection_prompt = f"""Your previous answer was incorrect. Analyze why and provide guidance.

Subject: {subject}
Question: {question}
Choices: {choices_text}
Your answer: {response}
Correct answer: {correct_letter}

What went wrong? Provide a brief explanation (1-2 sentences)."""
                
                reflection = backend._chat(reflection_prompt)
                reflections.append(f"Wrong: {response[:100]}... Feedback: {reflection}")
            
            if success:
                reflexion_correct += 1
            
            reflexion_attempts.append(attempts)
            
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{len(test_data)}, Correct: {reflexion_correct}/{i+1} = {reflexion_correct/(i+1):.2%}")
        
        reflexion_accuracy = reflexion_correct / len(test_data)
        avg_attempts = sum(reflexion_attempts) / len(reflexion_attempts)
        
        print(f"\nReflexion accuracy: {reflexion_correct}/{len(test_data)} = {reflexion_accuracy:.2%}")
        print(f"Average attempts: {avg_attempts:.2f}")
        
        improvement = reflexion_accuracy - baseline_accuracy
        print(f"Improvement: {improvement:+.2%}")
        
        results["results"].append({
            "seed": seed,
            "baseline_accuracy": baseline_accuracy,
            "reflexion_accuracy": reflexion_accuracy,
            "improvement": improvement,
            "avg_attempts": avg_attempts
        })
    
    # Overall statistics
    avg_baseline = sum(r["baseline_accuracy"] for r in results["results"]) / len(results["results"])
    avg_reflexion = sum(r["reflexion_accuracy"] for r in results["results"]) / len(results["results"])
    avg_improvement = sum(r["improvement"] for r in results["results"]) / len(results["results"])
    avg_attempts = sum(r["avg_attempts"] for r in results["results"]) / len(results["results"])
    
    results["overall"] = {
        "avg_baseline_accuracy": avg_baseline,
        "avg_reflexion_accuracy": avg_reflexion,
        "avg_improvement": avg_improvement,
        "avg_attempts": avg_attempts
    }
    
    print(f"\n=== Overall Results ===")
    print(f"Baseline: {avg_baseline:.2%}")
    print(f"Reflexion: {avg_reflexion:.2%}")
    print(f"Improvement: {avg_improvement:+.2%}")
    print(f"Average attempts: {avg_attempts:.2f}")
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run MMLU benchmark experiment")
    parser.add_argument("--backend", default="openai", help="Backend name")
    parser.add_argument("--model", default="glm-4-flash", help="Model name")
    parser.add_argument("--max-samples", type=int, default=100, help="Max samples to test")
    parser.add_argument("--seeds", default="1,2,3", help="Comma-separated seeds")
    parser.add_argument("--output", default="experiments/results/mmlu_benchmark.json",
                       help="Output file")
    
    args = parser.parse_args()
    
    seeds = [int(s) for s in args.seeds.split(",")]
    
    run_mmlu_experiment(
        backend_name=args.backend,
        model=args.model,
        max_samples=args.max_samples,
        seeds=seeds,
        output_file=args.output
    )
