#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from get_emoji import get_emoji
import dropbox
import time 
import requests
import cv2
import operator
import numpy as np 
import base64
import time
import uuid
import json
import sys
import os

# Variables
# URL to access the Emotion API of Microsoft Cognitive Services
_emotionUrl = 'https://api.projectoxford.ai/emotion/v1.0/recognize'
# Microsoft Cognitive Services API Key
_msftAPIKey = os.environ['MSFT_COGNITIVE_API_KEY']
# URL to access the 'upload' functionality of the Dropbox API
_uploadUrl = 'https://content.dropboxapi.com/2/files/upload'
# URL to acess the 'get shared link' functionality of the Dropbox API
_getlinkUrl = 'https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings'
# Dropbox API access token
_dbxAPIToken = os.environ['DROPBOX_API_TOKEN']
# No. of times program tries to call Emotion API before throwing error 
_maxNumRetries = 10
# generate random filename for emojified image in Dropbox folder
_filename = str(uuid.uuid4()).split('-')[0] + '.jpg'

def main():
    emojify('http://s3.amazonaws.com/etntmedia/media/images/ext/543627202/happy-people-friends.jpg')

def emojify(imageurl):
    """Emojifies (i.e replaces faces with emoji
    of the corresponding emotion) the image at the path urlImage

    Args
    urlImage: url at which image is accessible

    Returns
    emojifiedurl: url at which emojified image is accessible 
    """
    faceList = analyze_face(imageurl)
    emojifiedurl = draw_emoji(imageurl, faceList)
    return emojifiedurl

def analyze_face(urlImage):
    """Analyzes faces in an image

    Args
    urlImage: url at which image is accessible

    Return
    result: list of facial data (emotion probabilities and facial 
    coordinates) for each face detected in image
    """
    headers = dict()
    headers['Ocp-Apim-Subscription-Key'] = _msftAPIKey
    headers['Content-Type'] = 'application/json'

    json = {'url': urlImage}
    data = None
    params = None

    result = None
    retries = 0

    while True:
        # get response
        r = requests.request('post', 
            url=_emotionUrl, json=json, data=data, headers=headers, 
            params=params)

        # rate limit exceeded
        if r.status_code == 429:
            print("Message: %s" % (r.json()['error']['message']))
            if retries <= _maxNumRetries:
                time.sleep(1)
                retries += 1
                continue
            else:
                print('Error: failed after retrying!')
                break

        # successful call
        elif r.status_code == 200 or r.status_code == 201:
            if 'content-length' in r.headers and int(r.headers['content-length']) == 0:
                result = None
            elif 'content-type' in r.headers and isinstance(r.headers['content-type'], str):
                if 'application/json' in r.headers['content-type'].lower():
                    result = r.json() if r.content else None
                elif 'image' in r.headers['content-type'].lower():
                    result = r.content

        else:
            print("Error code: %d" % (r.status_code))
            print("Message: %s" % (r.json()['error']['message']))

        break

    if result:
        print("Facial analysis successful")
        sys.stdout.flush()
        return result    
    else:
        print("Facial analysis unsuccesful")
        sys.stdout.flush()
        exit()

def draw_emoji(urlImage, faceList):
    """Draws emoji of the corresponding emotion on faces in the image

    Args
    urlImage: url at which image is accessible
    faceList: list of facial data (coordinates, emotion) of each face
    in the image
    """

    # download image from urlImage and convert it into a matrix
    # accessible to OpenCV
    imgArr = np.asarray(bytearray(requests.get(urlImage).content), 
                        dtype=np.uint8)
    img = cv2.imdecode(imgArr, 1)

    # create alpha channel to allow addition of emoji png w/ transparent
    # background onto image
    b, g, r = cv2.split(img)
    #creating a dummy alpha channel
    a = np.ones((img.shape[0], img.shape[1])).astype(np.uint8) 
    img = cv2.merge((b, g, r, a))

    # draw emoji in image
    img = draw_face(img, faceList)

    # save image on temporary folder in local machine
    tempPath = '/tmp/result.jpg'
    cv2.imwrite(tempPath, img)

    # upload image to Dropbox and retrieve link that FB Messenger 
    # can access
    uploadToDropbox(tempPath)
    cloudPath = getImageDropboxUrl()

    return cloudPath

def draw_face(img, faceList):
    """Draws emoji of corresponding emotion onto faces in image

    Args
    img: image 
    faceList: list of facial data (e.g coordinates, emotion) for each
    face in the image

    Return
    img: emojified image
    """
    for face in faceList:
        # get emoji of corresponding emotion
        emotion = max(face['scores'].items(), 
                      key=operator.itemgetter(1))[0]
        emoji = cv2.imread('./png/' + get_emoji(emotion), -1)

        coor = face['faceRectangle']
        center = (int(coor['left'] + (coor['width'] / 2)),
                  int(coor['top'] + (coor['height'] / 2)))

        (b,g,r,a) = cv2.split(emoji)
        offset = int(0.45 * coor['width'])

        (width, height) = (coor['width'] + offset, 
                           coor['height'] + offset)

        emoji = cv2.resize(emoji, (width, height))

        # calculate y coordinates of 'rectangle' of image 
        # that will be overlaid with emoji
        yfrom = max(0, int(coor['top'] - (offset/2)))
        yto   = min(img.shape[0], 
                    int(coor['top'] + emoji.shape[1] - (offset/2)))

        # calculates y coordinates of emoji
        # that will be overlaid onto image
        ydist = yto - yfrom

        yfrom_e = 0
        yto_e = 0
        if yto == img.shape[0]:
            yto_e = ydist
        elif yfrom == 0:
            yfrom_e = emoji.shape[0]-ydist
            yto_e = emoji.shape[0]
        else:
            yto_e = emoji.shape[0]

        # calculate x coordinates of 'rectangle' of image 
        # that will be overlaid with emoji
        xfrom = max(0, int(coor['left'] - (offset/2)))
        xto   = min(img.shape[1], 
                    int(coor['left'] + emoji.shape[0] - (offset/2)))

        # calculates x coordinates of emoji
        # that will be overlaid onto image
        xdist = xto - xfrom

        xfrom_e = 0
        xto_e = 0
        if xto == img.shape[1]:
            xto_e = xdist
        elif xfrom == 0:
            xfrom_e = emoji.shape[1]-xdist
            xto_e = emoji.shape[1]
        else:
            xto_e = emoji.shape[1]

        # overlay emoji onto image
        for c in range(0,3):

            img[yfrom:yto,xfrom:xto,c] = \
                emoji[yfrom_e:yto_e,xfrom_e:xto_e,c] * \
                (emoji[yfrom_e:yto_e,xfrom_e:xto_e,3]/255.0) + \
                img[yfrom:yto,xfrom:xto,c] * \
                (1.0 - emoji[yfrom_e:yto_e,xfrom_e:xto_e,3]/255.0)

    return img

def uploadToDropbox(localPath):
    """Upload image to Dropbox folder

    Args
    localPath: path to image stored on local machine
    """
    headers = {
        "Authorization": "Bearer " + _dbxAPIToken,
        "Content-Type": "application/octet-stream",
        "Dropbox-API-Arg": "{\"path\":\"/" + _filename + "\"}"
    }

    data = open(localPath, "rb").read()

    r = requests.post(_uploadUrl, headers=headers, data=data)

    if r.status_code == 200: 
        print("Upload to Dropbox successful")
        sys.stdout.flush()
    else:
        print("Failed to upload to Dropbox")
        sys.stdout.flush() 
        exit()

def getImageDropboxUrl():
    """Get a URL to where the emojified image is hosted on Dropbox

    Return
    cloudurl: url to hosted image in Dropbox folder
    """
    headers = {
        "Authorization": "Bearer " + _dbxAPIToken,
        "Content-Type": "application/json"
    }

    data = {
        "path": "/" + _filename,
        "settings" : {
            "requested_visibility": {
                ".tag" : "public"
            }
        }
    }

    r = requests.post(_getlinkUrl, headers=headers, data=json.dumps(data))

    if r.status_code == 200: 
        idurl = (r.json())['url'].split('com')[1]
        print("Shared link created")
        sys.stdout.flush()
        return 'https://dl.dropboxusercontent.com' + idurl
    else:
        print("Failed to get Dropbox link to image")
        sys.stdout.flush()
        exit()

if __name__ == "__main__":
    main()