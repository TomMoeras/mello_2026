#!/usr/bin/env python3
"""
Generate a standalone JSON file with all Eurovision prediction data for analysis.
"""

import os
import sys
import json
import argparse
import datetime
from typing import Dict, Any, List, Optional

# Add the parent directory to the path so we can import the src package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.calculator import EurovisionCalculator


def generate_analysis_json(
    predictions_csv: str,
    output_file: str,
    results_file: Optional[str] = None,
    actual_results: Optional[List[str]] = None,
    odds_file: Optional[str] = None,
    odds_factor: float = 1.0,
    system_names: Optional[List[str]] = None
) -> None:
    """
    Generate a comprehensive JSON file with all prediction data.
    
    Args:
        predictions_csv: Path to CSV file with predictions
        output_file: Path to output JSON file
        results_file: Path to file with actual results (optional, either this or actual_results must be provided)
        actual_results: List of countries in actual result order (optional, used when results_file is not available)
        odds_file: Path to CSV file with bookmaker odds (optional)
        odds_factor: Multiplier for odds-based bonus points (default: 1.0)
        system_names: List of scoring systems to use (default: all available systems)
    """
    # Validate system names if specified
    if system_names:
        available_systems = list(EurovisionCalculator.AVAILABLE_SYSTEMS.keys())
        invalid_systems = [system for system in system_names if system not in available_systems]
        
        if invalid_systems:
            raise ValueError(f"Invalid scoring system(s): {', '.join(invalid_systems)}. "
                            f"Available systems: {', '.join(available_systems)}")
    
    # Initialize calculator with specified scoring systems and odds
    calculator = EurovisionCalculator(
        system_names=system_names,  # Use specified systems or all if None
        odds_file=odds_file,
        odds_bonus_factor=odds_factor
    )
    
    # Load participant data and results from file if available
    if results_file:
        calculator.load_data(predictions_csv, results_file)
    else:
        # Just load participants without results
        calculator.load_data(predictions_csv, None)
        
        # Set manual results if provided
        if actual_results:
            calculator.set_actual_results(actual_results)
        else:
            raise ValueError("Either results_file or actual_results must be provided")
    
    # Calculate scores
    calculator.calculate_scores()
    
    # Prepare data for JSON serialization
    json_data = {
        "metadata": {
            "generated_at": datetime.datetime.now().isoformat(),
            "predictions_csv": predictions_csv,
            "results_file": results_file,
            "actual_results_manual": actual_results is not None,
            "odds_file": odds_file,
            "odds_factor": odds_factor
        },
        "actual_results": calculator.actual_results,
        "scoring_systems": {},
        "participants": []
    }
    
    # Add details about scoring systems
    for system_name, system in calculator.scoring_systems.items():
        json_data["scoring_systems"][system_name] = {
            "description": system.description,
            "odds_scaling_factor": getattr(system, "odds_scaling_factor", 1.0)
        }
    
    # Add odds data if available
    if calculator.odds_calculator and calculator.odds_calculator.country_odds:
        json_data["odds"] = {
            country: float(odds) 
            for country, odds in calculator.odds_calculator.country_odds.items()
        }
        
        # Add sorted list of countries by odds for convenience
        json_data["countries_by_odds"] = [
            {"country": country, "odds": float(odds)}
            for country, odds in sorted(calculator.odds_calculator.country_odds.items(), 
                                        key=lambda x: x[1])
        ]
    
    # Add rankings for each scoring system
    json_data["rankings"] = {}
    for system_name in calculator.scoring_systems.keys():
        rankings = calculator.get_rankings(system_name)
        json_data["rankings"][system_name] = [
            {
                "rank": i+1,
                "name": participant.name,
                "score": score,
                "exact_matches": participant.exact_matches,
                "exact_top3_matches": participant.exact_top3_matches
            }
            for i, (participant, score) in enumerate(rankings)
        ]
    
    # Add detailed data for each participant
    for participant in calculator.participants:
        participant_data = {
            "name": participant.name,
            "timestamp": participant.timestamp.isoformat(),
            "predictions": participant.predictions,
            "scores": participant.scores,
            "exact_matches": participant.exact_matches,
            "exact_top3_matches": participant.exact_top3_matches,
            "breakdowns": {}
        }
        
        # Add detailed breakdowns for each scoring system
        for system_name, system in calculator.scoring_systems.items():
            participant_data["breakdowns"][system_name] = system.get_detailed_breakdown(
                participant.predictions, calculator.actual_results
            )
        
        json_data["participants"].append(participant_data)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write pretty-printed JSON to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str)
    
    print(f"Analysis JSON file generated: {output_file}")
    print(f"File size: {os.path.getsize(output_file) / 1024:.2f} KB")


def main():
    parser = argparse.ArgumentParser(description="Generate Eurovision prediction analysis JSON file")
    parser.add_argument(
        "--predictions", "-p",
        required=True,
        help="Path to CSV file with predictions"
    )
    parser.add_argument(
        "--results", "-r",
        required=True,
        help="Path to file with actual results (one country per line, in order)"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path to output JSON file"
    )
    parser.add_argument(
        "--odds-file",
        help="Path to CSV file with bookmaker odds for calculating bonus points"
    )
    parser.add_argument(
        "--odds-factor",
        type=float,
        default=1.0,
        help="Multiplier for odds-based bonus points (default: 1.0)"
    )
    parser.add_argument(
        "--systems", "-s",
        nargs="+",
        help="Scoring systems to calculate (default: all). Available systems: " + 
             ", ".join(f'"{name}"' for name in EurovisionCalculator.AVAILABLE_SYSTEMS.keys())
    )
    
    args = parser.parse_args()
    
    # Validate scoring systems if specified
    if args.systems:
        available_systems = list(EurovisionCalculator.AVAILABLE_SYSTEMS.keys())
        invalid_systems = [system for system in args.systems if system not in available_systems]
        
        if invalid_systems:
            print(f"Error: Invalid scoring system(s): {', '.join(invalid_systems)}")
            print(f"Available scoring systems: {', '.join(available_systems)}")
            sys.exit(1)
    
    generate_analysis_json(
        predictions_csv=args.predictions,
        results_file=args.results,
        output_file=args.output,
        odds_file=args.odds_file,
        odds_factor=args.odds_factor,
        system_names=args.systems
    )


if __name__ == "__main__":
    main() 