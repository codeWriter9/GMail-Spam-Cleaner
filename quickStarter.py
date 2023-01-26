"""Shows basic usage of the Gmail API.
Pulls The list of N emails
For each email checks against a list of spam email addresses
If Spam then deletes
else skips
"""
from __future__ import print_function
import argparse
import pickle
import os.path
import sys
import re
import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
GLOBAL_SPAM_LIST = []
MAXIMUM_MESSAGES_TO_BE_LOADED = 500

def save_skipped_emails(a_list):
    text_file = open("skipped-emails.txt", "w")
    n = text_file.write(str("\n".join(sorted(set(a_list)))))
    text_file.close()

def load_arguments():
    print("=======loading==arguments=====")
    res = []
    parser = argparse.ArgumentParser()
    parser.add_argument("spam_email_list", help="provide spam email list")
    args = parser.parse_args()
    print(args)
    if args.spam_email_list and os.path.exists(args.spam_email_list):
        print(args.spam_email_list)
        with open(args.spam_email_list, 'r') as spam_list_file:
            for line in spam_list_file:
                res.append(line)
    print("=======loaded====SPAM=LIST=====")
    ##res = ["Coursera@email.coursera.org", "SafeKey@welcome.aexp.com", "agm.preciousmetals@sbi.co.in", "alert@indeed.com", "alert@mailer.abhibus.com", "alerts@account.seeking.com", "alerts@updates.swiggy.in", "answer-noreply@quora.com", "contest@techgig.com", "cupid@adultfriendfinder.com", "demand@mail.adobe.com", "digest-noreply@quora.com", "education@naukri.com", "emarketing@hdfclife.com", "englishdigestnoreply@quora.com", "english-digest-noreply@quora.com", "etpromotions@indiatimes.com", "etnotifications@indiatimes.com", "info@bookbub.com", "info@easemytrip.com", "info@kaunsaoffers.com", "info@lucifro.com", "info@mailer.netflix.com", "info@pbengage.payback.in", "knowledge@expresscomputeronline.com", "mail@info.paytm.com", "mail@theadulthub.com", "messages-noreply@linkedin.com", "messagesnoreply@linkedin.com", "mythsofmodernphysics-noreply@quora.com", "news@nvidia.com", "newsletter@etprime.com", "news@edx.org", "newsletters@codechef.com", "newsletters@greatmail.in", "newsletters@kinkroot.com", "newsletters@prasscross.com", "no-reply@amazon.in", "no-reply@m.mail.coursera.org", "no-reply@swiggy.in", "no-reply@updates.bookmyshow.com", "noreply-maps-timeline@google.com", "noreply@e.udemymail.com", "no-reply@e.udemymail.com", "noreply@m.mail.coursera.org", "noreply@mailers.zomato.com", "noreply@medium.com", "noreply@redditmail.com", "noreply@tumblr.com", "no-reply@tumblr.com", "noreply@updates.bookmyshow.com", "nytimes@e.newyorktimes.com", "otifications-noreply@linkedin.com", "pinterest-picks@inspire.pinterest.com", "portfolio@portfolio.moneycontrol.com", "promotion@techgig.com", "recommendations@inspire.pinterest.com", "sbicrmdm_response@sbi.co.in", "technews@techgig.com", "udemy@email.udemy.com", "urbanpro-no-reply@urbanpro.com", "updates-noreply@linkedin.com", "wsmith@wordsmith.org"]    
    res = sorted(res)
    for email in res:
        GLOBAL_SPAM_LIST.append(email.replace("\n", ""))
    print(GLOBAL_SPAM_LIST)
    text_file = open("sorted-spam.txt", "w")
    n = text_file.write(str("\n".join(sorted(set(GLOBAL_SPAM_LIST)))))
    text_file.close()
    print("==============================")
    return ()

def creds():
    print("=======Verifying====Credentials=====")
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def extract_email(raw_email):
    email_list = raw_email.split(' ')
    return re.sub('[^a-zA-Z0-9-_*.@_]', '', email_list[len(email_list) - 1])

def is_from(header):
    return header['name'] == 'From'


def to_be_trashed(labels):
    return 'IMPORTANT' not in labels and 'SENT' not in labels


def list_messages(service, userId, numberOfMessages):
    return service.users().messages().list(userId=userId, maxResults=numberOfMessages).execute()


def get_message(service, userId, message):
   return service.users().messages().get(userId=userId, id=message['id']).execute()


def trash_message(service, userId, message):
   return service.users().messages().trash(userId=userId, id=message['id']).execute()


def main():

    arguments_tuple = load_arguments()
    start = time.time()
    print("=======Connecting==To===Server=====")
    service = build('gmail', 'v1', credentials=creds())

    # Call the Gmail API
    results = list_messages(service, 'me', MAXIMUM_MESSAGES_TO_BE_LOADED)
    messages = results.get('messages', [])
    skipped_emails = []
    total_msgs_trashed = []
    total_msgs_skipped = []

    if not messages:
        print('No messages found.')
    else:
        print('Fetching messages:')
        for message in messages:
            try:
                msg_body = get_message(service, 'me', message)
                headers, labels = msg_body['payload']['headers'], msg_body['labelIds']
                for header in headers:
                    if is_from(header) and to_be_trashed(labels):
                        email = extract_email(header['value'])
                        if email in GLOBAL_SPAM_LIST:
                            print("Trashing Message: " + str(message['id']) + " :from: " + str(email))
                            try:
                                trash_response = trash_message(service, 'me', message)
                                print("Trashed: " + str(message['id']) + " :Response: " + str(trash_response))
                                total_msgs_trashed.append("Trashed: " + str(message['id']) + " :Response: " + str(trash_response))
                            except Exception as exception:
                                print(type(exception))
                                continue
                        else:
                            try:
                                print("\tSkipping Message:" + " :from: " + str(email))
                                print("\t" + str(msg_body['labelIds']) + ":" + str(msg_body['snippet']))
                                total_msgs_skipped.append(" :from: " + str(email) + "\t" + str(msg_body['labelIds']) + ":" + str(msg_body['snippet']))
                                skipped_emails.append(str(email))
                            except Exception as exception:
                                print(type(exception))
                                continue
            except  Exception as exception:
                print(type(exception))
                continue
            print("\n")        
        save_skipped_emails(skipped_emails)
        print("\n Total Messages Trashed: " + str(len(total_msgs_trashed)))        
        print("\n Total Messages Skipped: " + str(len(total_msgs_skipped)))        
        time_taken = time.time() - start
        print("\n Time Taken (seconds): " + str(time_taken))
        print("\n\n\n")
        print("=======Program==Will===Exit=====")

if __name__ == '__main__':
    main()
