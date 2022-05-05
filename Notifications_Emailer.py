#!/usr/bin/env python
import sys
from email import message
import smtplib, ssl
import tkinter.messagebox

VERSION = sys.version_info[0]

if VERSION == 3:
    import _thread as thread
else:
    import thread

class NotificationsEmailer:
   
    def __init__(self, smtp_server, smtp_server_port, send_from_email, send_to_email, use_auth, auth_user, auth_password, subject_prefix):
        self.smtp_server = smtp_server
        self.smtp_server_port = smtp_server_port
        self.send_from_email = send_from_email
        self.send_to_email = send_to_email
        self.use_auth = use_auth
        self.auth_user = auth_user
        self.auth_password = auth_password
        self.subject_prefix = subject_prefix

    def multithread_send_email(self, email_subject, email_message):
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_server_port)

            ## server.connect()

            if(self.use_auth):
                ## authentication required
                context = ssl.create_default_context()
                server.starttls(context=context) #secure the connection
                server.login(self.auth_user, self.auth_password)

            ## send email here!
            server.sendmail(self.send_from_email, self.send_to_email, "Subject: " + self.subject_prefix + ": " + email_subject + "\n\n" + email_message)

        except Exception as e:
            pass  ## any message box causes GUI thread blocking, for now ignore error.
         ##   tkinter.messagebox.showinfo(title = "An error occured sending your email", message=e)

        finally:
            server.quit()

    def send_email(self, email_subject, email_message):
        try:
            ## tkinter.messagebox.showinfo("Email sending vars", "SMTP Server: " + smtp_server + "\r\nPort: " + smtp_server_port + "\r\nFrom: " + send_from_email)
            thread.start_new_thread(self.multithread_send_email, (email_subject, email_message))
        except Exception as e:
            pass  ## any message box causes GUI thread blocking, for now ignore error.
            ## tkinter.messagebox.showinfo(title = "An error occured sending your email", message=e)

