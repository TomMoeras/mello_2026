from typing import List, Dict, Tuple, Optional, Callable
import json
import os
from .data_loader import Participant, load_participants, load_actual_results
from .scoring import (
    ScoringSystem,
    SimpleAndSweet,
    PositionalProximityBase,
    TopHeavyPositionalProximity
)
from .odds_bonus import OddsCalculator


class EurovisionCalculator:
    """Main class for calculating Eurovision prediction scores"""
    
    # Dictionary mapping system names to their classes for easy reference
    AVAILABLE_SYSTEMS = {
        "Simple & Sweet": SimpleAndSweet,
        "Positional Proximity Base": PositionalProximityBase,
        "TopHeavyPositionalProximity": TopHeavyPositionalProximity
    }
    
    def __init__(self, system_names: Optional[List[str]] = None, odds_file: Optional[str] = None, odds_bonus_factor: float = 1.0):
        self.participants: List[Participant] = []
        self.actual_results: List[str] = []
        self.scoring_systems: Dict[str, ScoringSystem] = {}
        self.tiebreakers: List[Callable[[Participant, Participant], int]] = []
        self.odds_calculator: Optional[OddsCalculator] = None
        
        # Initialize odds calculator if odds file is provided
        if odds_file:
            self.odds_calculator = OddsCalculator(odds_file, odds_bonus_factor)
        
        # Initialize scoring systems
        self.initialize_scoring_systems(system_names)
        
        # Initialize default tiebreakers
        self.set_default_tiebreakers()
    
    def initialize_scoring_systems(self, system_names: Optional[List[str]] = None) -> None:
        """Initialize the requested scoring systems
        
        Args:
            system_names: List of system names to initialize, or None for all systems
        """
        # If no systems specified, use all available systems
        if system_names is None:
            system_names = list(self.AVAILABLE_SYSTEMS.keys())
        
        # Register each requested system
        for name in system_names:
            if name in self.AVAILABLE_SYSTEMS:
                system_class = self.AVAILABLE_SYSTEMS[name]
                scoring_system = system_class()
                
                # Set odds calculator if available
                if self.odds_calculator:
                    scoring_system.set_odds_calculator(self.odds_calculator)
                    if hasattr(scoring_system, 'odds_scaling_factor'):
                        print(f"Scaling factor for {name}: {scoring_system.odds_scaling_factor:.2f}")
                
                self.register_scoring_system(scoring_system)
            else:
                print(f"Warning: Unknown scoring system '{name}'. Available systems: {', '.join(self.AVAILABLE_SYSTEMS.keys())}")
    
    def register_scoring_system(self, system: ScoringSystem) -> None:
        """Register a scoring system to be used in the calculations"""
        self.scoring_systems[system.name] = system
    
    def set_odds_calculator(self, odds_file: str, bonus_factor: float = 1.0) -> None:
        """Set the odds calculator for all scoring systems
        
        Args:
            odds_file: Path to the odds data file
            bonus_factor: Multiplier for bonus points (default: 1.0)
        """
        self.odds_calculator = OddsCalculator(odds_file, bonus_factor)
        
        # Set for all scoring systems
        for system in self.scoring_systems.values():
            system.set_odds_calculator(self.odds_calculator)
    
    def set_default_tiebreakers(self) -> None:
        """Set the default tiebreakers"""
        # 1. Most exact positions overall
        self.tiebreakers.append(lambda p1, p2: p1.exact_matches - p2.exact_matches)
        
        # 2. Most exact positions within the actual top 3
        self.tiebreakers.append(lambda p1, p2: p1.exact_top3_matches - p2.exact_top3_matches)
        
        # 3. Early bird submission (earlier timestamp wins)
        self.tiebreakers.append(lambda p1, p2: (p2.timestamp - p1.timestamp).total_seconds())
    
    def load_data(self, participants_csv: str, results_file: Optional[str] = None) -> None:
        """Load participant data and optionally the actual results
        
        Args:
            participants_csv: Path to the CSV file with participant predictions
            results_file: Path to file with actual results, or None if not available yet
        """
        self.participants = load_participants(participants_csv)
        
        if results_file:
            self.actual_results = load_actual_results(results_file)
    
    def set_actual_results(self, results: List[str]) -> None:
        """Set the actual Eurovision results manually
        
        Args:
            results: List of countries in order of their actual finish
        """
        self.actual_results = results  # Store all countries, not just top 10
    
    def calculate_scores(self) -> None:
        """Calculate scores for all participants using all registered scoring systems"""
        if not self.actual_results:
            raise ValueError("Actual results must be set before calculating scores")
        
        for participant in self.participants:
            # Calculate score for each scoring system
            for system_name, system in self.scoring_systems.items():
                # Use calculate_score_with_odds_bonus if odds calculator is available, otherwise use calculate_score
                if self.odds_calculator and system.odds_calculator:
                    score = system.calculate_score_with_odds_bonus(participant.predictions, self.actual_results)
                else:
                    score = system.calculate_score(participant.predictions, self.actual_results)
                participant.scores[system_name] = score
            
            # Calculate tiebreaker values
            exact_positions = [i for i in range(10) if i < len(participant.predictions) and 
                              i < len(self.actual_results) and 
                              participant.predictions[i] == self.actual_results[i]]
            
            participant.exact_matches = len(exact_positions)
            participant.exact_top3_matches = sum(1 for pos in exact_positions if pos < 3)
    
    def get_rankings(self, system_name: str) -> List[Tuple[Participant, int]]:
        """Get the rankings for a specific scoring system
        
        Args:
            system_name: Name of the scoring system to rank by
            
        Returns:
            List of (participant, score) tuples sorted by score (highest first)
        """
        if system_name not in self.scoring_systems:
            raise ValueError(f"Unknown scoring system: {system_name}")
        
        # Create initial rankings based on score
        rankings = [(p, p.scores.get(system_name, 0)) for p in self.participants]
        
        # Sort by score (descending)
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        # Apply tiebreakers for equal scores
        i = 0
        while i < len(rankings) - 1:
            if rankings[i][1] == rankings[i+1][1]:
                # Found a tie, find all participants with this score
                start = i
                while i+1 < len(rankings) and rankings[i][1] == rankings[i+1][1]:
                    i += 1
                end = i
                
                # Apply tiebreakers to this group
                tied_participants = [rankings[j][0] for j in range(start, end+1)]
                tied_participants.sort(key=self._get_tiebreaker_key, reverse=True)
                
                # Replace the tied section with the new ordering
                for j in range(len(tied_participants)):
                    rankings[start+j] = (tied_participants[j], rankings[start+j][1])
            
            i += 1
        
        return rankings
    
    def _get_tiebreaker_key(self, participant: Participant) -> Tuple:
        """Create a sorting key for tiebreakers
        
        Returns a tuple of values to sort by, ordered by importance of tiebreakers
        """
        return tuple(tiebreaker(participant, participant) for tiebreaker in self.tiebreakers)
    
    def print_rankings(self, system_name: str) -> None:
        """Print the rankings for a specific scoring system
        
        Args:
            system_name: Name of the scoring system to rank by
        """
        rankings = self.get_rankings(system_name)
        
        print(f"\nRankings for {system_name}:")
        print("-" * 40)
        print(f"{'Rank':<6}{'Name':<15}{'Score':<8}{'Exact':<8}{'Top 3':<8}")
        print("-" * 40)
        
        prev_score = None
        rank = 1
        display_rank = 1
        
        for i, (participant, score) in enumerate(rankings):
            # If score is different from previous, update the rank display
            if score != prev_score:
                display_rank = rank
            
            print(f"{display_rank:<6}{participant.name:<15}{score:<8}{participant.exact_matches:<8}{participant.exact_top3_matches:<8}")
            
            prev_score = score
            rank += 1
    
    def write_detailed_log(self, log_file: str) -> None:
        """Write detailed score breakdown for all participants and scoring systems to a log file
        
        Args:
            log_file: Path to the log file
        """
        if not self.participants or not self.actual_results:
            raise ValueError("No data to log. Make sure to load participants and results first.")
        
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("# Eurovision Prediction Contest - Detailed Score Breakdown\n\n")
            
            # Write odds information if available
            if self.odds_calculator and self.odds_calculator.country_odds:
                f.write("## Bookmaker Odds\n\n")
                f.write("| Rank | Country | Median Odds |\n")
                f.write("|------|---------|-------------|\n")
                
                # Sort countries by odds
                countries_by_odds = sorted(self.odds_calculator.country_odds.items(), key=lambda x: x[1])
                for i, (country, odds) in enumerate(countries_by_odds):
                    f.write(f"| {i+1} | {country} | {odds:.2f} |\n")
                
                f.write("\n")
            
            # Write actual results
            f.write("## Actual Results\n\n")
            for i, country in enumerate(self.actual_results):
                f.write(f"{i+1}. {country}\n")
            f.write("\n")
            
            # Process each scoring system
            for system_name, system in self.scoring_systems.items():
                f.write(f"## Scoring System: {system_name}\n\n")
                f.write(f"Description: {system.description}\n\n")
                
                # Get rankings for this system
                rankings = self.get_rankings(system_name)
                
                # Process each participant
                for rank, (participant, score) in enumerate(rankings):
                    f.write(f"### {rank+1}. {participant.name} - {score} points\n\n")
                    
                    # Get detailed breakdown
                    breakdown = system.get_detailed_breakdown(participant.predictions, self.actual_results)
                    
                    # Write base score and odds bonus if applicable
                    base_score = breakdown.get("base_score", score)
                    odds_bonus = breakdown.get("odds_bonus", 0)
                    total_score = breakdown.get("total_score", score)
                    odds_scaling_factor = breakdown.get("odds_scaling_factor", 1.0)
                    
                    if odds_bonus > 0:
                        f.write(f"Base Score: {base_score} points + Odds Bonus: {odds_bonus} points = {total_score} total points\n")
                        f.write(f"(Odds scaling factor for this scoring system: {odds_scaling_factor:.2f})\n\n")
                    
                    # Write prediction vs actual
                    f.write("#### Prediction vs Actual\n\n")
                    f.write("| Position | Prediction | Actual | Points | Explanation |\n")
                    f.write("|----------|------------|--------|--------|--------------|\n")
                    
                    for detail in breakdown.get("country_details", []):
                        position = detail.get("position", "")
                        country = detail.get("country", "")
                        in_top10 = detail.get("in_top10", False)
                        
                        # Get the actual position or country
                        actual_position = detail.get("actual_position", "Not in Top 10")
                        if isinstance(actual_position, int):
                            # If it's an index, get the country at that position
                            actual_country = self.actual_results[actual_position] if 0 <= actual_position < len(self.actual_results) else "Not in Top 10"
                            actual_position_display = f"{actual_country} ({actual_position + 1})"
                        elif in_top10 and country in self.actual_results:
                            # If it's in top 10, show the country and its position
                            pos = self.actual_results.index(country) + 1
                            actual_position_display = f"{country} ({pos})"
                        else:
                            actual_position_display = actual_position
                            
                        points = detail.get("points", 0)
                        explanation = detail.get("explanation", "No points")
                        
                        f.write(f"| {position} | {country} | {actual_position_display} | {points} | {explanation} |\n")
                    
                    f.write("\n")
                    
                    # Write odds details if applicable
                    odds_details = breakdown.get("odds_details", {})
                    if odds_details and self.odds_calculator:
                        f.write("#### Odds Bonus Details\n\n")
                        f.write("| Country | Bookmaker Odds | Bonus Points |\n")
                        f.write("|---------|----------------|-------------|\n")
                        
                        for country, details in odds_details.items():
                            country_odds = details.get("odds", 0)
                            country_bonus = details.get("bonus", 0)
                            f.write(f"| {country} | {country_odds:.2f} | +{country_bonus:.1f} |\n")
                        
                        f.write("\n")
                    
                    # Write additional info based on scoring system
                    if system_name == "Simple & Sweet":
                        f.write(f"Correct countries: {breakdown.get('correct_countries', 0)} × 2 = {breakdown.get('correct_country_points', 0)} points\n")
                        f.write(f"Exact positions: {breakdown.get('exact_positions', 0)} × 3 = {breakdown.get('exact_position_points', 0)} points\n")
                    
                    f.write("\n")
                
                f.write("\n---\n\n")  # Separator between scoring systems
            
            # Write JSON version for machine processing
            f.write("## Machine-Readable Data\n\n")
            f.write("```json\n")
            
            # Prepare data for JSON serialization
            json_data = {
                "actual_results": self.actual_results,
                "participants": []
            }
            
            # Add odds data if available
            if self.odds_calculator and self.odds_calculator.country_odds:
                json_data["odds"] = {
                    country: float(odds) for country, odds in self.odds_calculator.country_odds.items()
                }
            
            for participant in self.participants:
                participant_data = {
                    "name": participant.name,
                    "predictions": participant.predictions,
                    "scores": participant.scores,
                    "breakdowns": {}
                }
                
                # Add detailed breakdowns for each scoring system
                for system_name, system in self.scoring_systems.items():
                    participant_data["breakdowns"][system_name] = system.get_detailed_breakdown(
                        participant.predictions, self.actual_results
                    )
                
                json_data["participants"].append(participant_data)
            
            # Write JSON to file
            f.write(json.dumps(json_data, indent=2))
            f.write("\n```\n")
            
            print(f"Detailed score breakdown written to {log_file}")
    
    def log_score_breakdown(self, participant: Participant, system_name: str) -> str:
        """Generate a text representation of a participant's score breakdown for a specific scoring system
        
        Args:
            participant: The participant
            system_name: Name of the scoring system
            
        Returns:
            Text description of the score breakdown
        """
        if system_name not in self.scoring_systems:
            return f"Unknown scoring system: {system_name}"
        
        system = self.scoring_systems[system_name]
        breakdown = system.get_detailed_breakdown(participant.predictions, self.actual_results)
        
        # Build a text representation
        lines = [
            f"Score Breakdown for {participant.name} - {system_name}",
            f"Total Score: {breakdown.get('total_score', 0)} points",
            ""
        ]
        
        # Add prediction vs actual
        lines.append("Prediction vs Actual:")
        lines.append("-" * 60)
        lines.append(f"{'Position':<10}{'Prediction':<15}{'Actual':<15}{'Points':<8}{'Explanation'}")
        lines.append("-" * 60)
        
        for detail in breakdown.get("country_details", []):
            position = detail.get("position", "")
            country = detail.get("country", "")
            in_top10 = detail.get("in_top10", False)
            
            # Get the actual position or country
            actual_position = detail.get("actual_position", "Not in Top 10")
            if isinstance(actual_position, int):
                # If it's an index, get the country at that position
                actual_country = self.actual_results[actual_position] if 0 <= actual_position < len(self.actual_results) else "Not in Top 10"
                actual_position_display = f"{actual_country} ({actual_position + 1})"
            elif in_top10 and country in self.actual_results:
                # If it's in top 10, show the country and its position
                pos = self.actual_results.index(country) + 1
                actual_position_display = f"{country} ({pos})"
            else:
                actual_position_display = actual_position
                
            points = detail.get("points", 0)
            explanation = detail.get("explanation", "No points")
            
            lines.append(f"{position:<10}{country:<15}{actual_position_display:<15}{points:<8}{explanation}")
        
        return "\n".join(lines) 