
from selenium import webdriver 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By 
from selenium.webdriver.common.action_chains import ActionChains
import re
import urllib.parse
from typing import Any,List

link1 = "https://www.youtube.com/watch?v=9XvXF1LrWgA"
link2 = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
driver = webdriver.Chrome() 

wait = WebDriverWait(driver, 10)

query_string = urllib.parse.urlencode({"search_query": query})
        
driver.get("http://www.youtube.com/results?" + query_string)
search_results = wait.until(EC.presence_of_all_elements_located(
                                (By.CSS_SELECTOR,"ytd-thumbnail-overlay-time-status-renderer span")))[:20]

entries_list : List[Any]=[]
for element in search_results:
            duration = element.text
            driver.execute_script("arguments[0].scrollIntoView();", element)
            ytd_thumbnail_overlay = driver.execute_script("return arguments[0].parentNode;", element)
            div = driver.execute_script("return arguments[0].parentNode;", ytd_thumbnail_overlay)
            link = driver.execute_script("return arguments[0].parentNode;", div).get_attribute("href")
            
            split_list = re.split("/|=|&",link)
            entries_list += [[(split_list[split_list.index("watch?v")+1]),duration]]   
print(entries_list)


""" 
info = {}
info["id"] = "PLN1mxegxWPd3d8jItTyrAxwm-iq-KrM-e"
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

info["entries"] = [x.get_attribute("href") for x in wait.until(EC.presence_of_all_elements_located(
                           (By.CSS_SELECTOR,"a#thumbnail")))]

entries_list: List[Any]=[]
for query in info["entries"]:
    if query:
        
        split_list = re.split("/|=|&",query)
        entries_list += [split_list[split_list.index("watch?v")+1]]

info["entries"] = entries_list



driver.quit()

print(info) """