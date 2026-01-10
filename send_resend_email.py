import resend

# Set your Resend API key
resend.api_key = "re_acCAr1wL_Q9iamVuoaSkJVGDo95Uu9dzX"

# Send the email
response = resend.Emails.send({
    "from": "onboarding@resend.dev",
    "to": "emiljoaquin.diaz@chmsc.edu.ph",
    "subject": "Hello World",
    "html": "<p>Congrats on sending your <strong>first email</strong>!</p>"
})

print(response)
