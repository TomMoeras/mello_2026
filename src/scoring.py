from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Set, Any, Optional


class ScoringSystem(ABC):
    """Base class for all Eurovision scoring systems"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.odds_calculator = None  # Will be set if odds bonus is enabled
        self.odds_scaling_factor = 1.0  # Standard baseline scaling
    
    def set_odds_calculator(self, odds_calculator) -> None:
        """Set the odds calculator for bonus calculations
        
        Args:
            odds_calculator: OddsCalculator instance
        """
        self.odds_calculator = odds_calculator
    
    @abstractmethod
    def calculate_score(self, prediction: List[str], actual_results: List[str]) -> int:
        """Calculate score based on prediction and actual results
        
        Args:
            prediction: List of countries in predicted order (1st to 10th)
            actual_results: List of countries in actual order (1st to 10th)
            
        Returns:
            The score as an integer
        """
        pass
    
    def calculate_score_with_odds_bonus(self, prediction: List[str], actual_results: List[str]) -> int:
        """Calculate score with odds-weighted bonus
        
        Args:
            prediction: List of countries in predicted order (1st to 10th)
            actual_results: List of countries in actual order (1st to 10th)
            
        Returns:
            The score with odds bonus
        """
        # Get base score
        base_score = self.calculate_score(prediction, actual_results)
        
        # Apply odds bonus if enabled
        if self.odds_calculator:
            return self.odds_calculator.apply_bonus_to_score(
                prediction, 
                actual_results, 
                base_score,
                self.odds_scaling_factor
            )
        
        return base_score
    
    def get_detailed_breakdown(self, prediction: List[str], actual_results: List[str]) -> Dict[str, Any]:
        """Get a detailed breakdown of the score calculation
        
        Args:
            prediction: List of countries in predicted order (1st to 10th)
            actual_results: List of countries in actual order (1st to 10th)
            
        Returns:
            Dictionary with detailed breakdown information
        """
        # Default implementation - subclasses should override for more specific breakdowns
        base_score = self.calculate_score(prediction, actual_results)
        total_score = base_score
        odds_bonus = 0
        odds_details = {}
        
        if self.odds_calculator:
            correct_countries = self.get_correct_countries(prediction, actual_results)
            total_score = self.odds_calculator.apply_bonus_to_score(
                prediction, 
                actual_results, 
                base_score,
                self.odds_scaling_factor
            )
            odds_bonus = total_score - base_score
            
            # Get detailed bonus for each correct country
            for country in correct_countries:
                bonus = self.odds_calculator.calculate_scaled_bonus(
                    country, 
                    self.odds_scaling_factor
                )
                odds = self.odds_calculator.country_odds.get(country, 0)
                odds_details[country] = {
                    "odds": odds,
                    "bonus": bonus
                }
        
        return {
            "system": self.name,
            "description": self.description,
            "total_score": total_score,
            "base_score": base_score,
            "odds_bonus": odds_bonus,
            "odds_scaling_factor": self.odds_scaling_factor,
            "odds_details": odds_details,
            "prediction": prediction,
            "actual_results": actual_results,
            "details": "No detailed breakdown available for this scoring system."
        }
    
    def get_top10_results(self, actual_results: List[str]) -> List[str]:
        """Get only the top 10 countries from the actual results
        
        Args:
            actual_results: Complete list of actual results
            
        Returns:
            List containing only the top 10 countries
        """
        return actual_results[:10] if len(actual_results) >= 10 else actual_results
    
    def get_correct_countries(self, prediction: List[str], actual_results: List[str]) -> Set[str]:
        """Get the set of correctly predicted countries (regardless of position)
        
        For standard scoring systems, only considers countries in the top 10 of actual results.
        Extended systems should override this method if they need to consider countries
        beyond the top 10.
        """
        # Only consider countries in the top 10 of actual results
        top10_results = self.get_top10_results(actual_results)
        return set(prediction) & set(top10_results)
    
    def get_exact_positions(self, prediction: List[str], actual_results: List[str]) -> List[int]:
        """Get a list of positions (0-indexed) that were predicted exactly"""
        # Only consider the top 10 results
        top10_results = self.get_top10_results(actual_results)
        return [i for i in range(min(len(prediction), len(top10_results))) if prediction[i] == top10_results[i]]


class SimpleAndSweet(ScoringSystem):
    """System 1: Simple & Sweet
    
    - Correct Country in Top 10: +2 points for each country in the actual Top 10
    - Exact Position Bonus: +3 additional points for each exact position match
    """
    
    def __init__(self):
        super().__init__(
            "Simple & Sweet",
            "2 points per correct country + 3 points per exact position"
        )
        # Typical perfect score is around 50 points, use as baseline
        self.odds_scaling_factor = 1.0  # Standard baseline scaling
    
    def calculate_score(self, prediction: List[str], actual_results: List[str]) -> int:
        # Only use the top 10 results
        top10_results = self.get_top10_results(actual_results)
        
        # Points for correct countries
        correct_countries = set(prediction) & set(top10_results)
        country_points = len(correct_countries) * 2
        
        # Points for exact positions
        exact_positions = [i for i in range(min(len(prediction), len(top10_results))) if prediction[i] == top10_results[i]]
        position_points = len(exact_positions) * 3
        
        return country_points + position_points
    
    def get_detailed_breakdown(self, prediction: List[str], actual_results: List[str]) -> Dict[str, Any]:
        # Only use the top 10 results
        top10_results = self.get_top10_results(actual_results)
        
        # Get correct countries and positions
        correct_countries = set(prediction) & set(top10_results)
        exact_positions = [i for i in range(min(len(prediction), len(top10_results))) if prediction[i] == top10_results[i]]
        
        # Calculate points
        country_points = len(correct_countries) * 2
        position_points = len(exact_positions) * 3
        base_score = country_points + position_points
        
        # Apply odds bonus if enabled
        total_score = base_score
        odds_bonus = 0
        odds_details = {}
        
        if self.odds_calculator:
            total_score = self.odds_calculator.apply_bonus_to_score(
                prediction, 
                top10_results,  # Use top10 results for odds bonus calculation
                base_score,
                self.odds_scaling_factor
            )
            odds_bonus = total_score - base_score
            
            # Get detailed bonus for each correct country
            for country in correct_countries:
                bonus = self.odds_calculator.calculate_scaled_bonus(
                    country, 
                    self.odds_scaling_factor
                )
                odds = self.odds_calculator.country_odds.get(country, 0)
                odds_details[country] = {
                    "odds": odds,
                    "bonus": bonus
                }
        
        # Create a lookup for actual positions
        actual_positions = {country: i for i, country in enumerate(top10_results)}
        
        # Create detailed breakdown
        country_details = []
        for i, country in enumerate(prediction):
            in_top10 = country in top10_results
            exact_match = i in exact_positions
            points = 0
            explanation = []
            
            if in_top10:
                points += 2
                explanation.append("+2 points (in top 10)")
                
                if exact_match:
                    points += 3
                    explanation.append("+3 points (exact position)")
                
                # Add odds bonus explanation if applicable
                if self.odds_calculator and country in odds_details:
                    country_bonus = odds_details[country]["bonus"]
                    country_odds = odds_details[country]["odds"]
                    if country_bonus > 0:
                        explanation.append(f"+{country_bonus:.1f} bonus (odds: {country_odds:.1f}, scaling: {self.odds_scaling_factor:.2f})")
            
            country_details.append({
                "position": i + 1,
                "country": country,
                "in_top10": in_top10,
                "exact_match": exact_match,
                "actual_position": actual_positions.get(country, "Not in Top 10"),
                "points": points,
                "explanation": ", ".join(explanation) if explanation else "No points"
            })
        
        return {
            "system": self.name,
            "description": self.description,
            "total_score": total_score,
            "base_score": base_score,
            "correct_countries": len(correct_countries),
            "correct_country_points": country_points,
            "exact_positions": len(exact_positions),
            "exact_position_points": position_points,
            "odds_bonus": odds_bonus,
            "odds_scaling_factor": self.odds_scaling_factor,
            "odds_details": odds_details,
            "country_details": country_details
        }


class EurovisionStyle(ScoringSystem):
    """System 3: Eurovision Style Points
    
    Mimics Eurovision voting for exact position guesses:
    - 1st place: +12 points
    - 2nd place: +10 points
    - 3rd place: +8 points
    - 4th place: +7 points
    - ...
    - 10th place: +1 point
    - Optional: +1 point for correct country in wrong position
    """
    
    def __init__(self, bonus_for_correct_country: bool = True):
        super().__init__(
            "Eurovision Style",
            "12, 10, 8, 7, 6, 5, 4, 3, 2, 1 points for exact positions"
        )
        self.position_points = [12, 10, 8, 7, 6, 5, 4, 3, 2, 1]
        self.bonus_for_correct_country = bonus_for_correct_country
        # Typical perfect score is around 68 points, scale to match baseline
        self.odds_scaling_factor = 1.4  # Adjusted from 0.5
    
    def calculate_score(self, prediction: List[str], actual_results: List[str]) -> int:
        score = 0
        # Only use the top 10 results
        top10_results = self.get_top10_results(actual_results)
        
        # Points for exact positions
        for i in range(min(len(prediction), len(top10_results))):
            if prediction[i] == top10_results[i]:
                score += self.position_points[i]
        
        # Optional bonus for correct countries in wrong positions
        if self.bonus_for_correct_country:
            correct_countries = set(prediction) & set(top10_results)
            exact_positions = [i for i in range(min(len(prediction), len(top10_results))) if prediction[i] == top10_results[i]]
            bonus_countries = len(correct_countries) - len(exact_positions)
            score += bonus_countries * 1
        
        return score
    
    def get_detailed_breakdown(self, prediction: List[str], actual_results: List[str]) -> Dict[str, Any]:
        # Only use the top 10 results
        top10_results = self.get_top10_results(actual_results)
        
        # Get correct countries and positions
        correct_countries = set(prediction) & set(top10_results)
        exact_positions = [i for i in range(min(len(prediction), len(top10_results))) if prediction[i] == top10_results[i]]
        
        # Calculate points
        position_points = 0
        for i in exact_positions:
            position_points += self.position_points[i]
        
        bonus_countries = len(correct_countries) - len(exact_positions)
        bonus_points = bonus_countries * 1 if self.bonus_for_correct_country else 0
        base_score = position_points + bonus_points
        
        # Apply odds bonus if enabled
        total_score = base_score
        odds_bonus = 0
        odds_details = {}
        
        if self.odds_calculator:
            total_score = self.odds_calculator.apply_bonus_to_score(
                prediction, 
                top10_results,  # Use top10 results for odds bonus calculation
                base_score,
                self.odds_scaling_factor
            )
            odds_bonus = total_score - base_score
            
            # Get detailed bonus for each correct country
            for country in correct_countries:
                bonus = self.odds_calculator.calculate_scaled_bonus(
                    country, 
                    self.odds_scaling_factor
                )
                odds = self.odds_calculator.country_odds.get(country, 0)
                odds_details[country] = {
                    "odds": odds,
                    "bonus": bonus
                }
        
        # Create a lookup for actual positions
        actual_positions = {country: i for i, country in enumerate(top10_results)}
        
        # Create detailed breakdown
        country_details = []
        for i, country in enumerate(prediction):
            in_top10 = country in top10_results
            exact_match = i in exact_positions
            points = 0
            explanation = []
            
            if exact_match:
                points += self.position_points[i]
                explanation.append(f"+{self.position_points[i]} points (exact position)")
            elif in_top10 and self.bonus_for_correct_country:
                points += 1
                explanation.append("+1 point (in top 10 but wrong position)")
            
            # Add odds bonus explanation if applicable
            if self.odds_calculator and country in odds_details:
                country_bonus = odds_details[country]["bonus"]
                country_odds = odds_details[country]["odds"]
                if country_bonus > 0:
                    explanation.append(f"+{country_bonus:.1f} bonus (odds: {country_odds:.1f}, scaling: {self.odds_scaling_factor:.2f})")
            
            country_details.append({
                "position": i + 1,
                "country": country,
                "in_top10": in_top10,
                "exact_match": exact_match,
                "actual_position": actual_positions.get(country, "Not in Top 10"),
                "points": points,
                "explanation": ", ".join(explanation) if explanation else "No points"
            })
        
        return {
            "system": self.name,
            "description": self.description,
            "total_score": total_score,
            "base_score": base_score,
            "position_points": position_points,
            "bonus_for_correct_country": self.bonus_for_correct_country,
            "bonus_countries": bonus_countries,
            "bonus_points": bonus_points,
            "odds_bonus": odds_bonus,
            "odds_scaling_factor": self.odds_scaling_factor,
            "odds_details": odds_details,
            "country_details": country_details
        }


class PositionalProximityBase(ScoringSystem):
    """Positional Proximity Base
    
    A scoring system that awards points based on proximity to actual position.
    
    This system awards points based on how close a predicted position 
    is to the actual position, regardless of whether the country finished 
    in the top 10 or beyond.
    """
    
    def __init__(self):
        super().__init__(
            "Positional Proximity Base",
            "Points awarded based on proximity to actual position, including for countries outside the top 10"
        )
        # Points awarded for proximity
        self.points = {
            0: 10,  # Exact match
            1: 7,   # Off by 1
            2: 5,   # Off by 2
            3: 3,   # Off by 3
            4: 2.5, # Off by 4
            5: 1,   # Off by 5
            6: 0.5, # Off by 6
            7: 0.25 # Off by 7
            # No points for positions off by more than 7
        }
        self.max_difference = 7  # Maximum difference to award points for
        self.exact_match_bonus = 1  # Bonus for getting the exact position
        self.odds_scaling_factor = 2.0  # Used to scale odds bonus
    
    def get_correct_countries(self, prediction: List[str], actual_results: List[str]) -> Set[str]:
        """Override to consider ALL countries in the actual results, not just top 10"""
        return set(prediction) & set(actual_results)

    def calculate_score(self, prediction: List[str], actual_results: List[str]) -> int:
        score = 0
        # Create a lookup for ALL actual positions, not just top 10, with case-insensitive matching
        actual_positions = {country.strip().lower(): i for i, country in enumerate(actual_results)}
        
        # Check each predicted country
        for pred_pos, country in enumerate(prediction):
            country_normalized = country.strip().lower()
            if country_normalized in actual_positions:
                # Country is somewhere in the results
                actual_pos = actual_positions[country_normalized]
                difference = abs(pred_pos - actual_pos)
                
                # Only award points if difference is 7 or less
                if difference <= 7:
                    score += self.points.get(difference, 0)
        
        return score
    
    def get_detailed_breakdown(self, prediction: List[str], actual_results: List[str]) -> Dict[str, Any]:
        # Debug: Print actual results and their normalized versions
        print("\nDEBUG - Actual Results:")
        # Print top 10 first
        for i, country in enumerate(actual_results):
            if i < 10:
                print(f"{i+1}: '{country}' -> '{country.strip().lower()}'")
        
        # Print positions 11 and beyond separately
        print("\nDEBUG - Countries beyond top 10:")
        for i, country in enumerate(actual_results):
            if i >= 10:
                print(f"{i+1}: '{country}' -> '{country.strip().lower()}'")
        
        # Create a lookup for ALL actual positions
        actual_positions = {country.strip().lower(): i for i, country in enumerate(actual_results)}
        
        # Debug: Print prediction countries and check if they're in actual_positions
        print("\nDEBUG - Predictions and Matches:")
        for i, country in enumerate(prediction):
            country_normalized = country.strip().lower()
            found = country_normalized in actual_positions
            pos = actual_positions.get(country_normalized, "Not found")
            print(f"{i+1}: '{country}' -> '{country_normalized}' | In results: {found} | Position: {pos}")
        
        # Calculate points and create detailed breakdown
        base_score = 0
        country_details = []
        correct_countries = set([p.strip().lower() for p in prediction]) & set([a.strip().lower() for a in actual_results])
        
        for pred_pos, country in enumerate(prediction):
            # Normalize country name for case-insensitive matching
            country_normalized = country.strip().lower()
            in_results = country_normalized in actual_positions
            points = 0
            explanation = []
            difference = None
            
            if in_results:
                actual_pos = actual_positions[country_normalized]
                difference = abs(pred_pos - actual_pos)
                
                # Only award points if difference is 7 or less
                if difference <= 7:
                    points = self.points.get(difference, 0)
                else:
                    points = 0
                    explanation.append(f"No points (off by {difference} positions, beyond the 7-position threshold)")
                
                base_score += points
                
                if difference == 0:
                    explanation.append(f"+{points} points (exact position)")
                elif difference <= 7:
                    explanation.append(f"+{points} points (off by {difference} position{'s' if difference > 1 else ''})")
                
                # Special note if country is outside top 10 but still correct
                if actual_pos >= 10 and difference <= 7:
                    explanation.append(f"(country finished at position {actual_pos+1})")
            else:
                explanation.append("No points (country not in results)")
            
            # Prepare actual position display - show where the predicted country actually finished
            if in_results:
                # Find the original case from actual_results
                original_case_country = next((c for c in actual_results if c.strip().lower() == country_normalized), country)
                actual_position_display = f"{original_case_country} ({actual_positions[country_normalized] + 1})"
            else:
                actual_position_display = "Not in Results"
            
            country_details.append({
                "position": pred_pos + 1,
                "country": country,
                "in_results": in_results,
                "actual_position": actual_position_display,
                "position_difference": difference,
                "points": points,
                "explanation": ", ".join(explanation) if explanation else "No points (country not in results)"
            })
        
        # Apply odds bonus if enabled
        total_score = base_score
        odds_bonus = 0
        odds_details = {}
        
        if self.odds_calculator:
            # We need to modify this to only consider the countries in both prediction and actual results
            # Use lowercase normalization for consistent matching
            filtered_prediction = [country for country in prediction if country.strip().lower() in [a.strip().lower() for a in actual_results]]
            filtered_actual = [country for country in actual_results if country.strip().lower() in [p.strip().lower() for p in prediction]]
            
            total_score = self.odds_calculator.apply_bonus_to_score(
                filtered_prediction, 
                filtered_actual, 
                base_score,
                self.odds_scaling_factor
            )
            odds_bonus = total_score - base_score
            
            # Get detailed bonus for each correct country - use normalized names
            for country in prediction:
                country_normalized = country.strip().lower()
                if country_normalized in [a.strip().lower() for a in actual_results]:
                    bonus = self.odds_calculator.calculate_scaled_bonus(
                        country, 
                        self.odds_scaling_factor
                    )
                    odds = self.odds_calculator.country_odds.get(country, 0)
                    odds_details[country] = {
                        "odds": odds,
                        "bonus": bonus
                    }
                    
                    # Add odds bonus explanation to country details
                    for detail in country_details:
                        if detail["country"].strip().lower() == country_normalized and detail["in_results"]:
                            country_bonus = odds_details[country]["bonus"]
                            country_odds = odds_details[country]["odds"]
                            if country_bonus > 0:
                                detail["explanation"] += f", +{country_bonus:.1f} bonus (odds: {country_odds:.1f}, scaling: {self.odds_scaling_factor:.2f})"
        
        return {
            "system": self.name,
            "description": self.description,
            "total_score": total_score,
            "base_score": base_score,
            "points_scale": self.points,
            "max_difference": self.max_difference,
            "exact_match_bonus": self.exact_match_bonus,
            "odds_bonus": odds_bonus,
            "odds_scaling_factor": self.odds_scaling_factor,
            "odds_details": odds_details,
            "country_details": country_details
        }


class TopHeavyPositionalProximity(ScoringSystem):
    """TopHeavyPositionalProximity
    
    A comprehensive system with base points for correctly predicted countries in top 10:
    - Base Points: +X points for each country correctly identified in the top 10
    - Additional points for proximity to actual position
    - Also awards points when a country predicted in top 10 finishes outside top 10
      based on proximity to actual position
    - Bonus of +3 points for correctly predicting the winner (1st place)
    """
    
    def __init__(self, base_points: int = 2):
        super().__init__(
            "TopHeavyPositionalProximity",
            f"+{base_points} base points per correct country + proximity points for all countries"
        )
        self.base_points = base_points
        self.winner_bonus = 3  # Bonus for correctly predicting the winner
        
        # Points for countries that actually finished in Top 3 (less top-heavy)
        self.top3_points = {
            0: 15,  # Exact position
            1: 12,  # Off by 1
            2: 9,   # Off by 2
            3: 6,   # Off by 3
            4: 4,   # Off by 4
            5: 2,   # Off by 5
            6: 1.5, # Off by 6
            7: 0.75 # Off by 7
            # No points for positions off by more than 7
        }
        
        # Points for countries that finished in positions 4-10
        self.lower_points = {
            0: 10,  # Exact position
            1: 8,   # Off by 1
            2: 6,   # Off by 2
            3: 4,   # Off by 3
            4: 3,   # Off by 4
            5: 2,   # Off by 5
            6: 1, # Off by 6
            7: 0.5 # Off by 7
            # No points for positions off by more than 7
        }
        
        # Points for countries predicted in top 10 but finished outside top 10
        # Now using a proximity-based approach instead of flat points
        self.outside_top10_points = {
            1: 7,   # Off by 1 position
            2: 5,   # Off by 2 positions
            3: 3,   # Off by 3 positions
            4: 1.5, # Off by 4 positions
            5: 1,   # Off by 5 positions
            6: 0.5, # Off by 6 positions
            7: 0.25 # Off by 7 positions
            # No points for positions off by more than 7
        }
        
        # Typical perfect score estimation and scaling
        self.odds_scaling_factor = 2.2
    
    def get_correct_countries(self, prediction: List[str], actual_results: List[str]) -> Set[str]:
        """Override to consider ALL countries in the actual results, not just top 10"""
        return set(prediction) & set(actual_results)

    def calculate_score(self, prediction: List[str], actual_results: List[str]) -> int:
        score = 0
        # Create a lookup for all actual positions with case-insensitive matching
        actual_positions = {country.strip().lower(): i for i, country in enumerate(actual_results)}
        
        # Check for winner bonus - if first prediction matches the actual winner
        if prediction and actual_results and prediction[0].strip().lower() == actual_results[0].strip().lower():
            score += self.winner_bonus
        
        # Check each predicted country
        for pred_pos, country in enumerate(prediction):
            country_normalized = country.strip().lower()
            if country_normalized in actual_positions:
                actual_pos = actual_positions[country_normalized]
                
                # Base points for correctly predicting a country that's in the results
                if actual_pos < 10:  # Country is in top 10
                    score += self.base_points
                    
                    difference = abs(pred_pos - actual_pos)
                    
                    # Additional points based on proximity to actual position
                    if actual_pos < 3:  # Top 3
                        if difference <= 7:  # Only award points if off by 7 or less
                            score += self.top3_points.get(difference, 0)
                    else:  # Positions 4-10
                        if difference <= 7:  # Only award points if off by 7 or less
                            score += self.lower_points.get(difference, 0)
                else:
                    # Country is in results but outside top 10
                    # Calculate the position difference considering positions beyond top 10
                    difference = abs(pred_pos - actual_pos)
                    if difference <= 7:  # Only award points if off by 7 or less
                        score += self.outside_top10_points.get(difference, 0)
        
        return score
    
    def get_detailed_breakdown(self, prediction: List[str], actual_results: List[str]) -> Dict[str, Any]:
        # Debug: Print actual results and their normalized versions
        print("\nDEBUG - Actual Results:")
        # Print top 10 first
        for i, country in enumerate(actual_results):
            if i < 10:
                print(f"{i+1}: '{country}' -> '{country.strip().lower()}'")
        
        # Print positions 11 and beyond separately
        print("\nDEBUG - Countries beyond top 10:")
        for i, country in enumerate(actual_results):
            if i >= 10:
                print(f"{i+1}: '{country}' -> '{country.strip().lower()}'")
        
        # Create a lookup for all actual positions with case-insensitive matching
        actual_positions = {country.strip().lower(): i for i, country in enumerate(actual_results)}
        
        # Debug: Print prediction countries and check if they're in actual_positions
        print("\nDEBUG - Predictions and Matches:")
        for i, country in enumerate(prediction):
            country_normalized = country.strip().lower()
            found = country_normalized in actual_positions
            pos = actual_positions.get(country_normalized, "Not found")
            print(f"{i+1}: '{country}' -> '{country_normalized}' | In results: {found} | Position: {pos}")
        
        # Calculate points and create detailed breakdown
        base_score = 0
        country_details = []
        correct_countries = set([p.strip().lower() for p in prediction]) & set([a.strip().lower() for a in actual_results])
        
        # Check for winner bonus
        winner_bonus_points = 0
        if prediction and actual_results and prediction[0].strip().lower() == actual_results[0].strip().lower():
            winner_bonus_points = self.winner_bonus
            base_score += winner_bonus_points
        
        for pred_pos, country in enumerate(prediction):
            # Normalize country name for case-insensitive matching
            country_normalized = country.strip().lower()
            in_results = country_normalized in actual_positions
            in_top10 = in_results and actual_positions[country_normalized] < 10
            points = 0
            explanation = []
            difference = None
            
            # Add winner bonus explanation for the first position if correct
            if pred_pos == 0 and in_results and actual_positions[country_normalized] == 0:
                points += self.winner_bonus
                explanation.append(f"+{self.winner_bonus} points (correctly predicted the winner)")
            
            if in_results:
                actual_pos = actual_positions[country_normalized]
                difference = abs(pred_pos - actual_pos)
                
                if in_top10:
                    # Base points for correctly predicting a top 10 country
                    points += self.base_points
                    explanation.append(f"+{self.base_points} points (country in top 10)")
                    
                    # Additional points based on proximity to actual position
                    if actual_pos < 3:  # Top 3
                        proximity_points = 0
                        if difference <= 7:  # Only award points if off by 7 or less
                            proximity_points = self.top3_points.get(difference, 0)
                        tier = "top 3"
                    else:  # Positions 4-10
                        proximity_points = 0
                        if difference <= 7:  # Only award points if off by 7 or less
                            proximity_points = self.lower_points.get(difference, 0)
                        tier = "positions 4-10"
                    
                    points += proximity_points
                    
                    if difference == 0:
                        explanation.append(f"+{proximity_points} points (exact position in {tier})")
                    elif difference <= 7:
                        explanation.append(f"+{proximity_points} points (off by {difference} position{'s' if difference > 1 else ''} in {tier})")
                    else:
                        explanation.append(f"No additional proximity points (off by {difference} positions, beyond the 7-position threshold)")
                else:
                    # Country is in results but outside top 10
                    # Calculate points based on proximity to the actual position
                    proximity_points = 0
                    if difference <= 7:  # Only award points if off by 7 or less
                        proximity_points = self.outside_top10_points.get(difference, 0)
                    points += proximity_points
                    if difference <= 7:
                        explanation.append(f"+{proximity_points} points (off by {difference} position{'s' if difference > 1 else ''}, country finished at position {actual_pos+1})")
                    else:
                        explanation.append(f"No points (off by {difference} positions, beyond the 7-position threshold, country finished at position {actual_pos+1})")
                
                base_score += points - (self.winner_bonus if pred_pos == 0 and actual_pos == 0 else 0)  # Avoid double-counting winner bonus
            else:
                explanation.append("No points (country not in results)")
            
            # Prepare actual position display - show where the predicted country actually finished
            if in_results:
                # Find the original case from actual_results
                original_case_country = next((c for c in actual_results if c.strip().lower() == country_normalized), country)
                actual_position_display = f"{original_case_country} ({actual_positions[country_normalized] + 1})"
            else:
                actual_position_display = "Not in Results"
            
            country_details.append({
                "position": pred_pos + 1,
                "country": country,
                "in_results": in_results,
                "in_top10": in_top10,
                "actual_position": actual_position_display,
                "position_difference": difference,
                "points": points,
                "explanation": ", ".join(explanation) if explanation else "No points (country not in results)"
            })
        
        # Apply odds bonus if enabled
        total_score = base_score
        odds_bonus = 0
        odds_details = {}
        
        if self.odds_calculator:
            # Use lowercase normalization for consistent matching
            filtered_prediction = [country for country in prediction if country.strip().lower() in [a.strip().lower() for a in actual_results]]
            filtered_actual = [country for country in actual_results if country.strip().lower() in [p.strip().lower() for p in prediction]]
            
            total_score = self.odds_calculator.apply_bonus_to_score(
                filtered_prediction, 
                filtered_actual, 
                base_score,
                self.odds_scaling_factor
            )
            odds_bonus = total_score - base_score
            
            # Get detailed bonus for each correct country - use normalized names
            for country in prediction:
                country_normalized = country.strip().lower()
                if country_normalized in [a.strip().lower() for a in actual_results]:
                    bonus = self.odds_calculator.calculate_scaled_bonus(
                        country, 
                        self.odds_scaling_factor
                    )
                    odds = self.odds_calculator.country_odds.get(country, 0)
                    odds_details[country] = {
                        "odds": odds,
                        "bonus": bonus
                    }
                    
                    # Add odds bonus explanation to country details
                    for detail in country_details:
                        if detail["country"].strip().lower() == country_normalized and detail["in_results"]:
                            country_bonus = odds_details[country]["bonus"]
                            country_odds = odds_details[country]["odds"]
                            if country_bonus > 0:
                                detail["explanation"] += f", +{country_bonus:.1f} bonus (odds: {country_odds:.1f}, scaling: {self.odds_scaling_factor:.2f})"
        
        return {
            "system": self.name,
            "description": self.description,
            "total_score": total_score,
            "base_score": base_score,
            "base_points": self.base_points,
            "winner_bonus": self.winner_bonus,
            "top3_points_scale": self.top3_points,
            "lower_points_scale": self.lower_points,
            "outside_top10_points_scale": self.outside_top10_points,
            "odds_bonus": odds_bonus,
            "odds_scaling_factor": self.odds_scaling_factor,
            "odds_details": odds_details,
            "country_details": country_details
        } 