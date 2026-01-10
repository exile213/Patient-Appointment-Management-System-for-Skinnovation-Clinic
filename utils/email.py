from postmarker.core import PostmarkClient
from django.template.loader import render_to_string
from django.conf import settings

def send_postmark_email(subject, to_email, template_name, context):
    html_body = render_to_string(template_name, context)
    client = PostmarkClient(server_token=settings.POSTMARK_API_TOKEN)
    client.emails.send(
        From=settings.POSTMARK_SENDER_EMAIL,
        To=to_email,
        Subject=subject,
        HtmlBody=html_body,
    )
