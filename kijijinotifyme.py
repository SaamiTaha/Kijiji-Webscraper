import sys
from selenium import webdriver
import imaplib, email
import smtplib
from email.message import EmailMessage
import time
import requests
from bs4 import BeautifulSoup
import os
import re

print('Sign in to gmail to send notifications from...')
user = str(input('Please enter a gmail address to send the notifications from:'))
password = str(input('Please enter an app password for the account you provided:'))
imap_url = "imap.gmail.com"

url = str(input("Enter the kijiji search you wish to monitor:"))

notifyEmail = str(input("Enter the email you wish to send the notifications to:"))

def check_sent():
    while True:
        con = imaplib.IMAP4_SSL(imap_url)
        r, d = con.login(user, password)
        assert r == 'OK', 'login failed'
        try:
            sent = []
            res, messages = con.select('"[Gmail]/Sent Mail"')
            messages = int(messages[0])
            n = 10
            for i in range(messages, messages - n, -1):
                res, msg = con.fetch(str(i), "(RFC822)")
                for response in msg:
                    if isinstance(response, tuple):
                        msg = email.message_from_bytes(response[1])
                        # getting the subject of the sent mail
                        subject = msg["Subject"]
                        if "BOT CRASHED" in subject:
                            pass
                        else:
                            index = subject.find("ID:") + 3
                            ID = int(subject[index:].strip())
                            sent.append(ID)
            return sent
        # do things with imap
        except Exception as e:
            print("IMAP failure: ", e)
            con.abort
            continue
        con.logout()
        break

def send_mail(newestAd):
    try:
        msg = EmailMessage()
        ID = str(newestAd.attrs.get("data-listing-id"))
        ID = int(''.join(ID.split()))
        subject = str(newestAd.find(class_="price").text).strip() + " " + str(newestAd.find(class_="title").text).strip() + " ID: " + str(ID)
        sentMail = check_sent()
        if ID in sentMail:
            print("Noti has already been sent.")
            return
        msg['Subject'] = subject.replace('\n', ' ').replace('\r', '')
        msg['From'] = user
        msg['To'] = notifyEmail
        msg.set_content(f'{info_builder(newestAd)}')
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
    except Exception as e:
        print(e, "\nemail failed to send.")
        report_error()
        quit()
def report_error():
    Error_msg = EmailMessage()
    Error_msg['Subject'] = "BOT CRASHED"
    Error_msg['From'] = user
    Error_msg['To'] = notifyEmail
    Error_msg.set_content('kijiji bot crashed. Check for errors.')
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(user, password)
        smtp.send_message(Error_msg)
def get_data():
    count = 0
    connected = False
    while connected == False:
        try:
           result = requests.get(url)
           doc = BeautifulSoup(result.text, "html.parser")
           newestAd = doc.find('div', class_="search-item regular-ad")
           if newestAd is not None and "data-listing-id" in newestAd.attrs:
               connected = True
           else:
               print("newestAd was Nonetype, trying again in 30 seconds...")
               time.sleep(30)
               count = count + 1
               if count == 10:
                   report_error()
                   print("Ad was Nonetype 10 times in a row")
                   quit()
        except Exception as e:
            print(e, "\nconnection failed, trying again...")
    return newestAd

def noti():
    Error_msg = EmailMessage()
    Error_msg['Subject'] = "BOT FIX TRIGGERED"
    Error_msg['From'] = user
    Error_msg['To'] = notifyEmail
    Error_msg.set_content('fix triggered, check for details')
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(user, password)
        smtp.send_message(Error_msg)
def info_builder(newestAd):
    link = newestAd.attrs.get("data-vip-url")
    info = f"kijiji.ca{link}" + "\n\n" + str(newestAd.find(class_="price").text).strip() + " " + str(newestAd.find(class_="title").text).strip() + "\n\n"
    description = str(newestAd.find(class_="description").text)
    description = " ".join(re.split("\s+", description, flags=re.UNICODE))
    description = description.lstrip()
    info = info + description
    return info
def getID(newestAd):
    id = newestAd.attrs.get()

def check_for_new():
    id = get_data()
    if(id == oldID):
        print("newest ad hasn't changed")
        return True
    else:
        print("new ad posted")
        send_noti()
        return False


oldID = get_data()
send_mail(oldID)
while True:
    id = get_data()
    if int(id.attrs.get("data-listing-id")) == int(oldID.attrs.get("data-listing-id")):
        print("no new ad found on refresh")
    else:
        print('new ad found!')
        oldID = id
        send_mail(id)
