import os
import subprocess #needed to run ffmpeg commands

#data_converter: cleans up previous files from previous runs, converts mp4 to mp4, creates demuxer_txt, creates the lecture
class data_converter:

    def deleteFileNameIfExists(self, fileName):
        if os.path.exists(fileName):
            os.remove(fileName)

    #use deleteFileNameIfExists to clear all files other than lecture.mp4 and this file(crawler.py)
    def clearLeftoverFiles(self):
        self.deleteFileNameIfExists("audio.mp3")
        self.deleteFileNameIfExists("demuxerfile.txt")
        self.deleteFileNameIfExists("slides.mp4")

    #takes mp4 url
    #downloads the audio only as "audio.mp3"
    def mp4_to_mp3(self, url):
        cmd = "ffmpeg -i " + url + " -vn audio.mp3"
        subprocess.call(cmd,shell=True)


    #takes list of timestamps of format "HH:MM:SS"
    #returns list of durations in seconds
    def hms_to_seconds(self, t):
        h,m,s = t.split(':')
        return (int(h)*3600 + int(m)*60 + int(s))

    #takes list of timestamps of format "HH:MM:SS"
    #appends total_vid_length to list
    #calculates list of durations for each image to appear in lecture.mp4
    def timestamps_to_durations(self, timeStamp_list):
        durations = []
        #add the total vid length as the last timestamp. this is to calculate duration for the last image requires both the timestamp the image appears, and timestamp image is ended

        for i in range(1, len(timeStamp_list)):
            # final  = hms_to_seconds(timeStamp_list[i])
            # initial = hms_to_seconds(timeStamp_list[i-1])
            # durations.append(final - initial)         #get the difference in seconds
            durations.append(self.hms_to_seconds(timeStamp_list[i]) - self.hms_to_seconds(timeStamp_list[i-1]))
        return durations


    #using timeStamp_list and img_url_list, create txt file for ffmpeg to make into mp4 w/o audio
    def create_demuxer_txt(self, total_vid_length, slidesData_tuple):
        #unpack tuple into slides data lists
        timeStamp_list, img_url_list = slidesData_tuple

        #the last slide requires both timestamp slide appears, and the time the video ends to calculate duration
        timeStamp_list.append(total_vid_length)

        #durations for how long each slide appears
        durations_list = self.timestamps_to_durations(timeStamp_list)

        f = open("demuxerfile.txt", "w")

        #due to a quirk in ffmpeg, the last_img_url will need to be written twice in the txt,
        last_img_url = img_url_list[-1]

        for i, (duration, img_url) in enumerate(zip(durations_list, img_url_list)):
            #this is the order to write to the text file...each f.write is one line.
            f.write("file " + "'" + img_url + "'" + "\n")
            f.write("duration " + str(duration) + "\n")

        f.write("file " + "'" + last_img_url + "'") #write last img url again.
        
        f.close()

        durations_list.clear()
        img_url_list.clear()


    #create the final lecture.mp4 of both audio and slides
    def create_lecture_mp4(self):
        #creates an mp4 of slides only, called "slides.mp4"
        command = "ffmpeg -f concat -safe 0 -protocol_whitelist file,http,https,tcp,tls -i demuxerfile.txt -vsync vfr -pix_fmt yuv420p slides.mp4"
        subprocess.call(command,shell=True)

        #adding audio
        cmd = "ffmpeg -i slides.mp4 -i audio.mp3 -c copy -map 0:v:0 -map 1:a:0 lecture.mp4"
        subprocess.call(cmd,shell=True)