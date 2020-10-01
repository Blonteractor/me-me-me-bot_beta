
from bs4 import BeautifulSoup
import requests

class Days:
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURDAY = 3
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
    
    def __init__(self, info):
        self.info = info
        
    def __str__(self):
        return f"{self.title}, By {self.author}"
    
    def __len__(self):
        return self.length
        
    @property
    def title(self) -> str:
        return self.info["title"]
    
    @property
    def likes(self) -> str:
        return self.info["likes"]
    
    @property
    def genre(self) -> str:
        return self.info["genre"]
    
    @property
    def author(self) -> str:
        return self.info["author"]
    
    @property
    def summary(self) -> str:
        return self.info["summary"]
    
    @property
    def status(self) -> str:
        return self.info["status"]
    
    @property
    def length(self) -> int:
        return int(self.info["length"])
    
    @property
    def last_updated(self) -> str:
        return self.info["last_updated"]
    
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
            
        webtoon["thumbnail"] = card.img["src"]

        anchor = card.a
        
        clean_title = ""
        for character in webtoon["title"]:
            if character == " ":
                clean_title += "-"
            elif character.isalnum():
                clean_title += character.lower()
        
        new_url = "https://www.webtoons.com/en/" + webtoon["genre"].lower() + "/" + clean_title + "/" + "list?title_no=" + anchor["href"].split("=")[-1]
        webtoon["url"] = new_url
        
        soup = BeautifulSoup(requests.get(new_url).text, "lxml")
        
        if webtoon["author"] is None:
            webtoon["author"] = soup.find("div", class_="info").a.text.replace("author info", "").strip()
        
        details_box = soup.find("div", id="_asideDetail")
        
        webtoon["status"] = details_box.find("p", class_="day_info").text
        webtoon["summary"] = details_box.find("p", class_="summary").text
    
        page_1_request = requests.get(new_url + "&page=1").text
        soup = BeautifulSoup(page_1_request, "lxml")
        
        ep_element = soup.find("ul", id="_listUl").li

        webtoon["length"] = ep_element.find("span", class_="subj").text.split()[1]
        webtoon["last_updated"] = ep_element.find("span", class_="date").text
        
        return cls(info=webtoon)
        
    
    @classmethod
    def get_webtoons_by_day(cls, day: int):
        HTML = requests.get(url=cls.SITE_URL).text
        soup = BeautifulSoup(HTML, "lxml")

        weekly_list = soup.find("div", id="weekdayList")
        cards = weekly_list.find_all("ul", class_="card_lst")[day].find_all("li")[:-1]
        
        for card in cards:
            yield cls.get_info_from_card(card)
    
    @classmethod
    def search(cls, query: str) -> list:  
        url = cls.SITE_URL + "search?keyword=" + query.replace(" ", "%20")
        html = requests.get(url).text
        soup = BeautifulSoup(html, "lxml")
        
        cards = soup.find("ul", class_="card_lst").find_all("li")              
        
        search_result = []
        for card in cards: 
            webtoon_object = cls.get_info_from_card(card)
            search_result.append(webtoon_object)
            
        return search_result
    
    @classmethod
    def get_webtons_by_genre(cls, genre: int):
        HTML = requests.get(url=cls.SITE_URL + "/genre").text
        soup = BeautifulSoup(HTML, "lxml")
        
        genre_list = soup.find("div", class_="card_wrap genre")
        genre_name = genre_list.find_all("h2")[genre].text
        
        cards = genre_list.find_all("ul", class_="card_lst")[genre].find_all("li")
        
        for card in cards:
            yield cls.get_info_from_card(card, genre=genre_name)
            
        