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

# Variables
_urlImgAPI = 'https://api.projectoxford.ai/emotion/v1.0/recognize'
# _urlVidAPI = 'https://api.projectoxford.ai/emotion/v1.0/recognizeinvideo'
_imgKey = '56abb73c70d649c395df24fe8c5f0d01'
# _vidKey = '6d733f1bc1e14010ac21969564926a56'
_maxNumRetries = 10
# generate random filename
_filename = str(uuid.uuid4()).split('-')[0] + '.jpg'

# def main():
#     emojify('http://s3.amazonaws.com/etntmedia/media/images/ext/543627202/happy-people-friends.jpg')

def emojify(urlImage):
    faceList = analyze_face(urlImage, 'prod')
    emojifiedurl = draw_emoji(urlImage, faceList)
    print(emojifiedurl)
    return emojifiedurl

def analyze_face(urlImage, mode):
    headers = dict()
    headers['Ocp-Apim-Subscription-Key'] = _imgKey
    headers['Content-Type'] = 'application/json'

    json = {'url': urlImage}
    data = None
    params = None

    result = processImgRequest(json, _urlImgAPI, data, headers, params)

    if result is not None:
        if mode == 'test':
            print("face found")
    else:
        print("face not found")

    return result    

def draw_emoji(urlImage, faceList):
    imgArr = np.asarray(bytearray(requests.get(urlImage).content), 
                        dtype=np.uint8)
    img = cv2.imdecode(imgArr, 1)

    b, g, r = cv2.split(img)
    a = np.ones((img.shape[0], img.shape[1])).astype(np.uint8) #creating a dummy alpha channel image.
    img = cv2.merge((b, g, r, a))

    for face in faceList:
        faceRect = face['faceRectangle']
        emotion = max(face['scores'].items(), 
                      key=operator.itemgetter(1))[0]

        center = (int(faceRect['left'] + (faceRect['width'] / 2)),
                  int(faceRect['top'] + (faceRect['height'] / 2)))

        path = './png/'
        emoji = cv2.imread(path + get_emoji(emotion), -1)

        (b,g,r,a) = cv2.split(emoji)

        offset = int(0.45 * faceRect['width'])

        (width, height) = (faceRect['width']  + offset, 
                           faceRect['height'] + offset)

        emoji = cv2.resize(emoji, (width, height))

        yfrom = int(faceRect['top'] - (offset/2))
        yfrom = max(0, yfrom)

        yto   = int(faceRect['top'] + emoji.shape[1] - (offset/2))
        yto   = min(img.shape[0], yto)

        ydist = yto - yfrom

        yfrom_emj = 0
        yto_emj = 0
        if yto == img.shape[0]:
            yfrom_emj = 0
            yto_emj = ydist
        elif yfrom == 0:
            yfrom_emj = emoji.shape[0]-ydist
            yto_emj = emoji.shape[0]
        else:
            yfrom_emj = 0
            yto_emj = emoji.shape[0]

        xfrom = int(faceRect['left'] - (offset/2))
        xfrom = max(0, xfrom)

        xto   = int(faceRect['left'] + emoji.shape[0] - (offset/2))
        xto   = min(img.shape[1], xto)

        xdist = xto - xfrom

        xfrom_emj = 0
        xto_emj = 0
        if xto == img.shape[1]:
            xfrom_emj = 0
            xto_emj = xdist
        elif xfrom == 0:
            xfrom_emj = emoji.shape[1]-xdist
            xto_emj = emoji.shape[1]
        else:
            xfrom_emj = 0
            xto_emj = emoji.shape[1]

        # print("yto-yfrom", yto-yfrom, "xto-xfrom", xto-xfrom)
        # print("yto_emj-yfrom_emj", yto_emj-yfrom_emj, "xto_emj-xfrom_emj", xto_emj-xfrom_emj)

        for c in range(0,3):
            img[yfrom:yto,xfrom:xto,c] = emoji[yfrom_emj:yto_emj,xfrom_emj:xto_emj,c] * (emoji[yfrom_emj:yto_emj,xfrom_emj:xto_emj,3]/255.0) + img[yfrom:yto,xfrom:xto,c] * (1.0 - emoji[yfrom_emj:yto_emj,xfrom_emj:xto_emj,3]/255.0)

    # cv2.imshow("asdf", img)
    # cv2.waitKey(0)
    tempPath = '/tmp/result.jpg'
    cv2.imwrite(tempPath, img)

    uploadToDropbox(tempPath)
    cloudPath = getImageDropboxUrl()
    return cloudPath

# Helper functions
def processImgRequest(json, url, data, headers, params):
    retries = 0
    result = None

    while True:
        # get response
        resp = requests.request('post', url=url,
                                    json=json, data=data, 
                                    headers=headers, params=params)
        
        # fields
        lenf = 'content-length'
        typef = 'content-type'

        # rate limit exceeded
        if resp.status_code == 429:
            print("Message: %s" % (resp.json()['error']['message']))

            if retries <= _maxNumRetries:
                time.sleep(1)
                retries += 1
                continue
            else:
                print('Error: failed after retrying!')
                break

        # successful call
        elif resp.status_code == 200 or resp.status_code == 201:
            if lenf in resp.headers and int(resp.headers[lenf]) == 0:
                result = None
            elif typef in resp.headers and isinstance(resp.headers[typef], str):
                if 'application/json' in resp.headers[typef].lower():
                    result = resp.json() if resp.content else None
                elif 'image' in resp.headers[typef].lower():
                    result = resp.content

        else:
            print("Error code: %d" % (resp.status_code))
            print("Message: %s" % (resp.json()['error']['message']))

        break

    return result

def drawFace(result, img):
    for face in result:
        faceRect = face['faceRectangle']
        cv2.rectangle(img, (faceRect['left'], 
                            faceRect['top']), 
                           (faceRect['left'] + faceRect['width'], 
                            faceRect['top']  + faceRect['height']), 
                           color=(255,0,0), thickness=5 )

    for face in result:
        faceRect = face['faceRectangle']
        emotion = max(face['scores'].items(), 
                      key=operator.itemgetter(1))[0]

        textToWrite = "%s" % (emotion)
        cv2.putText(img, textToWrite, (faceRect['left'], 
                                       faceRect['top']-10),
                                       cv2.FONT_HERSHEY_SIMPLEX,
                                       0.5, (255,0,0), 1)

def uploadToDropbox(localPath):
    """Upload image at localPath to Dropbox folder
    """
    access_token = "Aj1lmASJYSwAAAAAAAAnLdLWt52qVuQPAu0HuOfH9UGsQoPF1f2_oggtEdKcVkFV"
    url = "https://content.dropboxapi.com/2/files/upload"

    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/octet-stream",
        "Dropbox-API-Arg": "{\"path\":\"/" + _filename + "\"}"
    }

    data = open(localPath, "rb").read()

    r = requests.post(url, headers=headers, data=data)

    if r.status_code == 200: 
        print("Upload to Dropbox successful")
        sys.stdout.flush()
    else:
        print("Failed to upload to Dropbox")
        sys.stdout.flush() 
        exit()

def getImageDropboxUrl():
    """Get a URL to where the emojified image is hosted on Dropbox
    """
    access_token = "Aj1lmASJYSwAAAAAAAAnLdLWt52qVuQPAu0HuOfH9UGsQoPF1f2_oggtEdKcVkFV"
    url = "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings"

    headers = {
        "Authorization": "Bearer " + access_token,
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

    r = requests.post(url, headers=headers, data=json.dumps(data))

    if r.status_code == 200: 
        idurl = (r.json())['url'].split('com')[1]
        print("Shared link created")
        sys.stdout.flush()
        return 'https://dl.dropboxusercontent.com' + idurl
    else:
        print("Failed to get Dropbox link to image")
        sys.stdout.flush()
        exit()

# if __name__ == "__main__":
#     main()