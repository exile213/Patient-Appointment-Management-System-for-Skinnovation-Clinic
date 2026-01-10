import os
from mailjet_rest import Client
from django.template.loader import render_to_string

def send_mailjet_email(subject, to_email, template_name, context):
    api_key = os.environ['MAILJET_API_KEY']
    api_secret = os.environ['MAILJET_API_SECRET']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    html_body = render_to_string(template_name, context)
    data = {
        'Messages': [
            {
                "From": {
                    "Email": os.environ.get('MAILJET_SENDER_EMAIL', 'your_verified_sender@example.com'),
                    "Name": "Skinovation Beauty Clinic"
                },
                "To": [
                    {
                        "Email": to_email,
                        "Name": context.get('user').get_full_name() if context.get('user') else "Recipient"
                    }
                ],
                "Subject": subject,
                "HTMLPart": html_body,
                "TextPart": "This is a transactional email from Skinovation Beauty Clinic."
            }
        ]
    }
    return mailjet.send.create(data=data)
