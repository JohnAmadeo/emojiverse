from flask import Flask, request
import json 
import requests
import sys
from face_labeler import emojify

app = Flask(__name__)

# page access token generated on FB developers website
PAT = 'EAACYCiTBaaQBAJjjFJgiie5dTnPyFaXxED16afYeIrAMxHGQqENJOtY0ycsYpdfM7jZCgRb53iVDaMSZAwGrfKC7p7i0ahZBEWcURybNeaC6ZAI1ZAmGAzv1aJys0EaZAkGdf5EcrwyGGwJo9FvzsZAo5AWyt5NHKwodb2g78VyswZDZD'

# From https://developers.facebook.com/docs/graph-api/webhooks:
# "When you add a new subscription, or modify an existing one, 
# Facebook servers will make a GET request to your callback URL 
# in order to verify the validity of the callback server.""
@app.route('/', methods=['GET'])
def handle_verification():
    print("Handling Verification.")
    # verification token agreed specified on FB developers website
    if request.args.get('hub.verify_token', default='') == 'my_voice_is_my_password_verify_me':
        print("Verification successful!")
        return request.args.get('hub.challenge', default='')
    else:
        print("Verification failed!")
        return 'Error, wrong validation token'

# When a user sends a message to a bot, FB makes a POST request that contains
# information on what the user sent to our bot. The JSON object sent to us is 
# in the form specified by the Facebook Graph API.
# Read more at: https://developers.facebook.com/docs/graph-api/webhooks
@app.route('/', methods=['POST'])
def handle_message():
    print "Handling Messages"
    sys.stdout.flush()
    payload = request.get_data()
    for sender, imageurl in messaging_events(payload):
        print "Incoming from %s: %s" % (sender, imageurl)
        emojifiedurl = emojify(imageurl) 
        print "Retrieving emojified url %s." % (emojifiedurl)
        sys.stdout.flush()
        send_message(PAT, sender, emojiurl)

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
                # print(item['payload']['url'])
                yield event["sender"]["id"], item['payload']['url']

        # if "message" in event and "text" in event["message"]:
        #     yield event["sender"]["id"], event["message"]["text"].encode('unicode_escape')

# return a response to FB 
def send_message(token, recipient, imageurl):
    """
    Send the message text to recipient with id recipient.
    """

    # r = requests.post("https://graph.facebook.com/v2.6/me/messages",
    #     params = {"access_token": token},
    #     data=json.dumps({
    #         "recipient": {"id": recipient},
    #         "message": {"text": imageurl.decode('unicode_escape')}
    #     }),
    #     headers={'Content-type': 'application/json'})

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
                    # "payload": {"url": 'https://tctechcrunch2011.files.wordpress.com/2011/05/tcdisrupt_tc-9.jpg'}
                    # "payload": {"url": 'https://emojiverse2.blob.core.windows.net/imgstore/img019f73a6-6af6-4374-b8ac-95c7bc99511a.jpeg'}
                }
            }
        }),
        headers={'Content-type': 'application/json'})

    if r.status_code != requests.codes.ok:
        print(r.text)
        sys.stdout.flush()

if __name__ == "__main__":
    app.run()



