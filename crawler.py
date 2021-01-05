#this is a dynamically-generated webpage, ie using JS. have to scrape with selenium instead of beautifulSoup.
#extract the slides and the audio [x]
#calculate durations [x]
#problem of missing last duration value.
#a timestamp is when the image appears. so, if you wanted the duration of the last image appearing, you'd need the timestamp of the end of the video. (54:46)
#solution: find total length of the lecture, add that to the list of timestamps, and then you can calculate the desired 24 durations
#create a new mp4[x] using FFmpeg?


import os
import subprocess #needed to run ffmpeg commands
import glob
import urllib.request
from selenium import webdriver
from bs4 import BeautifulSoup
from moviepy.editor import *
import time
from datetime import timedelta

timeStamp_list = []
img_url_list = []
driver = webdriver.Chrome(executable_path="C:\Program Files (x86)\chromedriver.exe")

def getBongoPlayerFromURL():

    url = "https://bongo-ca.youseeu.com/spa/external-player/107762/cd7106029923b1e9a9ede8f229413946/styled?lti-scope=d2l-resource-syncmeeting-list"
    driver.get(url)
    time.sleep(15) #wait for page to load

    #isolate the player
    bongo_main = driver.find_element_by_class_name("bongo-main")
    bongo_app = bongo_main.find_element_by_class_name("bongo-app")
    page_debug_outline = bongo_app.find_element_by_class_name("page-debug-outline")
    page = page_debug_outline.find_element_by_class_name("page")
    container = page.find_element_by_class_name("container")
    content = container.find_element_by_class_name("content")
    paper = content.find_element_by_class_name("md-paper")
    playerDiv = paper.find_element_by_class_name("c-bbb-player")
    
    #from playerTop, extract 1) the total video length, and 2) extract the mp4
    playerTop = playerDiv.find_element_by_class_name("c-bbb-player__top")
    player = playerTop.find_element_by_class_name("c-bbb-player__player")
    inner_player = player.find_element_by_class_name("c-player")
    #1) extract total vid length
    #find video length

    controls = inner_player.find_element_by_class_name("c-player__controls")
    currenttime = controls.find_element_by_class_name("c-player__current-time")
    duration = currenttime.find_element_by_class_name("c-player__duration")
    total_vid_length = duration.get_attribute('innerHTML')
    total_vid_length = str("00:" + total_vid_length)

    #2) extract mp4
    vidWrapper = inner_player.find_element_by_class_name("c-player__video-wrapper")
    vid = vidWrapper.find_element_by_class_name("vjs-tech")
    mp4_url = vid.get_attribute("src")
    mp4_to_mp3(mp4_url) #LINE TO ENABLE MP3 DOWNLOAD

    #from player bottom, extract slides
    playerBottom = playerDiv.find_element_by_class_name("c-bbb-player__bottom")
    thumbnailsContainer = playerBottom.find_element_by_class_name("c-bbb-player__thumbnails")
    extractSlides(thumbnailsContainer)

    driver.quit()
    return total_vid_length

def downloadImages():
    counter = 0
    for imageURL in img_url_list:
        urllib.request.urlretrieve(imageURL, "images/img" + str(counter) + ".png")
        counter += 1

def emptyImagesFolder():
    files = glob.glob('images/*')
    for f in files:
        os.remove(f)

#convert to mp3
def mp4_to_mp3(url):
    #use the url, download as input.mp4
    urllib.request.urlretrieve(url, "input.mp4")
    time.sleep(5)

    #do the conversion
    videoClip = VideoFileClip("input.mp4")
    audioClip = videoClip.audio
    audioClip.write_audiofile("audio.mp3")
    audioClip.close()
    videoClip.close()

    #delete the mp4, if it exists.
    deleteFileNameIfExists("input.mp4")

def deleteFileNameIfExists(fileName):
    if os.path.exists(fileName):
        os.remove(fileName)

#extract the slides
def extractSlides(thumbnailsContainer):
    for thumb in thumbnailsContainer.find_elements_by_class_name("c-bbb-player__thumbnail"):
        #---IMG
        imgtag = thumb.find_element_by_class_name("c-bbb-player__thumbnail-image")
        imgsrc = imgtag.get_attribute("src")
        img_url_list.append(imgsrc)

        #---TIMESTAMP
        time_Ptag = thumb.find_element_by_class_name("c-bbb-player__thumbnail-time")
        driver.execute_script("arguments[0].style.visibility = 'visible'", time_Ptag)
        timestamp = time_Ptag.text
        timeStamp_list.append(timestamp)


#takes list of timestamps of format "HH:MM:SS"
#returns list of durations in seconds
def hms_to_seconds(t):
    h,m,s = t.split(':')
    secs = int(timedelta(hours=int(h),minutes=int(m),seconds=int(s)).total_seconds())
    return secs

def timestamps_to_durations(total_vid_length):
    durations = []
    frmat = '%H:%M:%S' #input format
    timeStamp_list.append(total_vid_length)
    #add the total vid length as the last timestamp. this is to calculate duration for the last image requires both the timestamp the image appears, and timestamp image is ended
    for count, item in enumerate(timeStamp_list):
        if count > 0:
            final  = hms_to_seconds(timeStamp_list[count])
            initial = hms_to_seconds(timeStamp_list[count-1])
            #get the difference in seconds
            durations.append(int((final - initial)))
    return durations


#using timeStamp_list and img_url_list
def create_demuxer_txt(total_vid_length):
    durations_list = timestamps_to_durations(total_vid_length)

    f = open("demuxerfile.txt", "w")
    images_list=os.listdir("images")

    #due to a quirk in ffmpeg, the last image file path needs to be written twice in the txt,
    #store the last image file path in this variable
    last_img_filepath = images_list[-1]

    for i, (duration, img_relative_path) in enumerate(zip(durations_list, images_list)):
        #this is the order to write to the text file...each f.write is one line.
        f.write("file " + "'images/" + img_relative_path + "'" + "\n")
        f.write("duration " + str(duration) + "\n")
        if i == (len(images_list) - 1): #you have reached the last index. b/c .py indicing starts at zero, the last index is one less than the element count.
            f.write("file " + "'images/" + last_img_filepath + "'")

    
    f.close()

    #slides only
    command = "ffmpeg -f concat -i demuxerfile.txt -vsync vfr -pix_fmt yuv420p slides.mp4"
    subprocess.call(command,shell=True)

    #adding audio
    cmd = "ffmpeg -i slides.mp4 -i audio.mp3 -c copy -map 0:v:0 -map 1:a:0 lecture.mp4"
    subprocess.call(cmd,shell=True)

def clearLeftoverFiles():
    emptyImagesFolder() #delete any files remaining from previous runs of code.
    deleteFileNameIfExists("audio.mp3")
    deleteFileNameIfExists("demuxerfile.txt")
    deleteFileNameIfExists("slides.mp4")

if __name__ == '__main__':
    clearLeftoverFiles()

    deleteFileNameIfExists("lecture.mp4")
    total_vid_length = getBongoPlayerFromURL()
    downloadImages() #LINE TO ENABLE IMAGE DOWNLOADING
    create_demuxer_txt(total_vid_length) #create new mp4

    clearLeftoverFiles()

