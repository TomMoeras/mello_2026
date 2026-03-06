import os
import sys
import argparse
import datetime
from typing import List, Optional

# Add the parent directory to the path so we can import the src package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.calculator import EurovisionCalculator
from src.generate_json import generate_analysis_json


def main():
    parser = argparse.ArgumentParser(description="Eurovision Prediction Calculator")
    parser.add_argument(
        "--predictions", "-p",
        required=True,
        help="Path to CSV file with predictions"
    )
    parser.add_argument(
        "--results", "-r",
        help="Path to file with actual results (one country per line, in order)"
    )
    parser.add_argument(
        "--manual-results", "-m",
        nargs="+",
        help="Manually specify the actual results (10 countries in order)"
    )
    parser.add_argument(
        "--systems", "-s",
        nargs="+",
        help="Scoring systems to calculate (default: all). Available systems: " + 
             ", ".join(f'"{name}"' for name in EurovisionCalculator.AVAILABLE_SYSTEMS.keys())
    )
    parser.add_argument(
        "--log-file", "-l",
        help="Generate a detailed log file with score breakdowns"
    )
    parser.add_argument(
        "--odds-file", "-o",
        help="Path to CSV file with bookmaker odds for calculating bonus points"
    )
    parser.add_argument(
        "--odds-factor", "-f",
        type=float,
        default=1.0,
        help="Multiplier for odds-based bonus points (default: 1.0). Increasing this value (e.g., 2.0) will award more bonus points for underdog predictions, making odds a more significant factor in the final scores. Decreasing it (e.g., 0.5) will reduce the impact of odds bonuses. Set to 0 to disable odds bonuses entirely."
    )
    parser.add_argument(
        "--json", "-j",
        nargs="?",
        const=True,
        default=True,
        help="Generate a JSON file with all data for analysis. Enabled by default. Use --no-json to disable."
    )
    parser.add_argument(
        "--no-json",
        dest="json",
        action="store_false",
        help="Disable JSON file generation"
    )
    parser.add_argument(
        "--json-dir",
        default="data",
        help="Directory to store the generated JSON file (default: data)"
    )
    
    args = parser.parse_args()
    
    # Validate scoring systems if specified
    if args.systems:
        available_systems = list(EurovisionCalculator.AVAILABLE_SYSTEMS.keys())
        invalid_systems = [system for system in args.systems if system not in available_systems]
        
        if invalid_systems:
            print(f"Error: Invalid scoring system(s): {', '.join(invalid_systems)}")
            print(f"Available scoring systems: {', '.join(available_systems)}")
            return 1
    
    # Initialize calculator with specified scoring systems and odds
    calculator = EurovisionCalculator(
        system_names=args.systems,
        odds_file=args.odds_file,
        odds_bonus_factor=args.odds_factor
    )
    
    # Load participant data
    calculator.load_data(args.predictions, args.results)
    
    # If manual results provided, use those instead
    if args.manual_results:
        calculator.set_actual_results(args.manual_results)
    
    # Check if we have results
    if not calculator.actual_results:
        print("Error: You must provide actual results either via file or manually")
        return 1
    
    # Calculate scores
    calculator.calculate_scores()
    
    # Print rankings for each scoring system
    for system_name in calculator.scoring_systems.keys():
        calculator.print_rankings(system_name)
    
    # Generate detailed log file if requested
    if args.log_file:
        calculator.write_detailed_log(args.log_file)
    
    # Generate JSON file if enabled
    if args.json:
        # Create timestamp for filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Determine the results source for the filename
        results_source = "results"
        if args.manual_results:
            results_source = "manual"
        
        # Generate JSON filename with timestamp
        json_filename = os.path.join(
            args.json_dir, 
            f"eurovision_analysis_{results_source}_{timestamp}.json"
        )
        
        # Ensure directory exists
        os.makedirs(args.json_dir, exist_ok=True)
        
        # Generate the JSON file
        if args.manual_results:
            # When using manual results
            generate_analysis_json(
                predictions_csv=args.predictions,
                results_file=None,
                actual_results=calculator.actual_results,  # Use the actual results already set in calculator
                output_file=json_filename,
                odds_file=args.odds_file,
                odds_factor=args.odds_factor,
                system_names=args.systems  # Pass the specified systems
            )
        else:
            # When using results file
            generate_analysis_json(
                predictions_csv=args.predictions,
                results_file=args.results,
                output_file=json_filename,
                odds_file=args.odds_file,
                odds_factor=args.odds_factor,
                system_names=args.systems  # Pass the specified systems
            )
        
        print(f"JSON analysis file generated: {json_filename}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 