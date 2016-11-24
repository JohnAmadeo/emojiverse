from flask import Flask, request
import json 
import requests
import sys
from face_labeler import emojify
import os

app = Flask(__name__)

# page access token generated on FB developers website
_fbAPIToken = os.environ['FB_GRAPH_API_TOKEN']


@app.route('/', methods=['GET'])
def handle_verification():
    """
    From https://developers.facebook.com/docs/graph-api/webhooks:
    "When you add a new subscription, or modify an existing one, 
    Facebook servers will make a GET request to your callback URL 
    in order to verify the validity of the callback server.""
    """
    print("Handling Verification.")
    # verification token agreed specified on FB developers website
    if request.args.get('hub.verify_token', default='') == 'my_voice_is_my_password_verify_me':
        print("Verification successful!")
        return request.args.get('hub.challenge', default='')
    else:
        print("Verification failed!")
        return 'Error, wrong validation token'


@app.route('/', methods=['POST'])
def handle_message():
    """
    When a user sends a message to a bot, FB makes a POST request that contains
    information on what the user sent to our bot. The JSON object sent to us is 
    in the form specified by the Facebook Graph API.
    More at: https://developers.facebook.com/docs/graph-api/webhooks
    """
    print "Handling Messages"
    sys.stdout.flush()
    payload = request.get_data()
    for sender, imageurl in messaging_events(payload):
        print "Incoming from %s: %s" % (sender, imageurl)
        sys.stdout.flush()

        emojifiedurl = emojify(imageurl) 
        print "Retrieving emojified url %s." % (emojifiedurl)
        sys.stdout.flush()
        send_message(_fbAPIToken, sender, emojifiedurl)

    return "ok"

# handle incoming messages from users
def messaging_events(payload):
    """
    Generate tuples of (sender_id, message_text) from the provided payload.
    """

    # convert JSON to python object
    data = json.loads(payload)

    # extract image URL for further processing if message is an image
    messaging_events = data['entry'][0]['messaging']
    for event in messaging_events:
        if "attachments" in event["message"]:
            attachments = event["message"]["attachments"]
            for item in attachments:
                yield event["sender"]["id"], item['payload']['url']

# return a response to FB 
def send_message(token, recipient, imageurl):
    """
    Send the emojified image at imageurl to the recipient with id recipient.
    """

    print "url w/ decode: %s." % imageurl.decode('unicode_escape')
    sys.stdout.flush()

    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
        params = {"access_token": token},
        data=json.dumps({
            "recipient": {"id": recipient},
            "message": {
                "attachment": {
                    "type":"image",
                    "payload": { "url": imageurl}
                }
            }
        }),
        headers={'Content-type': 'application/json'})

    if r.status_code != requests.codes.ok:
        print(r.text)
        sys.stdout.flush()

if __name__ == "__main__":
    app.run()



