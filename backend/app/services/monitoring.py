"""
WeatherWise Monitoring and Logging Service
Tracks system performance and data quality metrics
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Configure logging
log_dir = Path(__file__).parent.parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

# Setup file and console logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "weatherwise.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineMetrics:
    """Pipeline performance metrics."""
    timestamp: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    validation_failures: int
    average_response_time: float
    locations_processed: List[str]
    data_quality_score: float


@dataclass
class DataQualityMetric:
    """Data quality tracking."""
    location: str
    timestamp: str
    validation_passed: bool
    warnings_count: int
    errors_count: int
    data_completeness: float


class WeatherMonitoring:
    """Monitoring and metrics collection for weather data pipeline."""

    def __init__(self):
        """Initialize monitoring service."""
        self.metrics_file = log_dir / "pipeline_metrics.json"
        self.quality_file = log_dir / "data_quality.json"

        # Runtime metrics
        self.session_metrics = {
            'start_time': datetime.now(timezone.utc).isoformat(),
            'requests': [],
            'validation_results': [],
            'errors': []
        }

        logger.info("Weather monitoring service initialized")

    def log_api_requests(self, location: str, success: bool, response_time: float, error: Optional[str] = None):
        """Log API request metrics.
        
        Args:
            location: Location requested
            success: Whether request was successful
            response_time: Time taken for request in seconds
            error: Error message if request failed
        """
        request_log = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'location': location,
            'success': success,
            'response_time': response_time,
            'error': error
        }
        
        self.session_metrics['requests'].append(request_log)
        
        if success:
            logger.info(f"API request successful: {location} ({response_time:.2f}s)")
        else:
            logger.error(f"API request failed: {location} - {error}")

    def log_validation_result(self, location: str, validation_passed: bool, 
                            warnings: List[str], errors: List[str]):
        """Log data validation results.
        
        Args:
            location: Location validated
            validation_passed: Whether validation passed
            warnings: List of validation warnings
            errors: List of validation errors
        """
        validation_log = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'location': location,
            'validation_passed': validation_passed,
            'warnings_count': len(warnings),
            'errors_count': len(errors),
            'warnings': warnings,
            'errors': errors
        }
        
        self.session_metrics['validation_results'].append(validation_log)
        
        # Calculate data completeness (simple metric)
        data_completeness = 100.0 if validation_passed else max(0, 100 - len(errors) * 10)
        
        quality_metric = DataQualityMetric(
            location=location,
            timestamp=datetime.now(timezone.utc).isoformat(),
            validation_passed=validation_passed,
            warnings_count=len(warnings),
            errors_count=len(errors),
            data_completeness=data_completeness
        )
        
        self._save_quality_metric(quality_metric)
        
        if validation_passed:
            logger.info(f"Validation passed: {location} (Quality: {data_completeness:.1f}%)")
        else:
            logger.warning(f"Validation failed: {location} - {len(errors)} errors")
    
    def log_database_operation(self, operation: str, location: str, success: bool, 
                              records_affected: int = 0, error: Optional[str] = None):
        """Log database operations.
        
        Args:
            operation: Type of operation (insert, update, delete)
            location: Location affected
            success: Whether operation was successful
            records_affected: Number of records affected
            error: Error message if operation failed
        """
        db_log = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'operation': operation,
            'location': location,
            'success': success,
            'records_affected': records_affected,
            'error': error
        }
        
        if success:
            logger.info(f"Database {operation} successful: {location} ({records_affected} records)")
        else:
            logger.error(f"Database {operation} failed: {location} - {error}")
    
    def generate_session_report(self) -> Dict:
        """Generate report for current session.
        
        Returns:
            Dictionary containing session metrics and summary
        """
        requests = self.session_metrics['requests']
        validations = self.session_metrics['validation_results']
        
        if not requests:
            return {'message': 'No requests made in this session'}
        
        # Calculate metrics
        total_requests = len(requests)
        successful_requests = sum(1 for r in requests if r['success'])
        failed_requests = total_requests - successful_requests
        
        response_times = [r['response_time'] for r in requests if r['success']]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        validation_failures = sum(1 for v in validations if not v['validation_passed'])
        
        locations = list(set(r['location'] for r in requests))
        
        # Calculate overall data quality score
        if validations:
            quality_scores = []
            for v in validations:
                if v['validation_passed']:
                    score = max(90, 100 - v['warnings_count'] * 5)
                else:
                    score = max(0, 50 - v['errors_count'] * 10)
                quality_scores.append(score)
            data_quality_score = sum(quality_scores) / len(quality_scores)
        else:
            data_quality_score = 0
        
        # Create metrics object
        metrics = PipelineMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            validation_failures=validation_failures,
            average_response_time=avg_response_time,
            locations_processed=locations,
            data_quality_score=data_quality_score
        )
        
        self._save_session_metrics(metrics)
        
        return asdict(metrics)
    
    def get_performance_summary(self) -> str:
        """Get formatted performance summary.
        
        Returns:
            Formatted string with key performance indicators
        """
        report = self.generate_session_report()
        
        if 'message' in report:
            return report['message']
        
        summary = f"""
  WeatherWise Pipeline Performance Summary
{'='*50}
  Session Duration: {self._get_session_duration()}
  API Requests: {report['successful_requests']}/{report['total_requests']} successful
  Average Response Time: {report['average_response_time']:.2f}s
  Data Validation: {report['total_requests'] - report['validation_failures']}/{report['total_requests']} passed
  Data Quality Score: {report['data_quality_score']:.1f}%
  Locations Processed: {', '.join(report['locations_processed'])}

Status: {'EXCELLENT' if report['data_quality_score'] > 90 else '🟡 GOOD' if report['data_quality_score'] > 70 else '🔴 NEEDS ATTENTION'}
        """
        
        return summary.strip()
    
    def _save_session_metrics(self, metrics: PipelineMetrics):
        """Save session metrics to file."""
        try:
            # Load existing metrics
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    all_metrics = json.load(f)
            else:
                all_metrics = []
            
            # Add new metrics
            all_metrics.append(asdict(metrics))
            
            # Keep only last 100 sessions
            if len(all_metrics) > 100:
                all_metrics = all_metrics[-100:]
            
            # Save back to file
            with open(self.metrics_file, 'w') as f:
                json.dump(all_metrics, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def _save_quality_metric(self, metric: DataQualityMetric):
        """Save data quality metric to file."""
        try:
            # Load existing quality data
            if self.quality_file.exists():
                with open(self.quality_file, 'r') as f:
                    quality_data = json.load(f)
            else:
                quality_data = []
            
            # Add new metric
            quality_data.append(asdict(metric))
            
            # Keep only last 1000 entries
            if len(quality_data) > 1000:
                quality_data = quality_data[-1000:]
            
            # Save back to file
            with open(self.quality_file, 'w') as f:
                json.dump(quality_data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save quality metric: {e}")
    
    def _get_session_duration(self) -> str:
        """Get session duration as formatted string."""
        start_time = datetime.fromisoformat(self.session_metrics['start_time'].replace('Z', '+00:00'))
        duration = datetime.now(timezone.utc) - start_time
        
        total_seconds = int(duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        return f"{minutes}m {seconds}s"


# Example usage
if __name__ == "__main__":
    monitor = WeatherMonitoring()
    
    # Simulate some monitoring
    monitor.log_api_request("Manila,PH", True, 1.2)
    monitor.log_validation_result("Manila,PH", True, ["Minor warning"], [])
    monitor.log_database_operation("insert", "Manila,PH", True, 1)
    
    print(monitor.get_performance_summary())