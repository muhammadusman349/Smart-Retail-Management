import linecache
import os
import time
import traceback
from dataclasses import dataclass
from typing import Optional

from django.conf import settings

import logging

SORT_BY_OPTIONS = ['line_no', '-line_no', 'count', '-count', 'duration', '-duration']


@dataclass
class ReportingOptions:
    sort_by: str = 'line_no'
    modules: Optional[list[str]] = None
    max_sql_length: Optional[int] = None
    count_threshold: int = 1
    duration_threshold: float = 0.0

    def __post_init__(self):
        if self.sort_by not in SORT_BY_OPTIONS:
            raise ValueError(f'sort_by must be one of {SORT_BY_OPTIONS}')


@dataclass
class PrintingOptions(ReportingOptions):
    count_highlighting_threshold: int = 5
    duration_highlighting_threshold: float = 0.5


@dataclass
class LoggingOptions(ReportingOptions):
    logger_name: str = 'queryhunter'


class QueryHunterReporter:
    def __init__(self, query_hunter):
        self.query_hunter = query_hunter
        self.query_info = query_hunter.query_info
        self.options = query_hunter.reporting_options

    @classmethod
    def create(cls, queryhunter):
        reporting_options = queryhunter.reporting_options
        if isinstance(reporting_options, PrintingOptions):
            return PrintingQueryHunterReporter(queryhunter)
        elif isinstance(reporting_options, LoggingOptions):
            return LoggingQueryHunterReporter(queryhunter)


class PrintingQueryHunterReporter(QueryHunterReporter):
    def report(self, file_path: Optional[str] = None):
        RED = "\033[31m"
        GREEN = "\033[32m"
        BOLD = "\033[1m"

        output = []

        for name, module in self.query_info.items():
            output.append(f'{BOLD}{name}')
            output.append('=' * 2 * len(name))
            for line in module.lines:
                if line.duration < self.options.duration_threshold or line.count < self.options.count_threshold:
                    continue
                if line.duration >= self.options.duration_highlighting_threshold:
                    output.append(f'   {RED}{line}')
                elif line.count >= self.options.count_highlighting_threshold:
                    output.append(f'   {RED}{line}')
                else:
                    output.append(f'   {GREEN}{line}')
            output.append('\n')

        if file_path:
            with open(file_path, 'w') as file:
                file.write('\n'.join(output))
        else:
            print('\n'.join(output))


class LoggingQueryHunterReporter(QueryHunterReporter):
    def report(self):
        logger_name = self.options.logger_name
        logger = logging.getLogger(logger_name)
        for _name, module in self.query_info.items():
            for line in module.lines:
                if line.duration < self.options.duration_threshold or line.count < self.options.count_threshold:
                    continue
                logger.info(f'Module: {module.name} | {line}')


@dataclass
class Line:
    line_no: int
    code: str
    sql: str
    count: int
    duration: float
    meta_data: Optional[dict[str, str]] = None

    def __str__(self):
        string = (
            f'Line no: {self.line_no} | Code: {self.code} | '
            f'Num. Queries: {self.count} | Duration: {self.duration}'
        )
        if self.meta_data:
            for key, value in self.meta_data.items():
                string += f' | {key}: {value}'
        return string


@dataclass
class Module:
    name: str
    lines: list[Line]

    def __str__(self):
        data = ''
        for line_data in self.lines:
            data += f'Module: {self.name} | {line_data} \n'
        return data


class QueryHunter:
    def __init__(self, reporting_options: ReportingOptions, meta_data: Optional[dict[str, str]] = None):
        self.reporting_options = reporting_options
        self.query_info: dict[str, Module] = {}
        self.meta_data = meta_data or {}
        self.responses = []  # To store responses

    def __call__(self, execute, sql, params, many, context):
        stack_trace = traceback.extract_stack()[:-1]
        app_frame = None
        for frame in reversed(stack_trace):
            filename = frame.filename
            if self.is_application_code(filename):
                app_frame = frame
                break

        if app_frame:
            filename = app_frame.filename
            relative_path = str(os.path.relpath(app_frame.filename, settings.QUERYHUNTER_BASE_DIR))

            if self.reporting_options.modules is not None:
                if relative_path not in self.reporting_options.modules:
                    return execute(sql, params, many, context)

            module = self.query_info.get(relative_path, Module(relative_path, lines=[]))
            line_no = app_frame.lineno
            code = self.get_code_from_line(filename, line_no)
            start = time.monotonic()
            result = execute(sql, params, many, context)
            duration = time.monotonic() - start

            # Store response
            self.responses.append(result)

            if self.reporting_options.max_sql_length is not None:
                reportable_sql = sql[:self.reporting_options.max_sql_length]
            else:
                reportable_sql = sql

            try:
                line = next(line for line in module.lines if line.line_no == line_no)
            except StopIteration:
                line = Line(
                    line_no=line_no,
                    code=code,
                    sql=reportable_sql,
                    count=1,
                    duration=duration,
                    meta_data=self.meta_data,
                )
                module.lines.append(line)
            else:
                line.count += 1
                line.duration += duration

            reverse = self.reporting_options.sort_by.startswith('-')
            sort_by = self.reporting_options.sort_by[1:] if reverse else self.reporting_options.sort_by
            module.lines = sorted(module.lines, key=lambda x: getattr(x, sort_by), reverse=reverse)

            self.query_info[relative_path] = module

            # Debug print to check if queries are captured
            print(f'Captured SQL Query: {reportable_sql}')

            return result
        else:
            raise ValueError("Unable to determine application frame for SQL execution")

    @staticmethod
    def is_application_code(filename: str) -> bool:
        try:
            base_dir = settings.QUERYHUNTER_BASE_DIR
        except AttributeError:
            raise ValueError(
                "QUERYHUNTER_BASE_DIR not set in settings. "
                "Define manually or use the built in queryhunter.default_base_dir function",
            )
        return filename.startswith(base_dir)

    @staticmethod
    def get_code_from_line(filename: str, lineno: int) -> str:
        return linecache.getline(filename, lineno).strip()
