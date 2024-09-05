from django.db import models
from account.models import User
from django.db.models import JSONField
from django.utils import timezone
# Create your models here.


class BaseModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    added_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.id)

    class Meta:
        abstract = True
        ordering = ("-added_on",)


class API_METHODS:
    GET = 0
    PUT = 1
    POST = 2
    DELETE = 3
    PATCH = 4
    HEAD = 6
    OPTIONS = 7
    TRACE = 8
    CONNECT = 9
    OTHER = 10

    @classmethod
    def map(cls, name):
        name = str(name).upper()
        keys = {
            "GET": cls.GET,
            "PUT": cls.PUT,
            "POST": cls.POST,
            "DELETE": cls.DELETE,
            "PATCH": cls.PATCH,
            "HEAD": cls.HEAD,
            "OPTIONS": cls.OPTIONS,
            "TRACE": cls.TRACE,
            "CONNECT": cls.CONNECT,
        }
        return keys.get(name, cls.OTHER)

    @classmethod
    def choice_tuple(cls):
        return [
            (cls.GET, "GET"),
            (cls.PUT, "PUT"),
            (cls.POST, "POST"),
            (cls.DELETE, "DELETE"),
            (cls.PATCH, "PATCH"),
            (cls.HEAD, "HEAD"),
            (cls.OPTIONS, "OPTIONS"),
            (cls.TRACE, "TRACE"),
            (cls.CONNECT, "CONNECT"),
            (cls.OTHER, "OTHER"),
        ]


class APILog(BaseModel):
    api = models.CharField(max_length=1024, help_text="API URL")
    view_name = models.CharField(max_length=500, db_index=True, help_text="View name or endpoint name")
    namespace = models.CharField(max_length=500, db_index=True, help_text="Namespace if applicable")
    method = models.IntegerField(choices=API_METHODS.choice_tuple(), db_index=True)
    status_code = models.PositiveSmallIntegerField(db_index=True, help_text="HTTP response status code")
    execution_time = models.DecimalField(decimal_places=5, max_digits=8, help_text="Execution time in seconds")
    sql_queries = models.IntegerField(null=True, blank=True, help_text="Number of SQL queries executed")
    client_ip_address = models.CharField(max_length=50, help_text="Client IP address")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="User making the request")
    headers = JSONField(help_text="Request headers")
    body = JSONField(help_text="Request body")
    response = JSONField(help_text="Response body")

    class Meta:
        db_table = "api_logs"
        verbose_name = "API Log"
        verbose_name_plural = "API Logs"
        ordering = ("-added_on",)

    def __str__(self):
        return f"{self.namespace}:{self.view_name}:{self.api}"
