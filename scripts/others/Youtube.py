import youtube_dl
import urllib
import re
import bs4 as bs
import requests
from apiclient.discovery import build
from typing import List

api = "AIzaSyBhVkDTL219CN7Q9z5PB99ajFPkNrKcKUU"
youtube = build('youtube','v3',developerKey=api)


class YoutubeVideo:
    def __init__(self, id: str ):
        self.id = id

    @classmethod
    def from_query(cls, query: str , amount:int = 1):
        yl: List[YoutubeVideo] = []
        
        res = youtube.search().list(
            q = query,
            part = 'snippet',
            maxResults = amount,
            type = "video"
        ).execute()

        for item in res["items"]:
            yl += [YoutubeVideo(item['id']["videoId"])]
        
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
        res = youtube.videos().list(
            id= self.id,
            part = "snippet"

        ).execute()

        return res["items"][0]['snippet']

    @property
    def uploader(self) -> str:
        return self.info["channelTitle"]

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.id}"
    
    @property
    def thumbnail(self) -> str:
        return self.info["thumbnails"]["standard"]["url"]

    @property
    def thumbnails(self) -> dict:
        return self.info["thumbnails"]

    @property
    def title(self) -> str:
        return self.info["title"]
    
    @property
    def description(self) -> str:
        return self.info["description"]

    @property
    def duration_dict(self) -> dict:
        res = youtube.videos().list(
            id= self.id,
            part = "contentDetails"

        ).execute()

        duration = res["items"][0]["contentDetails"]["duration"]

        time = {'Y':0, "W":0, "D":0, "H":0, "M":0, "S":0}
    
        for i in range(len(duration)):
            if duration[i] in time:
                val = ""
                for j in range(i-1, 0, -1):
                    if duration[j].isalpha():
                        break 
                    else:
                        val = duration[j] + val

                time[duration[i]] = int(val)

        return time

    @property
    def duration(self) -> str:
        time = list(self.duration_dict.values())
        t_string = ""

        for i in time:
            if i != 0:
                for j in time[time.index(i): ]:
                    t_string += str(j)

                    if j != time[-1]:
                        t_string += ":"

                break

        t_ls = t_string.split(":")

        t_string_fn = ""
        for index, i in enumerate(t_ls):
            if len(i) <= 1:
                t_string_fn += "0" + i
            else:
                t_string_fn += i

            if not index == len(t_ls) - 1:
                t_string_fn += " : "

        return t_string_fn

    @property
    def seconds(self) -> int:
        time = self.duration_dict
        self._seconds = (time["Y"] * 365 * 24 * 60 * 60) + (time["W"] * 7 * 24 * 60 * 60) + (time["D"] * 24 * 60 * 60) + (time["H"] * 60 * 60) + (time["M"] * 60) + time["S"]

        return self._seconds



class YoutubePlaylist:

    def __init__(self,id:str):
        self.id = id

    @classmethod
    def from_query(cls, query: str,amount:int = 1):
        yl: List[YoutubeVideo] = []
        
        res = youtube.search().list(
            q = query,
            part = 'snippet',
            maxResults = amount,
            type = "playlisy"
        ).execute()

        for item in res["items"]:
            yl += [YoutubeVideo(item['id']["playlistId"])]
        
        return yl

    def __len__(self) -> int:
        return self.duration_sec

    def __lt__(self, other) -> bool:
        if not isinstance(other, YoutubePlaylist):
            return NotImplemented

        return self.duration_sec < other.duration_sec

    def __gt__(self, other) -> bool:
        if not isinstance(other, YoutubePlaylist):
            return NotImplemented

        return self.duration_sec > other.duration_sec

    def __eq__(self, other) -> bool:   # type: ignore
        if not isinstance(other, YoutubePlaylist):
            return NotImplemented

        return self.id == other.id

    def __ne__(self, other) -> bool:   # type: ignore
        if not isinstance(other, YoutubePlaylist):
            return NotImplemented

        return self.id != other.id
    
    def __str__(self) -> str:
        string =f'{self.title} ({self.duration}) - {self.uploader} \n\n'
        for video in self.entries:
            string += f"{str(video)} \n"

        return string        

    @property
    def info(self) -> dict:
        res = youtube.playlists().list(
            id= self.id,
            part = "snippet"

        ).execute()
        return res["items"][0]['snippet']

    @property
    def entries(self):
        
        res = youtube.playlistItems().list(
        part="snippet",
        playlistId=self.id,
        maxResults="50"
        ).execute()

        nextPageToken = res.get('nextPageToken')
        while ('nextPageToken' in res):
            nextPage = youtube.playlistItems().list(
            part="snippet",
            playlistId=self.id,
            maxResults="50",
            pageToken=nextPageToken
            ).execute()


            res['items'] = res['items'] + nextPage['items']

            if 'nextPageToken' not in nextPage:
                break
            else:
                nextPageToken = nextPage['nextPageToken']
        yl = []
        for vid in res['items']:
            yl += [YoutubeVideo(vid["snippet"]["resourceId"]["videoId"])]
        return yl

    
    @property
    def uploader(self) -> str:
        return self.info["channelTitle"]

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/playlist?list={self.id}"
    
    @property
    def thumbnail(self) -> str:
        return self.info["thumbnails"]["standard"]["url"]

    @property
    def thumbnails(self) -> dict:
        return self.info["thumbnails"]

    @property
    def title(self) -> str:
        return self.info["title"]
    
    @property
    def description(self) -> str:
        return self.info["description"]


    @property
    def duration_dict(self) -> dict:     
        time = {'Y':0,"W":0,"D":0,"H":0,"M":0,"S":0}

        for video in self.entries:
            v_duration_dict = video.duration_dict
            for x in v_duration_dict:
                time[x] += v_duration_dict[x]
        
        if time["S"] >= 60:
            time["M"] += time["S"] // 60
            time["S"] = time["S"] % 60

        if time["M"] >= 60:
            time["H"] += time["M"] // 60
            time["M"] = time["M"] % 60

        if time["H"] >= 24:
            time["D"] += time["H"] // 24
            time["H"] = time["H"] % 24
        
        time["D"] += time["W"]*7

        if time["D"] >= 7:
            if time["D"] >= 365:
                time["Y"] += time["D"] // 365
                time["D"] += time["D"] % 365
            
            time["W"] += time["D"] // 7
            time["D"] = time["D"] % 7

        return time

    @property
    def duration(self) ->str:
        time = list(self.duration_dict.values())

        t_string = ""
        for i in time:
            if i != 0:
                for j in time[time.index(i):]:
                    t_string+=str(j)
                    if j != time[-1]:
                        t_string+=":"
                break

        t_ls = t_string.split(":")

        t_string_fn = ""
        for index, i in enumerate(t_ls):
            if len(i) <= 1:
                t_string_fn += "0" + i
            else:
                t_string_fn += i

            if not index == len(t_ls) - 1:
                t_string_fn += " : "

        return t_string_fn
    
    @property
    def duration_sec(self) -> int:
        time = list(self.duration_dict.values())
        return time[0]*360031536000 + time[3]* 86400*7 + time[2]* 86400 +time[3]*3600 + time[4]*60 + time

