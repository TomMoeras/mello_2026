"""
Utility script to create a sample results file for testing the calculator.
"""

import os


def create_sample_results(output_file: str):
    """
    Create a sample results file for testing.
    
    Args:
        output_file: Path to the output file
    """
    # Sample results (countries in order of finish, 1st to 10th)
    results = [
        "Sweden",
        "Finland",
        "Israel",
        "Italy",
        "Ukraine",
        "France",
        "Spain",
        "Norway",
        "Portugal",
        "Lithuania"
    ]
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        for country in results:
            f.write(f"{country}\n")
    
    print(f"Sample results file created at: {output_file}")


if __name__ == "__main__":
    # Create results in the data directory
    output_path = os.path.join("data", "sample_results.txt")
    create_sample_results(output_path) 