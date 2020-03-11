<<<<<<< HEAD
=======

import youtube_dl
import re
import urllib
 
import os,sys
from typing import Any,List
import time



start_time = time.time()

link1 = "PLN1mxegxWPd3d8jItTyrAxwm-iq-KrM-e"
query = "Music to be murdered by"
query2 = "Godzilla"
linkid = "3qFvCPmee8U"
queue_path = os.path.abspath(f"./Try/%(id)s.%(ext)s")

query_string = urllib.parse.urlencode({"search_query": query})
html_content = urllib.request.urlopen(
    "http://www.youtube.com/results?" + query_string)
search_results = re.findall(
    r'href=\"\/playlist\?list=(.*)\" class=', html_content.read().decode())
print(search_results[:5])


#     print(info["thumbnails"],info["duration"])
#with youtube_dl.YoutubeDL(ydl_opts) as ydl:
#    info = ydl.extract_info(link1,download = False)
    


print("--- %s seconds ---" % (time.time() - start_time))
>>>>>>> 4031def7ba545a05bfa4b55af653d4c78f65bdbd
