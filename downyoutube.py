import sys, traceback
import io
import os
import os.path
import json
import re
import time
from builtins import str

def downyoutube_main():

    count = 0

    os.chdir("D:/网页抓取/youtube_data")
    base_title_url = "https://www.youtube.com"
    dgtle_dup = {}
    if os.path.exists("youtube_dup.json"):
        dgtle_dup = json.loads(io.open("youtube_dup.json", 'r', encoding='utf-8').read())
    else:
        return


    for tag in dgtle_dup:
        url = base_title_url + tag
        filename = tag.split("=")[1]
        command1 = "youtube-dl -o "
        command2 = " --proxy \"https://web-proxy.tencent.com:8080/\" -f 134+140 --write-thumbnail"
        final_command = command1 + filename + " " + url + command2
        print(final_command)
        os.system(final_command)
        mvmp4 = "mv ./*.mp4 MP4"
        mvimg = "mv ./*.jpg img"
    os.system(mvimg)
    os.system(mvmp4)


if __name__ == "__main__":
    downyoutube_main()