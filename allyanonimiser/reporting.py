"""
Reporting module for Allyanonimiser.

This module provides functionality for generating reports on anonymization activities,
including statistics, visualizations, and export capabilities.
"""

import os
import json
import datetime
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from collections import Counter, defaultdict

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False

try:
    from IPython.display import display, HTML, Markdown
    IN_NOTEBOOK = True
except ImportError:
    IN_NOTEBOOK = False


class AnonymizationReport:
    """
    Class for generating, storing, and presenting anonymization reports.
    
    This class collects statistics from anonymization operations and provides
    methods to generate reports in various formats, including rich HTML output
    for Jupyter notebooks.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize a new report.
        
        Args:
            session_id: Optional identifier for this reporting session
        """
        self.session_id = session_id or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.datetime.now()
        self.end_time = None
        
        # Initialize data structures to hold report information
        self.total_documents = 0
        self.total_entities = 0
        self.entity_counts = Counter()
        self.operator_counts = Counter()
        self.entity_type_scores = defaultdict(list)
        self.document_stats = []
        
        # Tracks total characters processed and anonymized
        self.total_characters = 0
        self.total_anonymized_characters = 0
        
        # Track processing times
        self.processing_times = []
        
        # Detailed reports for each document
        self.document_reports = []
    
    def record_anonymization(self, document_id: str, original_text: str, 
                           anonymization_result: Dict[str, Any], 
                           processing_time: float) -> None:
        """
        Record the results of an anonymization operation.
        
        Args:
            document_id: Identifier for the document
            original_text: Original text before anonymization
            anonymization_result: Dict containing anonymization results
            processing_time: Time taken to process the document in seconds
        """
        self.total_documents += 1
        self.processing_times.append(processing_time)
        
        # Track character counts
        original_chars = len(original_text)
        self.total_characters += original_chars
        
        # Extract entities and operators from the anonymization result
        items = anonymization_result.get('items', [])
        self.total_entities += len(items)
        
        # Count entities by type and operators
        anonymized_chars = 0
        for item in items:
            entity_type = item.get('entity_type', 'UNKNOWN')
            self.entity_counts[entity_type] += 1
            
            # Count characters anonymized
            original_entity = item.get('original', '')
            anonymized_chars += len(original_entity)
            
            # Record operator used (if available)
            if 'operator' in item:
                self.operator_counts[item['operator']] += 1
        
        self.total_anonymized_characters += anonymized_chars
        
        # Store document-level statistics
        doc_stats = {
            'document_id': document_id,
            'original_length': original_chars,
            'entity_count': len(items),
            'anonymized_chars': anonymized_chars,
            'anonymization_ratio': anonymized_chars / original_chars if original_chars > 0 else 0,
            'processing_time': processing_time
        }
        self.document_stats.append(doc_stats)
        
        # Store detailed report for this document
        self.document_reports.append({
            'document_id': document_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'processing_time': processing_time,
            'original_length': original_chars,
            'entity_count': len(items),
            'entities': [{
                'entity_type': item.get('entity_type', 'UNKNOWN'),
                'original': item.get('original', ''),
                'replacement': item.get('replacement', ''),
                'operator': item.get('operator', 'unknown')
            } for item in items]
        })
    
    def record_batch_processing(self, batch_id: str, batch_size: int, 
                              batch_result: Dict[str, Any],
                              processing_time: float) -> None:
        """
        Record the results of processing a batch of documents.
        
        Args:
            batch_id: Identifier for the batch
            batch_size: Number of documents in the batch
            batch_result: Dict containing batch processing results
            processing_time: Time taken to process the batch in seconds
        """
        self.total_documents += batch_size
        self.processing_times.append(processing_time)
        
        # Extract entity counts from batch result
        if 'entity_counts' in batch_result:
            for entity_type, count in batch_result['entity_counts'].items():
                self.entity_counts[entity_type] += count
                self.total_entities += count
        
        # Extract operator counts if available
        if 'operator_counts' in batch_result:
            for operator, count in batch_result['operator_counts'].items():
                self.operator_counts[operator] += count
        
        # Store batch-level statistics
        batch_stats = {
            'batch_id': batch_id,
            'batch_size': batch_size,
            'entity_count': batch_result.get('total_entities', 0),
            'processing_time': processing_time,
            'avg_processing_time': processing_time / batch_size if batch_size > 0 else 0
        }
        self.document_stats.append(batch_stats)
    
    def finalize(self) -> None:
        """Finalize the report by setting the end time."""
        self.end_time = datetime.datetime.now()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of anonymization statistics.
        
        Returns:
            Dictionary containing summary statistics
        """
        if not self.end_time:
            self.finalize()
        
        # Calculate time elapsed
        elapsed_time = (self.end_time - self.start_time).total_seconds()
        
        # Calculate average processing time per document
        avg_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        
        # Calculate anonymization rate
        anonymization_rate = self.total_anonymized_characters / self.total_characters if self.total_characters > 0 else 0
        
        # Calculate entity distribution
        entity_distribution = {
            entity_type: count / self.total_entities * 100 
            for entity_type, count in self.entity_counts.items()
        } if self.total_entities > 0 else {}
        
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "elapsed_time_seconds": elapsed_time,
            "total_documents": self.total_documents,
            "total_entities": self.total_entities,
            "entities_per_document": self.total_entities / self.total_documents if self.total_documents > 0 else 0,
            "total_characters": self.total_characters,
            "total_anonymized_characters": self.total_anonymized_characters,
            "anonymization_rate": anonymization_rate,
            "avg_processing_time": avg_processing_time,
            "entity_counts": dict(self.entity_counts),
            "operator_counts": dict(self.operator_counts),
            "entity_distribution": entity_distribution
        }
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """
        Get a detailed report including document-level statistics.
        
        Returns:
            Dictionary containing detailed report
        """
        summary = self.get_summary()
        summary["document_stats"] = self.document_stats
        summary["document_reports"] = self.document_reports
        return summary
    
    def export_report(self, filepath: str, format: str = "json") -> str:
        """
        Export the report to a file.
        
        Args:
            filepath: Path to save the report
            format: Format for the report (json, csv, html)
            
        Returns:
            Path to the saved report file
        """
        if not self.end_time:
            self.finalize()
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if format.lower() == "json":
            # Export as JSON
            with open(filepath, 'w') as f:
                json.dump(self.get_detailed_report(), f, indent=2)
            return filepath
        
        elif format.lower() == "csv":
            # Export document stats as CSV
            df = pd.DataFrame(self.document_stats)
            df.to_csv(filepath, index=False)
            return filepath
        
        elif format.lower() == "html":
            # Export as HTML report
            html_content = self.generate_html_report()
            with open(filepath, 'w') as f:
                f.write(html_content)
            return filepath
        
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json', 'csv', or 'html'.")
    
    def generate_html_report(self) -> str:
        """
        Generate an HTML report.
        
        Returns:
            HTML string containing the report
        """
        summary = self.get_summary()
        
        # Create HTML
        html = f"""
        <html>
        <head>
            <title>Anonymization Report: {summary['session_id']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; margin-top: 20px; }}
                .stats {{ margin: 20px 0; }}
                .stat-box {{ 
                    display: inline-block; 
                    border: 1px solid #ddd; 
                    border-radius: 5px;
                    padding: 10px;
                    margin: 10px;
                    min-width: 200px;
                    background-color: #f8f9fa;
                }}
                .stat-title {{ font-weight: bold; color: #7f8c8d; }}
                .stat-value {{ font-size: 24px; color: #2980b9; }}
                table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin: 20px 0;
                }}
                th, td {{ 
                    border: 1px solid #ddd; 
                    padding: 8px; 
                    text-align: left;
                }}
                th {{ background-color: #34495e; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Anonymization Report</h1>
            <p>Session ID: {summary['session_id']}</p>
            <p>Period: {summary['start_time']} to {summary['end_time']}</p>
            <p>Total elapsed time: {summary['elapsed_time_seconds']:.2f} seconds</p>
            
            <h2>Summary Statistics</h2>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-title">Documents Processed</div>
                    <div class="stat-value">{summary['total_documents']}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-title">Entities Detected</div>
                    <div class="stat-value">{summary['total_entities']}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-title">Entities per Document</div>
                    <div class="stat-value">{summary['entities_per_document']:.2f}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-title">Characters Processed</div>
                    <div class="stat-value">{summary['total_characters']:,}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-title">Anonymization Rate</div>
                    <div class="stat-value">{summary['anonymization_rate']*100:.2f}%</div>
                </div>
                <div class="stat-box">
                    <div class="stat-title">Avg Processing Time</div>
                    <div class="stat-value">{summary['avg_processing_time']*1000:.1f} ms</div>
                </div>
            </div>
            
            <h2>Entity Type Distribution</h2>
            <table>
                <tr>
                    <th>Entity Type</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
        """
        
        # Add entity distribution rows
        for entity_type, count in sorted(summary['entity_counts'].items(), 
                                      key=lambda x: x[1], reverse=True):
            percentage = count / summary['total_entities'] * 100 if summary['total_entities'] > 0 else 0
            html += f"""
                <tr>
                    <td>{entity_type}</td>
                    <td>{count}</td>
                    <td>{percentage:.2f}%</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>Anonymization Operators Used</h2>
            <table>
                <tr>
                    <th>Operator</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
        """
        
        # Add operator distribution rows
        total_ops = sum(summary['operator_counts'].values())
        for operator, count in sorted(summary['operator_counts'].items(), 
                                   key=lambda x: x[1], reverse=True):
            percentage = count / total_ops * 100 if total_ops > 0 else 0
            html += f"""
                <tr>
                    <td>{operator}</td>
                    <td>{count}</td>
                    <td>{percentage:.2f}%</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html
    
    def display_in_notebook(self) -> None:
        """
        Display the report in a Jupyter notebook.
        
        This method renders a rich HTML report directly in the notebook.
        """
        if not IN_NOTEBOOK:
            print("This method only works in Jupyter notebooks.")
            return
        
        summary = self.get_summary()
        
        # Display header
        display(Markdown(f"# Anonymization Report: {summary['session_id']}"))
        display(Markdown(f"**Period:** {summary['start_time']} to {summary['end_time']}"))
        display(Markdown(f"**Total elapsed time:** {summary['elapsed_time_seconds']:.2f} seconds"))
        
        # Create summary table
        summary_data = {
            'Metric': ['Documents Processed', 'Entities Detected', 'Entities per Document',
                      'Characters Processed', 'Characters Anonymized', 'Anonymization Rate',
                      'Avg Processing Time'],
            'Value': [
                summary['total_documents'],
                summary['total_entities'],
                f"{summary['entities_per_document']:.2f}",
                f"{summary['total_characters']:,}",
                f"{summary['total_anonymized_characters']:,}",
                f"{summary['anonymization_rate']*100:.2f}%",
                f"{summary['avg_processing_time']*1000:.1f} ms"
            ]
        }
        
        display(Markdown("## Summary Statistics"))
        display(pd.DataFrame(summary_data))
        
        # Create entity distribution table
        if summary['entity_counts']:
            display(Markdown("## Entity Type Distribution"))
            
            entity_data = []
            for entity_type, count in sorted(summary['entity_counts'].items(), 
                                          key=lambda x: x[1], reverse=True):
                percentage = count / summary['total_entities'] * 100 if summary['total_entities'] > 0 else 0
                entity_data.append({
                    'Entity Type': entity_type,
                    'Count': count,
                    'Percentage': f"{percentage:.2f}%"
                })
            
            display(pd.DataFrame(entity_data))
            
            # Create visualizations if matplotlib is available
            if HAS_VISUALIZATION and entity_data:
                # Prepare data for pie chart
                labels = [item['Entity Type'] for item in entity_data[:10]]  # Top 10 entities
                sizes = [summary['entity_counts'][label] for label in labels]
                
                # Create pie chart
                plt.figure(figsize=(10, 6))
                plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
                plt.axis('equal')
                plt.title('Top 10 Entity Types')
                plt.tight_layout()
                plt.show()
        
        # Create operator distribution table
        if summary['operator_counts']:
            display(Markdown("## Anonymization Operators Used"))
            
            operator_data = []
            total_ops = sum(summary['operator_counts'].values())
            for operator, count in sorted(summary['operator_counts'].items(), 
                                       key=lambda x: x[1], reverse=True):
                percentage = count / total_ops * 100 if total_ops > 0 else 0
                operator_data.append({
                    'Operator': operator,
                    'Count': count,
                    'Percentage': f"{percentage:.2f}%"
                })
            
            display(pd.DataFrame(operator_data))
            
            # Create visualizations if matplotlib is available
            if HAS_VISUALIZATION and operator_data:
                # Prepare data for bar chart
                operators = [item['Operator'] for item in operator_data]
                counts = [summary['operator_counts'][op] for op in operators]
                
                # Create bar chart
                plt.figure(figsize=(10, 6))
                plt.bar(operators, counts)
                plt.xlabel('Operator')
                plt.ylabel('Count')
                plt.title('Anonymization Operators Used')
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.show()
        
        # Display processing time distribution if we have multiple documents
        if len(self.processing_times) > 1 and HAS_VISUALIZATION:
            display(Markdown("## Processing Time Distribution"))
            
            plt.figure(figsize=(10, 6))
            plt.hist(self.processing_times, bins=20)
            plt.xlabel('Processing Time (seconds)')
            plt.ylabel('Frequency')
            plt.title('Document Processing Time Distribution')
            plt.tight_layout()
            plt.show()
    
    def __str__(self) -> str:
        """Return a string representation of the report."""
        summary = self.get_summary()
        return (
            f"Anonymization Report: {summary['session_id']}\n"
            f"Period: {summary['start_time']} to {summary['end_time']}\n"
            f"Documents Processed: {summary['total_documents']}\n"
            f"Entities Detected: {summary['total_entities']}\n"
            f"Entities per Document: {summary['entities_per_document']:.2f}\n"
            f"Anonymization Rate: {summary['anonymization_rate']*100:.2f}%\n"
            f"Avg Processing Time: {summary['avg_processing_time']*1000:.1f} ms\n"
        )


class ReportingManager:
    """
    Manager for creating and handling anonymization reports.
    
    This class provides a facade for the reporting functionality and integrates
    with the main Allyanonimiser classes.
    """
    
    def __init__(self):
        """Initialize the reporting manager."""
        self.current_report = None
        self.reports = {}
    
    def start_new_report(self, session_id: Optional[str] = None) -> AnonymizationReport:
        """
        Start a new anonymization report.
        
        Args:
            session_id: Optional identifier for this reporting session
            
        Returns:
            The new AnonymizationReport instance
        """
        self.current_report = AnonymizationReport(session_id)
        self.reports[self.current_report.session_id] = self.current_report
        return self.current_report
    
    def get_current_report(self) -> Optional[AnonymizationReport]:
        """
        Get the current report.
        
        Returns:
            The current AnonymizationReport instance, or None if no report is active
        """
        return self.current_report
    
    def get_report(self, session_id: str) -> Optional[AnonymizationReport]:
        """
        Get a specific report by session ID.
        
        Args:
            session_id: The session ID of the report to retrieve
            
        Returns:
            The requested AnonymizationReport instance, or None if not found
        """
        return self.reports.get(session_id)
    
    def finalize_current_report(self) -> Dict[str, Any]:
        """
        Finalize the current report and return its summary.
        
        Returns:
            Dictionary containing report summary
        """
        if self.current_report:
            self.current_report.finalize()
            return self.current_report.get_summary()
        return {}
    
    def generate_report_from_results(self, results: List[Dict[str, Any]], 
                                   session_id: Optional[str] = None) -> AnonymizationReport:
        """
        Generate a report from a list of anonymization results.
        
        Args:
            results: List of anonymization result dictionaries
            session_id: Optional identifier for this reporting session
            
        Returns:
            The generated AnonymizationReport instance
        """
        report = AnonymizationReport(session_id)
        
        for i, result in enumerate(results):
            document_id = result.get('document_id', f"document_{i}")
            original_text = result.get('original_text', '')
            processing_time = result.get('processing_time', 0.0)
            
            report.record_anonymization(
                document_id=document_id,
                original_text=original_text,
                anonymization_result=result,
                processing_time=processing_time
            )
        
        report.finalize()
        self.reports[report.session_id] = report
        return report

# Create a singleton instance
report_manager = ReportingManager()