import io
import json
from urllib.parse import quote

class BadgeGenerator:
    """Generate badges for grading results."""
    
    @classmethod
    def generate_badge_url(cls, repository_name, passed_checks, total_checks, status):
        """Generate a shields.io badge URL."""
        # URL encode the repository name for the badge
        repo_name = quote(repository_name)
        
        # Determine badge color based on status
        color = 'success' if status == 'passed' else 'critical'
        
        # Calculate percentage
        percentage = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Generate shields.io URL
        return f"https://img.shields.io/badge/{repo_name}-{passed_checks}%2F{total_checks}%20({percentage:.0f}%25)-{color}"

    @classmethod
    def generate_badge_json(cls, repository_name, passed_checks, total_checks, status):
        """Generate badge data in JSON format."""
        return {
            'schemaVersion': 1,
            'label': repository_name,
            'message': f"{passed_checks}/{total_checks} ({(passed_checks/total_checks*100):.0f}%)",
            'color': 'success' if status == 'passed' else 'critical'
        }