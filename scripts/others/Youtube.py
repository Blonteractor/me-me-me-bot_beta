
from selenium import webdriver 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By 
import re
import urllib.request
import urllib.parse
from typing import List,Any
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("disable-extensions")
chrome_options.add_argument("disable-gpu")
chrome_options.add_argument("headless")
chrome_options.add_argument("log-level=3")

driver = webdriver.Chrome(options = chrome_options) 
driver.get("http://www.youtube.com")
class YoutubeVideo:
    def __init__(self, id: str ,duration:str = None):
        self.id = id
        self._info = self.info
        if not duration:
            self.get_duration()
        else:
            self._info["duration"] = duration
            
    @classmethod
    def from_query(cls, query: str , amount:int = 1):

        wait = WebDriverWait(driver, 10)

        query_string = urllib.parse.urlencode({"search_query": query})
                
        driver.get("http://www.youtube.com/results?" + query_string)
        search_results = wait.until(EC.presence_of_all_elements_located(
                                        (By.CSS_SELECTOR,"ytd-thumbnail-overlay-time-status-renderer span")))[:amount]

        entries_list : List[Any]=[]
        for element in search_results:
            duration = element.text
            driver.execute_script("arguments[0].scrollIntoView();", element)
            ytd_thumbnail_overlay = driver.execute_script("return arguments[0].parentNode;", element)
            div = driver.execute_script("return arguments[0].parentNode;", ytd_thumbnail_overlay)
            link = driver.execute_script("return arguments[0].parentNode;", div).get_attribute("href")
            
            split_list = re.split("/|=|&",link)
            entries_list += [[(split_list[split_list.index("watch?v")+1]),duration]]   

        yl : List[Any]=[]
        
        for i in entries_list:
            yl += [cls(i[0],i[1])]

        
        return yl


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

        

        wait = WebDriverWait(driver, 10)
        info = {}
        info["id"] = self.id
        info["url"] = f"https://www.youtube.com/watch?v={info['id']}"

        driver.get(info["url"])
        
        
        info["views"]  = wait.until(EC.presence_of_element_located(
                                (By.CSS_SELECTOR,"yt-view-count-renderer span"))).text
        info["date"] = wait.until(EC.presence_of_element_located(
                                (By.CSS_SELECTOR,"div#date yt-formatted-string"))).text
        title = driver.find_element_by_css_selector("h1 yt-formatted-string")
        driver.execute_script("arguments[0].scrollIntoView();", title)
        info["title"] = title.text
        
        buttons = driver.find_elements_by_css_selector("div#top-level-buttons yt-formatted-string")
        info["likes"] = buttons[0].text
        info["dislikes"] = buttons[1].text
        info["thumbnail"] = f"https://i.ytimg.com/vi/{info['id']}/0.jpg"
        info["uploader"] = wait.until(EC.presence_of_element_located(
                                (By.CSS_SELECTOR,"div#upload-info ytd-channel-name yt-formatted-string"))).text
        wait.until(EC.presence_of_element_located(
                                (By.CSS_SELECTOR,"paper-button#more"))).click()
        info["description"] =wait.until(EC.presence_of_element_located(
                                (By.CSS_SELECTOR,"div#description"))).text

        

        return info


    @property
    def uploader(self) -> str:
        return self._info["uploader"]

    @property
    def likes(self) -> str:
        return self._info["likes"]
    
    @property
    def dislikes(self) -> str:
        return self._info["dislikes"]
    
    @property
    def views(self) -> str:
        return self._info["views"]
    
    @property
    def date(self) -> str:
        return self._info["date"]
    

    @property
    def thumbnail(self) -> str:
        return self._info["thumbnail"]

    @property
    def url(self) -> str:
        return self._info["url"]

    @property
    def title(self) -> str:
        return self._info["title"]
    
    @property
    def description(self) -> str:
        return self._info["description"]

    @property
    def duration_dict(self) -> dict:

        duration = self._info["duration"]
        duration = duration.split(":")

        time = {"H":0, "M":0, "S":0}

        if len(duration)==2:
            time["M"],time["S"] = map(int,duration)
            
        else:
            time["H"],time["M"],time["S"] = map(int,duration)

        return time

    def get_duration(self) -> str:
        wait = WebDriverWait(driver, 10)
        query_string = urllib.parse.urlencode({"search_query": self.id})
        
        driver.get("http://www.youtube.com/results?" + query_string)
        duration = wait.until(EC.presence_of_element_located(
                                        (By.CSS_SELECTOR,"ytd-thumbnail-overlay-time-status-renderer span"))).text

        self._info["duration"] = duration
        return duration

    @property
    def duration(self) -> str:
        return self._info["duration"] 

    @property
    def seconds(self) -> int:
        time = self.duration_dict
        self._seconds = (time["H"] * 60 * 60) + (time["M"] * 60) + time["S"]
        return self._seconds



class YoutubePlaylist:

    def __init__(self,id:str):
        self.id = id
        self._info = self.info

    @classmethod
    def from_query(cls, query: str , amount:int = 1):

        query_string = urllib.parse.urlencode({"search_query": query})
        html_content = urllib.request.urlopen(
            "http://www.youtube.com/results?" + query_string)
        search_results = re.findall(
            r'href=\"\/playlist\?list=(.{34})', html_content.read().decode())
        
        search_results = search_results[:amount]

        yl = [cls(x) for x in search_results]
        
        return yl

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
            link = driver.execute_script("return arguments[0].parentNode;", div).get_attribute("href")
            
            split_list = re.split("/|=|&",link)
            entries_list += [[(split_list[split_list.index("watch?v")+1]),duration]]   

        info["entries"] = entries_list
        
        time = {"H":0,"M":0,"S":0}

        for vid,duration in entries_list:
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
