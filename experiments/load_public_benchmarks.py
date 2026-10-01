"""Test on public reasoning benchmarks: GSM8K, MMLU, ARC."""

from datasets import load_dataset
import json
from pathlib import Path


def load_public_benchmarks():
    """Load public reasoning benchmarks."""
    benchmarks = {}
    
    # 1. GSM8K - Math reasoning
    print("Loading GSM8K (math reasoning)...")
    try:
        gsm8k = load_dataset("gsm8k", "main")
        benchmarks["gsm8k"] = gsm8k
        print(f"  GSM8K loaded: {len(gsm8k['train'])} train, {len(gsm8k['test'])} test")
        print(f"  Example: {gsm8k['test'][0]}")
    except Exception as e:
        print(f"  Error loading GSM8K: {e}")
    
    # 2. MMLU - Multi-task language understanding
    print("\nLoading MMLU (multi-task understanding)...")
    try:
        mmlu = load_dataset("cais/mmlu", "all")
        benchmarks["mmlu"] = mmlu
        print(f"  MMLU loaded: {len(mmlu['test'])} test examples")
        print(f"  Example: {mmlu['test'][0]}")
    except Exception as e:
        print(f"  Error loading MMLU: {e}")
    
    # 3. ARC - AI2 Reasoning Challenge
    print("\nLoading ARC (reasoning challenge)...")
    try:
        arc = load_dataset("ai2_arc", "ARC-Challenge")
        benchmarks["arc"] = arc
        print(f"  ARC loaded: {len(arc['train'])} train, {len(arc['test'])} test")
        print(f"  Example: {arc['test'][0]}")
    except Exception as e:
        print(f"  Error loading ARC: {e}")
    
    return benchmarks


def analyze_benchmarks(benchmarks):
    """Analyze benchmark datasets."""
    print("\n=== Benchmark Analysis ===\n")
    
    for name, dataset in benchmarks.items():
        print(f"\n{name.upper()}:")
        
        if isinstance(dataset, dict):
            for split in dataset.keys():
                print(f"  {split}: {len(dataset[split])} examples")
                
                if len(dataset[split]) > 0:
                    example = dataset[split][0]
                    print(f"  Keys: {list(example.keys())}")
                    
                    # Show first example
                    if name == "gsm8k":
                        print(f"  Question: {example['question'][:100]}...")
                        print(f"  Answer: {example['answer'][:100]}...")
                    elif name == "mmlu":
                        print(f"  Question: {example['question'][:100]}...")
                        print(f"  Choices: {example['choices']}")
                        print(f"  Answer: {example['answer']}")
                    elif name == "arc":
                        print(f"  Question: {example['question'][:100]}...")
                        print(f"  Choices: {example['choices']}")
                        print(f"  Answer: {example['answerKey']}")


if __name__ == "__main__":
    benchmarks = load_public_benchmarks()
    
    if benchmarks:
        analyze_benchmarks(benchmarks)
        
        # Save dataset info
        info = {}
        for name, dataset in benchmarks.items():
            info[name] = {}
            if isinstance(dataset, dict):
                for split in dataset.keys():
                    info[name][split] = len(dataset[split])
        
        with open("experiments/results/public_benchmarks_info.json", "w") as f:
            json.dump(info, f, indent=2)
        
        print(f"\nBenchmark info saved to experiments/results/public_benchmarks_info.json")
