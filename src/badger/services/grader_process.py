class GradeProcessor:
    """Process GatorGrader output and compute results."""
    
    @staticmethod
    def process_grading_results(grading_output):
        """
        Process raw GatorGrader output and return structured results.
        
        Args:
            grading_output (dict): Raw output from GatorGrader
        
        Returns:
            dict: Processed results with passed/total counts and details
        """
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
            'check_details': checks
        }

    @staticmethod
    def validate_grading_output(grading_output):
        """
        Validate that the grading output has the required structure.
        
        Args:
            grading_output (dict): Raw output to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(grading_output, dict):
            return False
            
        if 'checks' not in grading_output:
            return False
            
        checks = grading_output.get('checks', [])
        if not isinstance(checks, list):
            return False
            
        for check in checks:
            if not isinstance(check, dict):
                return False
            if 'passed' not in check:
                return False
                
        return True