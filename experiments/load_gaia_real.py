"""Load and test real GAIA benchmark dataset."""

from datasets import load_dataset
import json
from pathlib import Path


def load_gaia_dataset():
    """Load GAIA dataset from Hugging Face."""
    print("Loading GAIA dataset...")
    
    # GAIA dataset is hosted on Hugging Face
    # The dataset has validation and test splits
    try:
        dataset = load_dataset("gaia-benchmark/GAIA", trust_remote_code=True)
        print(f"Dataset loaded successfully!")
        print(f"Splits: {dataset.keys()}")
        
        for split in dataset.keys():
            print(f"\n{split} split: {len(dataset[split])} examples")
            if len(dataset[split]) > 0:
                print(f"Example: {dataset[split][0]}")
        
        return dataset
    except Exception as e:
        print(f"Error loading dataset: {e}")
        print("\nTrying alternative loading method...")
        
        # Try with different configuration
        try:
            dataset = load_dataset("gaia-benchmark/GAIA", "all", trust_remote_code=True)
            print(f"Dataset loaded with 'all' config!")
            return dataset
        except Exception as e2:
            print(f"Error with alternative method: {e2}")
            return None


def analyze_gaia_dataset(dataset):
    """Analyze GAIA dataset structure and content."""
    if dataset is None:
        return
    
    print("\n=== GAIA Dataset Analysis ===\n")
    
    for split in dataset.keys():
        examples = dataset[split]
        print(f"\n{split} split: {len(examples)} examples")
        
        if len(examples) > 0:
            # Analyze first example
            example = examples[0]
            print(f"\nFirst example keys: {example.keys()}")
            print(f"\nFirst example:")
            for key, value in example.items():
                print(f"  {key}: {value if len(str(value)) < 100 else str(value)[:100] + '...'}")
            
            # Analyze task types/levels if available
            if 'Level' in example or 'level' in example:
                levels = {}
                for ex in examples:
                    level = ex.get('Level', ex.get('level', 'unknown'))
                    levels[level] = levels.get(level, 0) + 1
                print(f"\nTask levels distribution:")
                for level, count in sorted(levels.items()):
                    print(f"  Level {level}: {count} tasks")


if __name__ == "__main__":
    dataset = load_gaia_dataset()
    if dataset:
        analyze_gaia_dataset(dataset)
        
        # Save dataset info
        info = {
            "splits": {split: len(dataset[split]) for split in dataset.keys()},
        }
        
        with open("experiments/results/gaia_dataset_info.json", "w") as f:
            json.dump(info, f, indent=2)
        
        print(f"\nDataset info saved to experiments/results/gaia_dataset_info.json")
