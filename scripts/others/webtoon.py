
from bs4 import BeautifulSoup
import requests
from random import choice
from imgurpython import ImgurClient
import os
import concurrent.futures
from state import BotState

_CLIENT_ID = "d25b6deb1dedc8e"
_CLIENT_SECRET = "7a357962df433442627eb65cdada3daed03465dc"
    
_client = ImgurClient(_CLIENT_ID, _CLIENT_SECRET)

def get_image_url(response, path) -> str:
    with open(path, "wb+") as f:
        f.write(response.content)
                
    url = _client.upload_from_path(path)["link"]
    
    os.remove(path)
    
    return url

class Days:
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6
    
class Genres:
    DRAMA = 0
    FANTASY = 1
    COMEDY = 2
    ACTION = 3
    SLICE_OF_LIFE = 4
    ROMANCE = 5
    SUPERHERO = 6
    SCI_FI = 7
    THRILLER = 8
    SUPERNATURAL = 9
    MYSTERY = 10
    SPORTS = 11
    HISTORICAL = 12
    HEARTWARMING = 13
    HORROR = 14
    INFORMATIVE = 15

class Webtoon:
    SITE_URL = "https://www.webtoons.com/en/"
    HEADERS = referer_header = { "Referer": SITE_URL[:-4] }
    
    cache = BotState("w").webtoon_cache
    
    def __init__(self, info):
        self._info = info
        
    def __str__(self):
        return f"{self.title}, By {self.author}"
    
    def __len__(self):
        return int(self.length)
        
    @property
    def title(self) -> str:
        return self._info["title"]
    
    @property
    def url(self) -> str:
        return self._info["url"]
    
    @property
    def thumbnail(self) -> str:
        return self._info["thumbnail"]
    
    @property
    def clean_title(self) -> str:
        return self._info["clean_title"]
    
    @property
    def likes(self) -> str:
        return self._info["likes"]
    
    @property
    def genre(self) -> str:
        return self._info["genre"]
    
    @property
    def author(self) -> str:
        return self._info["author"]
    
    @property
    def summary(self) -> str:
        return self._info["summary"]
    
    @property
    def status(self) -> str:
        return self._info["status"].replace("UP", "UP ").lower().capitalize()
    
    @property
    def is_daily_pass(self) -> bool:
        return self._info["is_daily_pass"]
    
    @property
    def is_completed(self) -> bool:
        return not self.status.startswith("Up")
    
    @property
    def extra_ep_app(self) -> str:
        return self._info["extra_ep_app"]
    
    @property
    def length(self) -> int:
        return int(self._info["length"])
    
    @property
    def last_updated(self) -> str:
        return self._info["last_updated"]
    
    @classmethod
    def get_info_from_card(cls, card, genre=None):
        webtoon = {}
            
        result = card.find("div", class_="info")
        
        try:
            title = result.find("h3", class_="subj").text
        except AttributeError as e:
            title = result.find("p", class_="subj").text    
        
        webtoon["title"] = title
        
        try:
            webtoon["author"] = result.find("p", class_="author").text
        except AttributeError:
            webtoon["author"] = None
            
        webtoon["likes"] = result.find("p", class_="grade_area").em.text
        
        if genre is None:
            webtoon["genre"] = card.find_all("span")[1].text
        else:
            webtoon["genre"] = genre
        
        anchor = card.a
        
        clean_title = ""
        for character in webtoon["title"]:
            if character == " ":
                clean_title += "-"
            elif character.isalnum():
                clean_title += character.lower()
                
        thumbnail_url = card.img["src"].replace("?type=q90", "")
        url = thumbnail_url
        
        if clean_title not in cls.cache:
            response_thumbnail = requests.get(thumbnail_url, headers=cls.HEADERS)
            img_path = f'./cache.bot/{clean_title}.png'
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                thread = executor.submit(get_image_url, response_thumbnail, img_path)
                url = thread.result()
            
            cls.cache[clean_title] = url 
            webtoon["thumbnail"] = url
            
            BotState("w").webtoon_cache = cls.cache
        else:
            url = cls.cache[clean_title]
            webtoon["thumbnail"] = url
            
        
                
        webtoon["clean_title"] = clean_title
        
        new_url = "https://www.webtoons.com/en/" + webtoon["genre"].lower().replace(" ", "-") + "/" + clean_title + "/" + "list?title_no=" + anchor["href"].split("=")[-1]
        webtoon["url"] = new_url
        
        soup = BeautifulSoup(requests.get(new_url, headers=cls.HEADERS).text, "lxml")
        
        if webtoon["author"] is None:
            webtoon["author"] = soup.find("div", class_="info").a.text.replace("author info", "").strip()
        
        details_box = soup.find("div", id="_asideDetail")
        
        webtoon["status"] = details_box.find("p", class_="day_info").text
        webtoon["summary"] = details_box.find("p", class_="summary").text
    
        page_1_request = requests.get(new_url + "&page=1", headers=cls.HEADERS).text
        soup = BeautifulSoup(page_1_request, "lxml")
        
        app_add = ep_element = soup.find("div", class_="detail_install_app")
        if app_add is not None:
            if app_add.strong.text == "Read more episodes for free every day on the app!":
                webtoon["is_daily_pass"] = True
                webtoon["extra_ep_app"] = None
            else:
                webtoon["extra_ep_app"] = app_add.em.text
                webtoon["is_daily_pass"] = False
        else:
            webtoon["is_daily_pass"] = False
            webtoon["extra_ep_app"] = None
        
        ep_element = soup.find("ul", id="_listUl").li

        webtoon["length"] = ep_element.find("span", class_="tx").text[1:]
        webtoon["last_updated"] = ep_element.find("span", class_="date").text
        
        return cls(info=webtoon)
        
    
    @classmethod
    def get_webtoons_by_day(cls, day: int):
        HTML = requests.get(url=cls.SITE_URL, headers=cls.HEADERS).text
        soup = BeautifulSoup(HTML, "lxml")

        weekly_list = soup.find("div", id="weekdayList")
        cards = weekly_list.find_all("ul", class_="card_lst")[day].find_all("li")[:-1]
        
        search_result = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            threads = [executor.submit(cls.get_info_from_card, card) for card in cards]
            results = [thread.result() for thread in concurrent.futures.as_completed(threads)]
            search_result.extend(results)
            
        return search_result
    
    @classmethod
    def search(cls, query: str) -> list:  
        url = cls.SITE_URL + "search?keyword=" + query.replace(" ", "%20")
        html = requests.get(url, headers=cls.HEADERS).text
        soup = BeautifulSoup(html, "lxml")
        
        m = soup.find("ul", class_="card_lst")
        
        if m is None:
            return []
        
        cards = m.find_all("li")              
        
        search_result = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            threads = [executor.submit(cls.get_info_from_card, card) for card in cards]
            results = [thread.result() for thread in concurrent.futures.as_completed(threads)]
            search_result.extend(results)
            
        return search_result
    
    @classmethod
    def get_webtoons_by_genre(cls, genre: int, all=False, limit=-1):
        HTML = requests.get(url=cls.SITE_URL + "/genre", headers=cls.HEADERS).text
        soup = BeautifulSoup(HTML, "lxml")
        
        genre_list = soup.find("div", class_="card_wrap genre")
        genre_name = genre_list.find_all("h2")[genre].text
        
        cards = genre_list.find_all("ul", class_="card_lst")[genre].find_all("li")
        
        if not all:
            ch = choice(cards)
            yield cls.get_info_from_card(ch, genre=genre_name)
        else:
            for i, card in enumerate(cards):
                yield cls.get_info_from_card(card, genre=genre_name)
                if i + 1 == limit:
                    return