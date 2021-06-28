from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import time
import re

browser = webdriver.Firefox()
browser.get('https://www.youtube.com/c/LutoAraka/community')
time.sleep(2)

# 最後に到達しているかどうかをチェックし、到達してないとスクロール続ける
browser.find_element_by_id('content-text').click()
for i in range(10):
    browser.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
    time.sleep(100/1000)
FindContent = browser.find_elements_by_tag_name('ytd-backstage-post-thread-renderer')
LastContent_text = FindContent[len(FindContent) - 1].text
judgeContent = bool(re.match(r".*Forgot to post on yt but here's schedule for this week! :3.*", LastContent_text, re.S))
while judgeContent == 0:
    for i in range(10):
        browser.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
        time.sleep(100/1000)
    FindContent = browser.find_elements_by_tag_name('ytd-backstage-post-thread-renderer')
    LastContent_text = FindContent[len(FindContent) - 1].text
    judgeContent = bool(re.match(r".*Forgot to post on yt but here's schedule for this week! :3.*", LastContent_text, re.S))

# 最後に到達したら全部の内容を取り出す
GetContents = browser.find_elements_by_tag_name('ytd-backstage-post-thread-renderer')
contents = []
for GetContent in GetContents:
    content = GetContent.text
    contents.append(content)
print(contents)


time.sleep(1)
browser.quit()