#extract the slides and the audio [x]
#calculate durations [x]
#create a new mp4[x] using FFmpeg

from selenium import webdriver
import time
from data_converter import data_converter

#data_extractor: processes the url into the playerDiv, extracts data from divs
class data_extractor:

    #use the driver to remove the playerDiv from the html from the url.
    def getPlayerDivFromURL(self, driver, url):
        driver.get(url)
        time.sleep(18) #wait for page to load

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
    def getTotalVidLength(self, inner_player):
        controls = inner_player.find_element_by_class_name("c-player__controls")
        currenttime = controls.find_element_by_class_name("c-player__current-time")
        duration = currenttime.find_element_by_class_name("c-player__duration")
        total_vid_length = duration.get_attribute('innerHTML')
        total_vid_length = str("00:" + total_vid_length)
        return total_vid_length



    #identify the slides in the slideshow, given playerDiv
    #for each slide, append img_url and timestamp to their respective lists.
    #return tuple containing both lists
    def get_slides_data(self, playerDiv, driver):
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




    def get_mp4_url(self, inner_player):
        #extract mp4 url
        vidWrapper = inner_player.find_element_by_class_name("c-player__video-wrapper")
        vid = vidWrapper.find_element_by_class_name("vjs-tech")
        mp4_url = vid.get_attribute("src")
        return mp4_url

    def get_inner_player_from_playerDiv(self, playerDiv):
        playerTop = playerDiv.find_element_by_class_name("c-bbb-player__top")
        player = playerTop.find_element_by_class_name("c-bbb-player__player")
        inner_player = player.find_element_by_class_name("c-player")
        return inner_player

def main():

    #data_extractor: processes the url into the playerDiv, extracts data from divs
    #data_processor: cleans up previous files from previous runs, converts mp4 to mp3, creates demuxer_txt, creates the lecture

    start_time = time.time()

    extractor = data_extractor()
    converter = data_converter()

    converter.clearLeftoverFiles()
    converter.deleteFileNameIfExists("lecture.mp4")



    driver = webdriver.Chrome(executable_path="C:\Program Files (x86)\chromedriver.exe")
    url = "recorded_bongo_lecture_URL"
    
    #use the driver to retrieve the player div from the url
    playerDiv = extractor.getPlayerDivFromURL(driver, url)

    #---from the playerdiv, put the slide data into the timeStamp_list and img_url_list, which are lists held in a tuple
    slidesData_tuple = extractor.get_slides_data(playerDiv, driver)

    #get the inner_player, because it holds the total_vid_length and the mp4_url...
    inner_player = extractor.get_inner_player_from_playerDiv(playerDiv)

    #---from the innerPlayer, get the total vid length and the mp4 url
    total_vid_length = extractor.getTotalVidLength(inner_player)
    mp4_url = extractor.get_mp4_url(inner_player)

    #done using webdriver
    driver.quit()

    #download the mp4_url to file called "audio.mp3"
    converter.mp4_to_mp3(mp4_url)

    #create demuxer txt for ffmpeg to use
    converter.create_demuxer_txt(total_vid_length, slidesData_tuple)

    converter.create_lecture_mp4()


    converter.clearLeftoverFiles()
    print("--- %s seconds ---" % (time.time() - start_time))

if __name__ == '__main__':
    main()