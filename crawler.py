#extract the slides and the audio [x]
#calculate durations [x]
#create a new mp4[x] using FFmpeg


import os
import subprocess #needed to run ffmpeg commands
import urllib.request
from selenium import webdriver
import time
from datetime import timedelta

#use the driver to remove the playerDiv from the html from the url.
def getPlayerDivFromURL(driver, url):
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

    return playerDiv

#takes a section of webElement, called "inner_player"
#returns total video length in HH:MM:SS format
def getTotalVidLength(inner_player):
    controls = inner_player.find_element_by_class_name("c-player__controls")
    currenttime = controls.find_element_by_class_name("c-player__current-time")
    duration = currenttime.find_element_by_class_name("c-player__duration")
    total_vid_length = duration.get_attribute('innerHTML')
    total_vid_length = str("00:" + total_vid_length)
    return total_vid_length

#takes mp4 url
#downloads the audio only as "audio.mp3"
def mp4_to_mp3(url):
    cmd = "ffmpeg -i " + url + " -vn audio.mp3"
    subprocess.call(cmd,shell=True)


def deleteFileNameIfExists(fileName):
    if os.path.exists(fileName):
        os.remove(fileName)

#identify the slides in the slideshow, given playerDiv
#for each slide, append img_url and timestamp to their respective lists.
def get_slides_data(playerDiv, driver):
    timeStamp_list = []
    img_url_list = []
    playerBottom = playerDiv.find_element_by_class_name("c-bbb-player__bottom")
    thumbnailsContainer = playerBottom.find_element_by_class_name("c-bbb-player__thumbnails")

    for thumb in thumbnailsContainer.find_elements_by_class_name("c-bbb-player__thumbnail"):
        #---IMG 
        img_url_list.append(thumb.find_element_by_class_name("c-bbb-player__thumbnail-image").get_attribute("src"))

        #---TIMESTAMP
        time_Ptag = thumb.find_element_by_class_name("c-bbb-player__thumbnail-time")
        driver.execute_script("arguments[0].style.visibility = 'visible'", time_Ptag) #set visible so selenium can see element
        timeStamp_list.append(time_Ptag.text)

    return (timeStamp_list, img_url_list)


#takes list of timestamps of format "HH:MM:SS"
#returns list of durations in seconds
def hms_to_seconds(t):
    h,m,s = t.split(':')
    secs = int(timedelta(hours=int(h),minutes=int(m),seconds=int(s)).total_seconds())
    return secs

#takes list of timestamps of format "HH:MM:SS"
#appends total_vid_length to list
#calculates list of durations for each image to appear in lecture.mp4
def timestamps_to_durations(timeStamp_list):
    durations = []
    frmat = '%H:%M:%S' #input format
    timeStamp_list.append(total_vid_length)
    #add the total vid length as the last timestamp. this is to calculate duration for the last image requires both the timestamp the image appears, and timestamp image is ended

    for i in range(1, len(timeStamp_list)):
        final  = hms_to_seconds(timeStamp_list[i])
        initial = hms_to_seconds(timeStamp_list[i-1])
        durations.append(int((final - initial)))         #get the difference in seconds
    return durations


#using timeStamp_list and img_url_list, create txt file for ffmpeg to make into mp4 w/o audio
def create_demuxer_txt(total_vid_length, slidesData_tuple):
    #unpack tuple into slides data lists
    timeStamp_list, img_url_list = slidesData_tuple

    #the last slide requires both timestamp slide appears, and the time the video ends to calculate duration
    timeStamp_list.append(total_vid_length)

    #durations for how long each slide appears
    durations_list = timestamps_to_durations(timeStamp_list)

    f = open("demuxerfile.txt", "w")

    #due to a quirk in ffmpeg, the last_img_url will need to be written twice in the txt,
    last_img_url = img_url_list[-1]

    for i, (duration, img_url) in enumerate(zip(durations_list, img_url_list)):
        #this is the order to write to the text file...each f.write is one line.
        f.write("file " + "'" + img_url + "'" + "\n")
        f.write("duration " + str(duration) + "\n")

        if i == (len(img_url_list) - 1): #if at last index, write last_img_url again.
            f.write("file " + "'" + last_img_url + "'")

    
    f.close()

    durations_list.clear()
    img_url_list.clear()


#create the final lecture.mp4 of both audio and slides
def create_lecture_mp4():
    #creates an mp4 of slides only, called "slides.mp4"
    command = "ffmpeg -f concat -safe 0 -protocol_whitelist file,http,https,tcp,tls -i demuxerfile.txt -vsync vfr -pix_fmt yuv420p slides.mp4"
    subprocess.call(command,shell=True)

    #adding audio
    cmd = "ffmpeg -i slides.mp4 -i audio.mp3 -c copy -map 0:v:0 -map 1:a:0 lecture.mp4"
    subprocess.call(cmd,shell=True)

#clear all files other than lecture.mp4 and this file(crawler.py)
def clearLeftoverFiles():
    deleteFileNameIfExists("audio.mp3")
    deleteFileNameIfExists("demuxerfile.txt")
    deleteFileNameIfExists("slides.mp4")


def get_mp4_url(inner_player):
    #extract mp4 url
    vidWrapper = inner_player.find_element_by_class_name("c-player__video-wrapper")
    vid = vidWrapper.find_element_by_class_name("vjs-tech")
    mp4_url = vid.get_attribute("src")
    return mp4_url

def get_inner_player_from_playerDiv(playerDiv):
    playerTop = playerDiv.find_element_by_class_name("c-bbb-player__top")
    player = playerTop.find_element_by_class_name("c-bbb-player__player")
    inner_player = player.find_element_by_class_name("c-player")
    return inner_player

if __name__ == '__main__':
    start_time = time.time()
    clearLeftoverFiles()
    deleteFileNameIfExists("lecture.mp4")



    driver = webdriver.Chrome(executable_path="C:\Program Files (x86)\chromedriver.exe")
    url = "https://bongo-ca.youseeu.com/spa/external-player/107762/cd7106029923b1e9a9ede8f229413946/styled?lti-scope=d2l-resource-syncmeeting-list"
    playerDiv = getPlayerDivFromURL(driver, url) #retrieve the player div

    #---from the playerdiv, put the slide data into the timeStamp_list and img_url_list, which are lists held in a tuple
    slidesData_tuple = get_slides_data(playerDiv, driver)

    #get the inner_player, because it holds the total_vid_length and the mp4_url...
    inner_player = get_inner_player_from_playerDiv(playerDiv)

    #---from the innerPlayer, get the total vid length and the mp4 url
    total_vid_length = getTotalVidLength(inner_player)
    mp4_url = get_mp4_url(inner_player)

    #done using webdriver
    driver.quit()

    #download the mp4_url to file called "audio.mp3"
    mp4_to_mp3(mp4_url)
    create_demuxer_txt(total_vid_length, slidesData_tuple) #create demuxer txt for ffmpeg to use
    create_lecture_mp4()



    clearLeftoverFiles()
    print("--- %s seconds ---" % (time.time() - start_time))