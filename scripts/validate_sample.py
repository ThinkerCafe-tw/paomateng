#!/usr/bin/env python3
"""
Random sampling validation for time extraction quality
"""

import sys
import json
import random
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def sample_and_validate(num_samples: int = 10):
    """Sample random announcements and display for manual validation"""

    # Load data
    data_file = project_root / "data" / "master.json"
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Filter candidates that have either predicted or actual time
    candidates = []
    for ann in data:
        extracted = ann['version_history'][0]['extracted_data']
        if extracted.get('predicted_resumption_time') or extracted.get('actual_resumption_time'):
            candidates.append(ann)

    print(f"Total candidates with time data: {len(candidates)}/{len(data)}")
    print(f"Sampling {min(num_samples, len(candidates))} cases...\n")
    print("=" * 100)

    # Random sample
    samples = random.sample(candidates, min(num_samples, len(candidates)))

    for i, ann in enumerate(samples, 1):
        extracted = ann['version_history'][0]['extracted_data']
        content_text = ann['version_history'][0]['content_text']

        print(f"\n【Sample {i}】")
        print(f"ID: {ann['id']}")
        print(f"Title: {ann['title']}")
        print(f"Publish Date: {ann['publish_date']}")
        print(f"Classification: {ann['classification'].get('category', 'N/A')}")

        # Show extracted times
        predicted = extracted.get('predicted_resumption_time')
        actual = extracted.get('actual_resumption_time')

        if predicted:
            print(f"✓ Predicted: {predicted}")
        if actual:
            print(f"✓ Actual: {actual}")

        # Show relevant content snippet (first 300 chars)
        print(f"\nContent snippet:")
        print(f"{content_text[:300]}...")

        # Look for time-related keywords in content
        time_keywords = ['恢復', '復駛', '今日', '明日', '時', '首班車', '末班車', '停駛', '預計']
        relevant_sentences = []
        for sentence in content_text.split('。'):
            if any(kw in sentence for kw in time_keywords):
                relevant_sentences.append(sentence.strip())

        if relevant_sentences:
            print(f"\nTime-related sentences:")
            for sentence in relevant_sentences[:3]:  # Show first 3
                print(f"  - {sentence}")

        print("=" * 100)


if __name__ == "__main__":
    sample_and_validate(10)
