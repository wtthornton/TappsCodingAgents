"""
InfluxDB Validator - Validates InfluxDB queries and patterns

Phase 1.2: InfluxDB & Time-Series Support for HomeIQ
"""

import re
from pathlib import Path
from typing import Any


class InfluxDBValidator:
    """
    Validates InfluxDB queries and connection patterns.
    
    Checks for:
    - Flux query syntax and patterns
    - Query optimization opportunities
    - Connection pattern best practices
    - Time-series data modeling issues
    """

    def __init__(self):
        """Initialize InfluxDB validator."""
        self.flux_query_pattern = re.compile(
            r'from\(bucket:\s*["\']([^"\']+)["\']\)',
            re.IGNORECASE
        )
        self.range_pattern = re.compile(
            r'range\(start:\s*([^)]+)\)',
            re.IGNORECASE
        )
        self.filter_pattern = re.compile(
            r'filter\(fn:\s*\(r\)\s*=>\s*([^)]+)\)',
            re.IGNORECASE
        )

    def validate_flux_query(self, query: str) -> dict[str, Any]:
        """
        Validate Flux query syntax and patterns.
        
        Args:
            query: Flux query string
            
        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "issues": list[str],
                "suggestions": list[str],
                "optimization_opportunities": list[str]
            }
        """
        issues = []
        suggestions = []
        optimizations = []
        
        # Check for time range
        if not self.range_pattern.search(query):
            issues.append("Missing time range - always specify range() after from()")
            suggestions.append("Add |> range(start: -1h) after from()")
        
        # Check for bucket specification
        if not self.flux_query_pattern.search(query):
            issues.append("Missing or invalid bucket specification in from()")
            suggestions.append("Use: from(bucket: \"bucket_name\")")
        
        # Check query order (range should be early)
        range_match = self.range_pattern.search(query)
        filter_matches = list(self.filter_pattern.finditer(query))
        
        if range_match and filter_matches:
            range_pos = range_match.start()
            first_filter_pos = filter_matches[0].start() if filter_matches else -1
            
            # Check if filters come before range (bad pattern)
            if first_filter_pos != -1 and first_filter_pos < range_pos:
                issues.append("Filters appear before range() - range should come first")
                suggestions.append("Move |> range(start: ...) before filter() operations")
        
        # Check for common anti-patterns
        if "aggregateWindow" in query and "filter" in query:
            # Check if aggregation comes before filtering
            agg_pos = query.find("aggregateWindow")
            filter_pos = query.find("filter")
            
            if agg_pos != -1 and filter_pos != -1 and agg_pos < filter_pos:
                optimizations.append(
                    "Consider filtering before aggregating to reduce data processed"
                )
        
        # Check for missing createEmpty parameter
        if "aggregateWindow" in query and "createEmpty: false" not in query:
            suggestions.append(
                "Add createEmpty: false to aggregateWindow() to skip empty windows"
            )
        
        # Check for limit() usage
        if "limit(" not in query and len(query) > 500:
            suggestions.append(
                "Consider adding limit() for large result sets to improve performance"
            )
        
        # Check for tag vs field filtering order
        # This is a heuristic - tags are typically in filter conditions with ==
        # Fields are typically in filter conditions with >, <, >=, <=
        tag_filters = re.findall(r'filter\(fn:\s*\(r\)\s*=>\s*r\["([^"]+)"\]\s*==', query)
        field_filters = re.findall(r'filter\(fn:\s*\(r\)\s*=>\s*r\["([^"]+)"\]\s*[><=]', query)
        
        if tag_filters and field_filters:
            # Check if field filters come before tag filters
            for field_filter in field_filters:
                field_pos = query.find(f'r["{field_filter}"]')
                for tag_filter in tag_filters:
                    tag_pos = query.find(f'r["{tag_filter}"]')
                    if field_pos != -1 and tag_pos != -1 and field_pos < tag_pos:
                        optimizations.append(
                            f"Consider filtering by tag '{tag_filter}' before field '{field_filter}' "
                            "(tags are indexed, fields are not)"
                        )
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "optimization_opportunities": optimizations
        }

    def validate_connection_pattern(self, code: str) -> dict[str, Any]:
        """
        Validate InfluxDB connection patterns.
        
        Args:
            code: Python code containing InfluxDB client usage
            
        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "issues": list[str],
                "suggestions": list[str]
            }
        """
        issues = []
        suggestions = []
        
        # Check for client creation
        if "InfluxDBClient" not in code:
            return {
                "valid": True,
                "issues": [],
                "suggestions": []
            }
        
        # Check for context manager usage
        if "InfluxDBClient" in code and "with" not in code:
            suggestions.append(
                "Consider using context manager (with statement) for automatic cleanup"
            )
        
        # Check for connection pooling/reuse
        if code.count("InfluxDBClient(") > 1:
            issues.append("Multiple InfluxDBClient instances - consider connection pooling")
            suggestions.append("Reuse a single client instance or use connection pooling")
        
        # Check for error handling
        if "InfluxDBClient" in code and "except" not in code:
            suggestions.append("Add error handling for InfluxDB operations")
        
        # Check for retry logic
        if "InfluxDBClient" in code and "retry" not in code.lower():
            suggestions.append("Consider adding retry logic for network operations")
        
        # Check for batch writes
        if "write_api.write" in code:
            write_calls = code.count("write_api.write")
            if write_calls > 5:
                suggestions.append(
                    "Consider batching multiple writes into a single write_api.write() call"
                )
        
        # Check for async patterns
        if "InfluxDBClient" in code and "async" in code:
            if "await" not in code:
                issues.append("Async function defined but await not used")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions
        }

    def validate_data_modeling(self, code: str) -> dict[str, Any]:
        """
        Validate time-series data modeling patterns.
        
        Args:
            code: Code containing InfluxDB data point creation
            
        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "issues": list[str],
                "suggestions": list[str]
            }
        """
        issues = []
        suggestions = []
        
        # Check for Point creation
        if "Point(" not in code:
            return {
                "valid": True,
                "issues": [],
                "suggestions": []
            }
        
        # Check for tag vs field usage
        if ".tag(" in code and ".field(" in code:
            # Check if high-cardinality data is used as tag
            # This is a heuristic - timestamps, unique IDs as tags are problematic
            if re.search(r'\.tag\([^)]*timestamp', code, re.IGNORECASE):
                issues.append("Timestamp used as tag - timestamps are automatic, don't duplicate")
                suggestions.append("Remove timestamp from tags, use time parameter instead")
        
        # Check for measurement naming
        point_creations = re.findall(r'Point\(["\']([^"\']+)["\']\)', code)
        for measurement in point_creations:
            if len(measurement) > 50:
                suggestions.append(
                    f"Measurement name '{measurement}' is long - consider shorter names"
                )
        
        # Check for proper field types
        if ".field(" in code:
            # Check for string fields that should be numeric
            if re.search(r'\.field\([^,]+,\s*["\']\d+\.?\d*["\']', code):
                suggestions.append(
                    "Numeric values in quotes - ensure proper field types (float vs string)"
                )
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions
        }

    def review_file(self, file_path: Path, code: str) -> dict[str, Any]:
        """
        Review a file for InfluxDB patterns.
        
        Args:
            file_path: Path to the file
            code: File content
            
        Returns:
            Dictionary with review results:
            {
                "has_influxdb": bool,
                "flux_queries": list[dict],
                "connection_issues": list[str],
                "data_modeling_issues": list[str],
                "suggestions": list[str]
            }
        """
        results = {
            "has_influxdb": False,
            "flux_queries": [],
            "connection_issues": [],
            "data_modeling_issues": [],
            "suggestions": []
        }
        
        # Check if file contains InfluxDB code
        has_influxdb = (
            "InfluxDBClient" in code or
            "influxdb" in code.lower() or
            "from(bucket:" in code or
            "Point(" in code
        )
        
        if not has_influxdb:
            return results
        
        results["has_influxdb"] = True
        
        # Extract and validate Flux queries
        flux_queries = re.findall(
            r'from\(bucket:[^}]+',
            code,
            re.DOTALL | re.IGNORECASE
        )
        
        for query in flux_queries:
            validation = self.validate_flux_query(query)
            results["flux_queries"].append({
                "query": query[:100] + "..." if len(query) > 100 else query,
                "validation": validation
            })
            results["suggestions"].extend(validation.get("suggestions", []))
        
        # Validate connection patterns
        connection_validation = self.validate_connection_pattern(code)
        results["connection_issues"].extend(connection_validation.get("issues", []))
        results["suggestions"].extend(connection_validation.get("suggestions", []))
        
        # Validate data modeling
        modeling_validation = self.validate_data_modeling(code)
        results["data_modeling_issues"].extend(modeling_validation.get("issues", []))
        results["suggestions"].extend(modeling_validation.get("suggestions", []))
        
        return results

