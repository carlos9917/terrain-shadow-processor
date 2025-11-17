"""
Some libs to send messages from glat VM server
It will only work from glatmodelvm1p at the moment
This is to replace the mail command from hpcdev

"""

import smtplib
from string import Template
from datetime import datetime

def get_contacts(filename) -> tuple:
    """
    Get the data from the new contacts
    """
    names = []
    emails = []
    with open(filename, mode='r', encoding='utf-8') as contacts_file:
        for a_contact in contacts_file:
            names.append(a_contact.split()[0])
            emails.append(a_contact.split()[1])
    return names, emails


def read_template(filename):
    """
    Read the template message
    """
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

def send_emails(message_template,contacts_list="contacts.txt") -> None:
    """
    Send the emails with the new data
    """

    names, emails = get_contacts(contacts_list)  # read contacts
    #message_template = read_template('message.txt')
    message_template = read_template(message_template)
    
    
    dmi_server="diggums.dmi.dk"
    dmi_port=25 #or 587 or 465
    #fromAddr='cap@dmi.dk'
    #toAddr='cap@dmi.dk'
    text= "This is a test of sending email from within Python."
    server = smtplib.SMTP(host=dmi_server, port=dmi_port)
    
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    TODAY=datetime.strftime(datetime.today(),"%Y%m%d")
    for name, email in zip(names, emails):
        msg = MIMEMultipart()       # create a message
    
        # add in the actual person name to the message template
        message = message_template.substitute(PERSON_NAME=name.title())
        fromAddr = "cap@dmi.dk"
        # setup the parameters of the message
        msg['From']=fromAddr
        msg['To']=email
        msg['Subject']=f"New shadow station data generated on {TODAY}"
        print(f"Sending email from {fromAddr} to {email}") 
    
        # add in the message body
        msg.attach(MIMEText(message, 'plain'))
    
        # send the message via the server set up earlier.
        server.send_message(msg)
    
        del msg
    server.quit()

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        print("Using generic message for testing")
        send_emails("message.txt")
    elif len(sys.argv) == 2:
        message=sys.argv[1]
        print(f"Message provided as: {message}")
        send_emails(message)
    elif len(sys.argv) == 3:
        message=sys.argv[1]
        contact_list = sys.argv[2]
        print(f"Message provided as: {message} and contact list: {contact_list}")
        send_emails(message,contact_list)
