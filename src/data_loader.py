import csv
from datetime import datetime
from typing import List, Dict, Any, Tuple


class Participant:
    """Represents a participant in the Eurovision prediction competition"""
    
    def __init__(self, name: str, timestamp: datetime, predictions: List[str]):
        self.name = name
        self.timestamp = timestamp
        self.predictions = predictions
        self.scores: Dict[str, int] = {}  # Will store scores for different systems
        self.exact_matches = 0  # For tiebreaker
        self.exact_top3_matches = 0  # For tiebreaker


def parse_datetime(timestamp_str: str) -> datetime:
    """Parse a timestamp string from the CSV into a datetime object"""
    try:
        return datetime.strptime(timestamp_str, "%d/%m/%Y %H:%M:%S")
    except ValueError:
        # Fallback if the format is different
        try:
            return datetime.strptime(timestamp_str, "%m/%d/%Y %H:%M:%S")
        except ValueError:
            # Return current datetime if parsing fails
            return datetime.now()


def load_participants(csv_path: str) -> List[Participant]:
    """Load participants and their predictions from a CSV file
    
    Expected CSV format:
    Timestamp, Naam?, 1ste plaats?, 2de plaats?, ..., 10de plaats?
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        List of Participant objects
    """
    participants = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header row
        
        for row in reader:
            if len(row) < 12:  # Need timestamp, name, and 10 predictions
                continue
                
            timestamp = parse_datetime(row[0])
            name = row[1]
            predictions = row[2:12]  # Extract the 10 predictions
            
            participant = Participant(name, timestamp, predictions)
            participants.append(participant)
    
    return participants


def load_actual_results(results_file: str) -> List[str]:
    """Load the actual Eurovision results from a file
    
    Args:
        results_file: Path to the results file (one country per line, in order)
        
    Returns:
        List of countries in order of their actual finish
    """
    countries = []
    
    with open(results_file, 'r', encoding='utf-8') as f:
        for line in f:
            country = line.strip()
            if country:
                countries.append(country)
    
    return countries  # Return all countries, not just top 10 