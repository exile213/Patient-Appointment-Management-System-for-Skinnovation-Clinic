import os
import resend
from django.template.loader import render_to_string

def send_resend_email(subject, to_email, template_name, context):
    resend.api_key = os.environ["RESEND_API_KEY"]
    html_body = render_to_string(template_name, context)
    params = {
        "from": "Skinovation Beauty Clinic <onboarding@resend.dev>",
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }
    return resend.Emails.send(params)
