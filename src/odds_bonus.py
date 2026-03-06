"""Module for handling odds data and calculating odds-based bonus points."""

import csv
from typing import Dict, List, Optional, Tuple
import statistics
import math


class OddsCalculator:
    """Class to calculate bonus points based on betting odds."""
    
    def __init__(self, odds_file: Optional[str] = None, bonus_factor: float = 1.0):
        """Initialize the odds calculator.
        
        Args:
            odds_file: Path to the CSV file with betting odds data
            bonus_factor: Multiplier for bonus points (default: 1.0)
        """
        self.country_odds: Dict[str, float] = {}
        self.bonus_factor = bonus_factor
        
        if odds_file:
            self.load_odds_data(odds_file)
    
    def load_odds_data(self, odds_file: str) -> None:
        """Load odds data from a CSV file.
        
        Expected format:
        Country,Odds1,Odds2,...
        Sweden,1.8,1.9,...
        
        Args:
            odds_file: Path to the CSV file with betting odds data
        """
        try:
            with open(odds_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header row
                
                for row in reader:
                    if len(row) < 2:  # Need at least country and one odds value
                        continue
                    
                    country = row[0].strip()
                    if country.startswith('#'):  # Skip rows with comments
                        continue
                        
                    # Get all valid odds and calculate average
                    odds_values = []
                    for odds_str in row[1:]:
                        try:
                            odds = float(odds_str)
                            if odds > 0:
                                odds_values.append(odds)
                        except (ValueError, TypeError):
                            pass
                    
                    if odds_values:
                        # Calculate median odds (more robust than mean)
                        median_odds = statistics.median(odds_values)
                        self.country_odds[country] = median_odds
            
            print(f"Loaded odds data for {len(self.country_odds)} countries")
        except Exception as e:
            print(f"Error loading odds data: {e}")
    
    def set_manual_odds(self, country_odds: Dict[str, float]) -> None:
        """Set odds data manually.
        
        Args:
            country_odds: Dictionary mapping country names to their odds
        """
        self.country_odds = country_odds
    
    def calculate_bonus(self, country: str) -> float:
        """Calculate bonus points for correctly predicting a country.
        
        Args:
            country: The country to calculate bonus for
            
        Returns:
            Bonus points (higher if country was less expected by bookmakers)
        """
        if not self.country_odds or country not in self.country_odds:
            return 0.0
        
        # Formula: log(odds) * bonus_factor
        # This gives proportionally higher points for countries with higher odds
        # but avoids extreme differences
        odds = self.country_odds[country]
        bonus = math.log10(odds) * self.bonus_factor
        
        # Ensure minimum bonus is 1
        return max(1.0, bonus)
    
    def calculate_scaled_bonus(self, country: str, scaling_factor: float) -> float:
        """Calculate bonus points with scaling for the specific scoring system.
        
        Args:
            country: The country to calculate bonus for
            scaling_factor: A factor to scale the bonus by (based on scoring system)
            
        Returns:
            Scaled bonus points
        """
        raw_bonus = self.calculate_bonus(country)
        scaled_bonus = raw_bonus * scaling_factor
        # Print for debugging
        print(f"Country: {country}, Odds: {self.country_odds.get(country, 0):.1f}, Raw bonus: {raw_bonus:.1f}, Scaling: {scaling_factor:.2f}, Scaled: {scaled_bonus:.1f}")
        return scaled_bonus
    
    def apply_bonus_to_score(self, prediction: List[str], actual_results: List[str], base_score: int, scaling_factor: float = 1.0) -> int:
        """Apply odds-based bonus to a base score.
        
        Args:
            prediction: List of countries in predicted order
            actual_results: List of countries in actual order
            base_score: The initial score without bonus
            scaling_factor: Optional scaling factor for the bonus (default: 1.0)
            
        Returns:
            New score with bonus points added
        """
        if not self.country_odds:
            return base_score
        
        # Find correctly predicted countries
        correct_predictions = set(prediction) & set(actual_results)
        
        # Calculate total bonus
        bonus = 0
        for country in correct_predictions:
            if scaling_factor != 1.0:
                bonus += self.calculate_scaled_bonus(country, scaling_factor)
            else:
                bonus += self.calculate_bonus(country)
        
        # Round to nearest integer
        rounded_bonus = int(bonus + 0.5)
        
        # Debug output
        print(f"Total bonus before rounding: {bonus:.2f}, after rounding: {rounded_bonus}, scaling factor: {scaling_factor:.2f}")
        
        # Return base score plus rounded bonus
        return base_score + rounded_bonus
    
    def get_country_odds_list(self) -> List[Tuple[str, float]]:
        """Get all country odds sorted by odds (ascending).
        
        Returns:
            List of (country, odds) tuples sorted by odds
        """
        return sorted(self.country_odds.items(), key=lambda x: x[1])


def create_odds_data_from_table(table_file: str) -> Dict[str, float]:
    """Create odds data from a formatted table text file.
    
    Args:
        table_file: Path to the text file with formatted odds table
        
    Returns:
        Dictionary mapping country names to median odds
    """
    country_odds = {}
    
    try:
        with open(table_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # Process each line
            for line in lines:
                # Skip header lines and empty lines
                if not line.strip() or "BETSSON" in line or "chance" in line or "verified" in line:
                    continue
                
                # Try to extract country and odds
                parts = line.strip().split()
                if len(parts) < 2:
                    continue
                
                # Check if this is a country line (starts with number)
                if not parts[0].isdigit():
                    continue
                
                # Extract country name
                country_idx = -1
                for i, part in enumerate(parts):
                    if part.startswith('-'):
                        country_idx = i
                        break
                
                if country_idx == -1 or country_idx == len(parts) - 1:
                    continue
                
                country = parts[country_idx + 1]
                
                # Extract odds values
                odds_values = []
                for part in parts[country_idx + 2:]:
                    try:
                        odds = float(part)
                        if odds > 0:
                            odds_values.append(odds)
                    except (ValueError, TypeError):
                        pass
                
                if odds_values:
                    median_odds = statistics.median(odds_values)
                    country_odds[country] = median_odds
    
    except Exception as e:
        print(f"Error parsing odds table: {e}")
    
    return country_odds 