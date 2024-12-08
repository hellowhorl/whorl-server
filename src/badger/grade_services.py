import logging

logger = logging.getLogger(__name__)

class GradeService:
    """Service for processing and validating GatorGrader results."""

    @staticmethod
    def validate_grading_output(grading_output):
        """
        Validate that the grading output has the required structure.
        
        Args:
            grading_output (dict): Raw output to validate
            
        Returns:
            bool: True if valid, raises ValueError if invalid
        """
        if not isinstance(grading_output, dict):
            raise ValueError("Grading output must be a dictionary")

        # Check for required 'checks' field
        if 'checks' not in grading_output:
            raise ValueError("Grading output must contain 'checks' field")

        # Validate checks structure
        checks = grading_output.get('checks', [])
        if not isinstance(checks, list):
            raise ValueError("Checks must be a list")

        # Validate each check has required fields
        for check in checks:
            if not isinstance(check, dict):
                raise ValueError("Each check must be a dictionary")
            if 'passed' not in check:
                raise ValueError("Each check must have a 'passed' field")

        return True

    @staticmethod
    def process_gator_output(grading_output):
        """
        Process raw GatorGrader output and compute results.
        
        Args:
            grading_output (dict): Raw output from GatorGrader
            
        Returns:
            dict: Processed results with passed/total counts and details
        """
        try:
            # First validate the output structure
            GradeService.validate_grading_output(grading_output)

            # Extract checks from output
            checks = grading_output.get('checks', [])
            
            # Count passed checks
            passed_checks = sum(1 for check in checks if check.get('passed'))
            total_checks = len(checks)
            
            # Determine status
            status = 'passed' if passed_checks == total_checks else 'failed'
            
            return {
                'passed_checks': passed_checks,
                'total_checks': total_checks,
                'status': status,
                'details': checks
            }

        except Exception as e:
            logger.error(f"Error processing GatorGrader output: {str(e)}")
            raise ValueError(f"Invalid GatorGrader output format: {str(e)}")

    @staticmethod
    def format_check_output(check_results):
        """
        Format check results for display or storage.
        
        Args:
            check_results (dict): Processed check results
            
        Returns:
            dict: Formatted results with additional metadata
        """
        return {
            'summary': f"Passed {check_results['passed_checks']}/{check_results['total_checks']} checks",
            'status': check_results['status'],
            'details': check_results['details'],
            'pass_percentage': (check_results['passed_checks'] / check_results['total_checks'] * 100) 
                if check_results['total_checks'] > 0 else 0
        }