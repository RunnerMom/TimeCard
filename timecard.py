#Timecard application
#RunnerMom May 2015

# Twilio Phone Number to dial in.
# checks whether callerid = 'work number'
# no -> leave a message regarding "Worker's Timecard"
# yes -> press 1 to check in. press 9 to check out.
# 1-> Thank you. You are checked in. -> sends text to Gowri
# 9-> Thank you. You are now checked out.
# constants in CAPS
# future feature: support >1 user with a dict

import os
from flask import Flask, request, redirect, url_for
from twilio import twiml
from twilio.rest import TwilioRestClient
from datetime import datetime, timedelta
from rfc822 import parsedate, mktime_tz
from time import strftime
import pytz


work_location=os.environ.get("WORK_LOCATION")
test_location=os.environ.get("TEST_LOCATION")
boss_number=os.environ.get("BOSS_NUMBER")
twilio_number=os.environ.get("TIMECARD_NUMBER")

workers={
	
}

account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

client=TwilioRestClient(account_sid, auth_token)

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def welcome():
	#Check whether callerid = work_location
	menu_url = url_for(".menu") #takes the name of the function, not the endpoint
	from_number = request.values.get('From')
	resp = twiml.Response()
	print "work = ", work_location
	print "from = ", from_number

	if from_number==work_location or from_number==test_location: #work location, triggers check in
		with resp.gather(numDigits=1, action=menu_url, method="POST") as g:
    			g.say("Welcome to your TimeCard. Press 1 to check inn, or press 9 to check out.", voice="woman")
	else: # leave a message
		resp.say("I'm sorry. You are not calling from your work location. Please call back", voice="woman")
		resp.hangup()
	return str(resp)

@app.route("/menu", methods=['GET', 'POST'])
def menu():
	#check digits
	digit = request.values.get('Digits')
	#get timestamp
	callsid = request.values.get('CallSid')
	call = client.calls.get(callsid)
	rfc_timestamp = call.date_created
	#convert to PDT formatted
	timestamp = convert_date(rfc_timestamp) #calls convert_date method below

	resp = twiml.Response()
	if digit =="1":
		message = client.messages.create(
			    body="Your worker checked in at: "+timestamp,  # Message body, if any
			    to=boss_number,
			    from_=twilio_number)
		print message.sid
		resp.say("You are now checked in. Thank you very much")
		resp.hangup()
	elif digit =="9":
		message = client.messages.create(
			    body="Your worker checked out at: "+timestamp,  # Message body, if any
			    to=boss_number,
			    from_=twilio_number)
		resp.say("Thanks for checking out")
	else:	
		resp.say("Sorry, that is an invalid selection. Please try again.")
		resp.redirect("/")
	return str(resp)

# Utility Functions	
def convert_date (rfc_timestamp):
	# input is an rfc timestamp in GMT, given by the Twilio API date_created parameter
	# output is a formatted timestamp in PDT
	pdt = pytz.timezone('US/Pacific')
	utc = pytz.utc
	# convert rfc to tuple to datetime object
	# PLS EXPLAIN ->http://www.saltycrane.com/blog/2008/11/python-datetime-time-conversions/

	#tuple object
	tpl_timestamp = list(parsedate(rfc_timestamp))
	#datetime object
	dt_timestamp = utc.localize(datetime(*tpl_timestamp[0:7]))
	
	#convert timestamp to PDT
	pdt_timestamp = dt_timestamp.astimezone(pdt)
	format = "%a, %d %b %Y %H:%M:%S %Z"
	timestamp= pdt_timestamp.strftime(format)
	return timestamp

if __name__=="__main__":

	app.debug = True
	if os.environ.get('HEROKU') is not None:
		import logging
		stream_handler = logging.StreamHandler()
		app.logger.addHandler(stream_handler)
		app.logger.setLevel(logging.DEBUG)
		app.logger.info('Timecard startup')

	app.run(host='0.0.0.0', port=5000)