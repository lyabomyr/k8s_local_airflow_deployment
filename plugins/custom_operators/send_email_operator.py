import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from airflow.hooks.base import BaseHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults


class SendEmailOperator(BaseOperator):

    @apply_defaults
    def __init__(
        self,
        to_email: str,
        subject: str,
        description: str,
        from_email: str,
        smtp_conn_id: str = "smtp_default",
        html_attached_content: list = None,
        pull_xcom_data: dict = None,
        attached_data_content_key: str = "html_context",
        attached_data_file_path_key: str = "file_name",
        *args,
        **kwargs
    ):
        super(SendEmailOperator, self).__init__(*args, **kwargs)
        self.to_email = to_email if isinstance(to_email, list) else [to_email]
        self.subject = subject
        self.description = description
        self.smtp_conn_id = smtp_conn_id
        self.from_email = from_email
        self.pull_xcom_data = pull_xcom_data
        self.html_attached_content = (
            html_attached_content if html_attached_content else []
        )
        self.html_reports = None
        self.attached_data_content_key = attached_data_content_key
        self.attached_data_file_path_key = attached_data_file_path_key

    def execute(self, context):
        smtp_conn = BaseHook.get_connection(self.smtp_conn_id)
        smtp_host = smtp_conn.host
        smtp_port = smtp_conn.port
        smtp_user = smtp_conn.login
        smtp_password = smtp_conn.password

        if self.pull_xcom_data is not None:
            self.html_reports = context["ti"].xcom_pull(
                task_ids=self.pull_xcom_data["task_ids"], key=self.pull_xcom_data["key"]
            )

        elif self.html_attached_content is not None:
            self.html_reports = self.html_attached_content

        self.log.info("html_reports contain: %s", self.html_reports)
        msg = MIMEMultipart()
        msg["From"] = self.from_email
        msg["To"] = ", ".join(self.to_email)
        msg["Subject"] = self.subject

        body = self.description
        msg.attach(MIMEText(body, "plain"))

        for html in self.html_reports:
            html_content = html[self.attached_data_content_key]
            file_name = html[self.attached_data_file_path_key]
            html_part = MIMEApplication(html_content.encode("utf-8"))
            html_part.add_header(
                "Content-Disposition", "attachment", filename=file_name
            )
            msg.attach(html_part)

        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=300) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(self.from_email, self.to_email, msg.as_string())
            self.log.info("Email sent successfully to %s", self.to_email)
        except Exception as e:
            self.log.error("Failed to send email: %s", str(e))
            raise
