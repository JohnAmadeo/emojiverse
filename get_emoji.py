import random
import json
import io
from pprint import pprint


def emotion_to_shortname(emotion):
    r = random.random()
    a = ""
    if emotion == "anger":
        if r < .25:
            a = ":angry:"
        elif .25 < r and r < .5:
            a = ":rage:"
        elif .5 < r and r < .75:
            a = ":persevere:"
        else:
            a = ":japanese_ogre:"
    elif emotion == "contempt":
        if r < .25:
            a = ":confounded:"
        elif .25 < r and r < .5:
            a = ":triumph:"
        elif .5 < r and r < .75:
            a = ":unamused:"
        else:
            a = ":rolling_eyes:"
    elif emotion == "disgust":
        if r < .333:
            a = ":confounded:"
        elif .333 < r and r < .666:
            a = ":tired_face:"
        else:
            a = ":mask:"

    elif emotion == "fear":
        if r < .25:
            a = ":scream:"
        elif .25 < r and r < .5:
            a = ":fearful:"
        elif .5 < r and r < .75:
            a = ":frowning:"
        else:
            a = ":anguished:"
    elif emotion == "happiness":
        if r < .07692:
            a = ":joy:"
        elif .07692 < r and r < .15384:
            a = ":sunglasses:"
        elif .15384 < r and r < .23076:
            a = ":grin:"
        elif .23076 < r and r < .30769:
            a = ":smiley:"
        elif .30769 < r and r < .38461:
            a = ":smile:"
        elif .38461 < r and r < .46153:
            a = ":laughing:"
        elif .46153 < r and r < .53846:
            a = ":blush:"
        elif .53846 < r and r < .61538:
            a = ":slight_smile:"
        elif .61538 < r and r < .69230:
            a = ":relaxed:"
        elif .69230 < r and r < .76923:
            a = ":yum:"
        elif .76923 < r and r < .81645:
            a = ":stuck_out_tongue_closed_eyes:"
        else:
            a = ":grinning:"

    elif emotion == "neutral":
        if r < .2:
            a = ":nerd:"
        elif .2 < r and r < .4:
            a = ":no_mouth:"
        elif .4 < r and r < .7:
            a = ":neutral_face:"
        elif .7 < r and r < .9:
            a = ":confused:"
        else:
            a = ":robot:"
    elif emotion == "sadness":
        if r < .2:
            a = ":disappointed:"
        elif .2 < r and r < .4:
            a = ":pensive:"
        elif .4 < r and r < .6:
            a = ":cry:"
        elif .6 < r and r < .8:
            a = ":disappointed_relieved:"
        else:
            a = ":sob:"
    elif emotion == "surprise":
        if r < .333:
            a = ":dizzy_face:"
        elif .333 < r and r < .666:
            a = ":astonished:"
        else:
            a = ":open_mouth:"
    else:
        a = ":gear:"
    """to debug, we use a gear emoji. This means your emotion input string is bad."""
    return a


with open('emoji.json') as data_file:
    data = json.load(data_file)


def shortname_to_file(shortname):
    name = shortname[1:-1]
    return data[name]["unicode"] + ".png"

def get_emoji(emotion):
    shortname = emotion_to_shortname(emotion)
    filename = shortname_to_file(shortname)
    return filename