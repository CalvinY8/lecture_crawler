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

    #from player bottom, extract slides
    playerBottom = playerDiv.find_element_by_class_name("c-bbb-player__bottom")
    thumbnailsContainer = playerBottom.find_element_by_class_name("c-bbb-player__thumbnails")
    extractSlides(thumbnailsContainer)

    driver.quit()
    mp4_to_mp3(mp4_url) #LINE TO ENABLE MP3 DOWNLOAD
    return total_vid_length

#convert to mp3
def mp4_to_mp3(url):
    #use the url, download as input.mp4
    urllib.request.urlretrieve(url, "input.mp4")
    # time.sleep(5)

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
        img_url_list.append(imgtag.get_attribute("src"))

        #---TIMESTAMP
        time_Ptag = thumb.find_element_by_class_name("c-bbb-player__thumbnail-time")
        driver.execute_script("arguments[0].style.visibility = 'visible'", time_Ptag) #set visible so selenium can see element
        timeStamp_list.append(time_Ptag.text)


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

    for i in range(1, len(timeStamp_list)):
        final  = hms_to_seconds(timeStamp_list[i])
        initial = hms_to_seconds(timeStamp_list[i-1])
        durations.append(int((final - initial)))         #get the difference in seconds
    return durations


#using timeStamp_list and img_url_list
def create_demuxer_txt(total_vid_length):
    durations_list = timestamps_to_durations(total_vid_length)

    f = open("demuxerfile.txt", "w")

    #due to a quirk in ffmpeg, the last image file path needs to be written twice in the txt,
    #store the last image file path in this variable
    last_img_url = img_url_list[-1]

    for i, (duration, img_url) in enumerate(zip(durations_list, img_url_list)):
        #this is the order to write to the text file...each f.write is one line.
        f.write("file " + "'" + img_url + "'" + "\n")
        f.write("duration " + str(duration) + "\n")
        if i == (len(img_url_list) - 1): #you have reached the last index. b/c .py indicing starts at zero, the last index is one less than the element count.
            f.write("file " + "'" + last_img_url + "'")

    
    f.close()

    durations_list.clear()
    img_url_list.clear()

    #slides only
    command = "ffmpeg -f concat -safe 0 -protocol_whitelist file,http,https,tcp,tls -i demuxerfile.txt -vsync vfr -pix_fmt yuv420p slides.mp4"
    subprocess.call(command,shell=True)

    #adding audio
    cmd = "ffmpeg -i slides.mp4 -i audio.mp3 -c copy -map 0:v:0 -map 1:a:0 lecture.mp4"
    subprocess.call(cmd,shell=True)

def clearLeftoverFiles():
    deleteFileNameIfExists("audio.mp3")
    deleteFileNameIfExists("demuxerfile.txt")
    deleteFileNameIfExists("slides.mp4")

if __name__ == '__main__':
    start_time = time.time()

    clearLeftoverFiles()

    deleteFileNameIfExists("lecture.mp4")
    total_vid_length = getBongoPlayerFromURL()
    create_demuxer_txt(total_vid_length) #create new mp4

    clearLeftoverFiles()

    print("--- %s seconds ---" % (time.time() - start_time))