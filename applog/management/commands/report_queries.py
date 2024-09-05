from django.core.management.base import BaseCommand
from applog.middleware.queryhunter import (
            QueryHunter,
            PrintingOptions,
            PrintingQueryHunterReporter
            )


class Command(BaseCommand):
    help = 'Generate a SQL query report'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Path to the output file')

    def handle(self, *args, **options):
        reporting_options = PrintingOptions(
            sort_by='line_no',
            count_threshold=1,
            duration_threshold=0.0,
            count_highlighting_threshold=5,
            duration_highlighting_threshold=0.5
        )

        query_hunter = QueryHunter(reporting_options)

        # Initialize your QueryHunter middleware or use it to capture queries

        # Generate the report
        reporter = PrintingQueryHunterReporter(query_hunter)
        file_path = options['file']
        reporter.report(file_path=file_path)

        self.stdout.write(self.style.SUCCESS(f'Report generated at {file_path}'))
