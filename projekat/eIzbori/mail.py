### if you have a password, send credentials.
### if you dont, send the user key.
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(email,key = None,password = None,advance = None):
    smtp_port = 587
    smtp_server = "smtp.gmail.com"
    email_from = "agandr456@gmail.com"
    pswd = "xuqumizscvldnrgo"
    base_url = "http://localhost:8000/Process/Voting/"

    TIE_server = smtplib.SMTP(smtp_server, smtp_port)
    TIE_server.starttls()
    TIE_server.login(email_from, pswd)
    
    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email
    msg['Subject'] = "E-Voting"
    link = f"{base_url}{key}"
    if password != None:
        body = f'Your access credentials for the voting platform are : \n E-mail: {email} \n Password: {password}'
        msg.attach(MIMEText(body, 'plain'))
        mail = msg.as_string()
        TIE_server.sendmail(email_from, email, mail)
    if advance == "start":
        body = f'Your link to access the candidacy phase is : \n {link}'
        msg.attach(MIMEText(body, 'plain'))
        mail = msg.as_string()
        TIE_server.sendmail(email_from, email, mail)
    elif advance == "advance":
        body = f'Your link to access the voting phase is : \n {link}'
        msg.attach(MIMEText(body, 'plain'))
        mail = msg.as_string()
        TIE_server.sendmail(email_from, email, mail)
    elif advance == "personal":
        body = 'You have successfully voted.'
        msg.attach(MIMEText(body, 'plain'))
        mail = msg.as_string()


    TIE_server.quit()
        
