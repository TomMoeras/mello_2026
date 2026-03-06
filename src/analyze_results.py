#!/usr/bin/env python3
"""
Examples of how to analyze the Eurovision prediction data from the JSON file.
"""

import json
import argparse
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any


def load_data(json_file: str) -> Dict[str, Any]:
    """Load the JSON data from file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def print_basic_stats(data: Dict[str, Any]) -> None:
    """Print basic statistics about the data"""
    print("=== Basic Statistics ===")
    print(f"Number of participants: {len(data['participants'])}")
    print(f"Number of scoring systems: {len(data['scoring_systems'])}")
    print(f"Actual results (top 3): {', '.join(data['actual_results'][:3])}")
    
    # Print rankings for all scoring systems
    print("\n=== Rankings by Scoring System ===")
    for system_name, rankings in data['rankings'].items():
        print(f"\n{system_name} Rankings:")
        for rank in rankings:
            print(f"  {rank['rank']}. {rank['name']}: {rank['score']} points " +
                  f"({rank['exact_matches']} exact matches, {rank['exact_top3_matches']} in top 3)")


def analyze_predictions(data: Dict[str, Any]) -> None:
    """Analyze the predictions made by participants"""
    actual_results = data['actual_results']
    participants = data['participants']
    
    print("\n=== Prediction Analysis ===")
    
    # Count how many participants predicted each country in the top 10
    country_predictions = {}
    for country in set([c for p in participants for c in p['predictions']]):
        count = sum(1 for p in participants if country in p['predictions'])
        country_predictions[country] = count
    
    # Sort by frequency
    sorted_predictions = sorted(country_predictions.items(), key=lambda x: x[1], reverse=True)
    
    print("Most predicted countries:")
    for country, count in sorted_predictions[:5]:
        in_actual = country in actual_results
        print(f"  {country}: {count}/{len(participants)} participants " +
              f"({'correct' if in_actual else 'incorrect'})")
    
    # Countries that were in actual results but rarely predicted
    overlooked = [(c, country_predictions.get(c, 0)) for c in actual_results]
    overlooked.sort(key=lambda x: x[1])
    
    print("\nOverlooked countries (in actual results but less frequently predicted):")
    for country, count in overlooked[:3]:
        print(f"  {country}: only {count}/{len(participants)} participants predicted this country")


def analyze_odds_impact(data: Dict[str, Any]) -> None:
    """Analyze the impact of odds bonus on scores"""
    if 'odds' not in data:
        print("\nNo odds data available for analysis")
        return
    
    print("\n=== Odds Bonus Impact Analysis ===")
    
    # Analyze how much the odds bonus contributed to scores
    for system_name in data['scoring_systems'].keys():
        odds_scaling = data['scoring_systems'][system_name]['odds_scaling_factor']
        total_base = 0
        total_bonus = 0
        max_bonus = 0
        max_bonus_participant = ""
        
        for participant in data['participants']:
            breakdown = participant['breakdowns'][system_name]
            base_score = breakdown['base_score']
            odds_bonus = breakdown['odds_bonus']
            
            total_base += base_score
            total_bonus += odds_bonus
            
            if odds_bonus > max_bonus:
                max_bonus = odds_bonus
                max_bonus_participant = participant['name']
        
        avg_base = total_base / len(data['participants'])
        avg_bonus = total_bonus / len(data['participants'])
        bonus_percentage = (avg_bonus / (avg_base + avg_bonus)) * 100 if avg_base + avg_bonus > 0 else 0
        
        print(f"\n{system_name} (scaling factor: {odds_scaling}):")
        print(f"  Average base score: {avg_base:.1f}")
        print(f"  Average odds bonus: {avg_bonus:.1f} ({bonus_percentage:.1f}% of total score)")
        print(f"  Highest odds bonus: {max_bonus} points ({max_bonus_participant})")


def visualize_results(data: Dict[str, Any]) -> None:
    """Create visualizations of the results"""
    try:
        # Make sure we have matplotlib installed
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("\nVisualization requires matplotlib. Install with 'pip install matplotlib'")
        return
    
    print("\n=== Creating Visualizations ===")
    
    # Bar chart comparing scores across systems for top participants
    plt.figure(figsize=(12, 8))
    
    # Get top 3 participants from the first scoring system
    first_system = list(data['scoring_systems'].keys())[0]
    top_participants = [r['name'] for r in data['rankings'][first_system][:3]]
    
    # Prepare data for bar chart
    systems = list(data['scoring_systems'].keys())
    x = np.arange(len(systems))
    width = 0.25
    
    for i, name in enumerate(top_participants):
        participant = next(p for p in data['participants'] if p['name'] == name)
        scores = [participant['scores'][system] for system in systems]
        plt.bar(x + i*width, scores, width, label=name)
    
    plt.xlabel('Scoring System')
    plt.ylabel('Score')
    plt.title('Scores by System for Top Participants')
    plt.xticks(x + width, [s.replace(' & ', '\n& ') for s in systems], rotation=45)
    plt.legend()
    plt.tight_layout()
    
    # Save the plot
    plt.savefig('analysis_scores_comparison.png')
    print("Saved visualization to 'analysis_scores_comparison.png'")


def main():
    parser = argparse.ArgumentParser(description="Analyze Eurovision prediction results")
    parser.add_argument(
        "--json-file", "-j",
        required=True,
        help="Path to the JSON file with prediction data"
    )
    
    args = parser.parse_args()
    
    # Load data
    data = load_data(args.json_file)
    
    # Run analyses
    print_basic_stats(data)
    analyze_predictions(data)
    analyze_odds_impact(data)
    
    # Create visualizations if matplotlib is available
    try:
        visualize_results(data)
    except Exception as e:
        print(f"\nCould not create visualizations: {e}")
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main() 