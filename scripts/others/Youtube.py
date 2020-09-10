
from selenium import webdriver 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By 
import re
import urllib.request
import urllib.parse
from typing import List,Any
from selenium.webdriver.chrome.options import Options
import youtube_dl
import os.path 
import math
import tracemalloc
tracemalloc.start()

chrome_options = Options()
chrome_options.add_argument("disable-extensions")
chrome_options.add_argument("disable-gpu")
chrome_options.add_argument("headless")
chrome_options.add_argument("log-level=3")

driver = webdriver.Chrome(chrome_options = chrome_options, executable_path=os.path.abspath("./Bin/chromedriver.exe")) 

driver.get("http://www.youtube.com")

millnames = ['','K','M','B']

def millify(n):
    n = float(n)
    millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return f'{round(n / 10**(3 * millidx),2)} {millnames[millidx]}'


class YoutubeVideo:
    def __init__(self, id: str,info:dict = None,requested_by:str = None):
        self.id = id
        self._requester = requested_by
        

        if not info:
            self._info = self.info
        else:
            self._info = info

    @classmethod
    def from_query(cls, query: str , amount:int = 1):

        wait = WebDriverWait(driver, 30)

        query_string = urllib.parse.urlencode({"search_query": query})
                
        driver.get("http://www.youtube.com/results?" + query_string)
        search_results = wait.until(EC.presence_of_all_elements_located(
                                        (By.CSS_SELECTOR,"ytd-thumbnail-overlay-time-status-renderer span")))[:amount]

        entries_list : List[Any]=[]
        
        for element in search_results:
            try:
                duration = element.text
                driver.execute_script("arguments[0].scrollIntoView();", element)
                ytd_thumbnail_overlay = driver.execute_script("return arguments[0].parentNode;", element)
                div = driver.execute_script("return arguments[0].parentNode;", ytd_thumbnail_overlay)
                link = driver.execute_script("return arguments[0].parentNode;", div)
                thumbnail = driver.execute_script("return arguments[0].parentNode;", link)
                video = driver.execute_script("return arguments[0].parentNode;", thumbnail)
        
                name = video.find_element_by_css_selector("h3").text
                channel_name = video.find_element_by_css_selector("ytd-channel-name").text
            except:
                pass
            else:
                split_list = re.split("/|=|&",link.get_attribute("href"))
                entries_list += [[(split_list[split_list.index("watch?v")+1]),name,channel_name,duration]]   
        return entries_list

    def __len__(self) -> int:
        return self.seconds

    def __lt__(self, other) -> bool:
        if not isinstance(other, YoutubeVideo):
            return NotImplemented

        return self.seconds < other.seconds

    def __gt__(self, other) -> bool:
        if not isinstance(other, YoutubeVideo):
            return NotImplemented

        return self.seconds > other.seconds

    def __eq__(self, other) -> bool:   # type: ignore
        if not isinstance(other, YoutubeVideo):
            return NotImplemented

        return self.id == other.id

    def __ne__(self, other) -> bool:   # type: ignore
        if not isinstance(other, YoutubeVideo):
            return NotImplemented

        return self.id != other.id

    def __str__(self) -> str:
        return f"{self.title} ({self.duration}) - {self.uploader}"

    @property
    def info(self) -> dict:
        ydl_opts = {
            'format': 'bestaudio',
            'quiet': True,
        } 
        
        need = ["id",
                "uploader",
                "upload_date",
                "title",
                "thumbnail",
                "description",
                "duration",
                "webpage_url",
                "view_count",
                "like_count",
                "dislike_count",
                "thumbnails",
                "format_id",
                "url",
                "ext"
                ]
        
        info = youtube_dl.YoutubeDL(ydl_opts).extract_info(self.id,download = False)
    
        info2 = {}
        for i in need:
            info2[i] = info[i]
        return info2

    @property
    def uploader(self) -> str:
        return self._info["uploader"]

    @property
    def likes(self) -> str:
        if self._info["like_count"]:
            return millify(self._info["like_count"])
        else:
            return None
    
    @property
    def dislikes(self) -> str:
        if self._info["dislike_count"]:
            return millify(self._info["dislike_count"])
        else:
            return None
    
    @property
    def views(self) -> str:
        if self._info["view_count"]:
            return millify(self._info["view_count"])
        else:
            return None
    
    @property
    def date(self) -> str:
        _date=self._info["upload_date"]
        if _date:
            return "-".join([_date[:4],_date[4:6],_date[6:]])
        else:
            return None

    @property
    def ext(self) -> str:
        return self._info["ext"]

    @property
    def thumbnails(self) -> str:
        return self._info["thumbnails"]
    
    @property
    def thumbnail(self) -> str:
        return self._info["thumbnail"]

    @property
    def url(self) -> str:
        return self._info["webpage_url"]

    @property
    def title(self) -> str:
        return self._info["title"]
    
    @property
    def description(self) -> str:
        return self._info["description"]

    @property
    def requester(self) -> str:
        return self._requester

    @property
    def audio_url(self) -> str:
        return self._info["url"]
    
    @property
    def duration_dict(self) -> dict:

        duration = self._info["duration"]

        time = {"H":0, "M":0, "S":0}


        time["S"] = int(duration)%60
        time["M"] = (int(duration)%3600)//60
        time["H"] = int(duration)//3600

        return time


    @property
    def duration(self) -> str:
        time = self.duration_dict
        def two_dig(number):
            if len(number)==1:
                return f"0{number}"
            else:
                return (number)
        for x in time:
            time[x] = str(time[x])
            if x != "H":
                time[x] = two_dig(time[x])
        
               
        if time["H"] == "0":
            return ":".join(list(time.values())[1:])
        else:
            return ":".join(list(time.values()))


    

    @property
    def seconds(self) -> int:
        return self._info["duration"] 



class YoutubePlaylist:

    def __init__(self,id:str,info:dict = None,requested_by:str = None):
        self.id = id
        self._requester = requested_by
      
        
        if not info:
            self._info = self.info
        else:
            self._info = info


    @classmethod
    def from_query(cls, query: str , amount:int = 1,requested_by:str = None):

        yl = []
        
        wait = WebDriverWait(driver, 10)

        query_string = urllib.parse.urlencode({"search_query": query})
                
        driver.get("http://www.youtube.com/results?" + query_string)
        search_results = wait.until(EC.presence_of_all_elements_located(
                                        (By.CSS_SELECTOR,"ytd-playlist-thumbnail a")))[:amount]
        
        for link in search_results:
            try:
                driver.execute_script("arguments[0].scrollIntoView();", link)
                split_list = re.split("/|=|&",link.get_attribute("href"))
                
            except:
                pass
            else: 
                yl += [split_list[split_list.index("list")+1]]    
                
        if requested_by:
            return [cls(x,requested_by=requested_by) for x in yl]
        else:
            return [cls(x) for x in yl]

    def __len__(self) -> int:
        return self.seconds

    def __lt__(self, other) -> bool:
        if not isinstance(other, YoutubePlaylist):
            return NotImplemented

        return self.seconds < other.seconds

    def __gt__(self, other) -> bool:
        if not isinstance(other, YoutubePlaylist):
            return NotImplemented

        return self.seconds > other.seconds

    def __eq__(self, other) -> bool:   # type: ignore
        if not isinstance(other, YoutubePlaylist):
            return NotImplemented

        return self.id == other.id

    def __ne__(self, other) -> bool:   # type: ignore
        if not isinstance(other, YoutubePlaylist):
            return NotImplemented

        return self.id != other.id
    
    def __str__(self) -> str:
        return f'{self.title} ({self.duration}) - {self.uploader}'

    @property
    def info(self) -> dict:
    
        wait = WebDriverWait(driver, 10)

        info = {}
        info["id"] = self.id
        
        info["url"] = f"https://www.youtube.com/playlist?list={info['id']}"

 

        driver.get(info["url"])

        info["title"] = wait.until(EC.presence_of_element_located(
                                (By.CSS_SELECTOR,"h1#title yt-formatted-string"))).text
        stats = wait.until(EC.presence_of_all_elements_located(
                                (By.CSS_SELECTOR,"div#stats yt-formatted-string")))

        info["views"]  = stats[1].text

        info["date"] = stats[2].text

        info["thumbnail"] = wait.until(EC.presence_of_element_located(
                                (By.CSS_SELECTOR,"ytd-playlist-video-thumbnail-renderer img"))).get_attribute("src")

        info["uploader"] = wait.until(EC.presence_of_element_located(
                                (By.CSS_SELECTOR,"div#upload-info ytd-channel-name yt-formatted-string"))).text

        search_results = wait.until(EC.presence_of_all_elements_located(
                                        (By.CSS_SELECTOR,"ytd-thumbnail-overlay-time-status-renderer span")))
     
        entries_list : List[Any]=[]
        for element in search_results:
            duration = element.text
            driver.execute_script("arguments[0].scrollIntoView();", element)
            ytd_thumbnail_overlay = driver.execute_script("return arguments[0].parentNode;", element)
            div = driver.execute_script("return arguments[0].parentNode;", ytd_thumbnail_overlay)
            link = driver.execute_script("return arguments[0].parentNode;", div)
            thumbnail = driver.execute_script("return arguments[0].parentNode;", link)
            video = driver.execute_script("return arguments[0].parentNode;", thumbnail)
            name = video.find_element_by_css_selector("h3").text

            split_list = re.split("/|=|&",link.get_attribute("href"))
            entries_list += [[(split_list[split_list.index("watch?v")+1]),duration,name]]   

        info["entries"] = entries_list
     
        
        time = {"H":0,"M":0,"S":0}

        for vid,duration,name in entries_list:
            v_duration_list = list(map(int,duration.split(":")))            
            if len(v_duration_list)==3:
                time["H"] += v_duration_list[-3]
            time["M"] += v_duration_list[-2]
            time["S"] += v_duration_list[-1]

        if time["S"] >= 60:
            time["M"] += time["S"] // 60
            time["S"] = time["S"] % 60

        if time["M"] >= 60:
            time["H"] += time["M"] // 60
            time["M"] = time["M"] % 60

        info["duration_dict"] = time
        return info
   
    @property
    def entries(self):
        return self._info["entries"]

    @property
    def uploader(self) -> str:
        return self._info["uploader"]

    @property
    def url(self) -> str:
        return self._info["url"]
    
    @property
    def thumbnail(self) -> str:
        return self._info["thumbnail"]

    @property
    def title(self) -> str:
        return self._info["title"]
    
    @property
    def requester(self) -> str:
        return self._requester

    @property
    def views(self) -> str:
        return self._info["views"]
    
    @property
    def date(self) -> str:
        return self._info["date"]

    @property
    def description(self) -> str:
        return self._info["description"]


    @property
    def duration_dict(self) -> dict:     
        return self._info["duration_dict"] 

    @property
    def duration(self) ->str:
        time = self._info["duration_dict"] 
        time = list(map(str,list(time.values())))
        def two_dig(number):
            if len(number)==1:
                return f"0{number}"
            else:
                return (number)
        if time[0] == '0':
            _duration = f"{time[1]}:{two_dig(time[2])}"
        else:
            _duration = f"{time[0]}:{two_dig(time[1])}:{two_dig(time[2])}"
        return _duration    
    
    @property
    def seconds(self) -> int:
        time = self.duration_dict
        self._seconds = (time["H"] * 60 * 60) + (time["M"] * 60) + time["S"]
        return self._seconds
