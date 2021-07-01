from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import time
import re
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from gspread_dataframe import set_with_dataframe

options = webdriver.FirefoxOptions()
# options.headless = True
browser = webdriver.Firefox(options=options)
browser.get('https://www.youtube.com/c/LutoAraka/community')
time.sleep(2)

# 最後に到達しているかどうかをチェックし
browser.find_element_by_id('content-text').click()
for i in range(10):
    browser.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
    time.sleep(100/1000)
FindContent = browser.find_elements_by_tag_name('ytd-backstage-post-thread-renderer')
LastContent_text = FindContent[len(FindContent) - 1].text
judgeContent = bool(re.match(r".*Forgot to post on yt but here's schedule for this week! :3.*", LastContent_text, re.S))
# 到達するまでスクロール
time.sleep(1)
while judgeContent == 0:
    for i in range(10):
        browser.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
        time.sleep(100/1000)
    FindContent = browser.find_elements_by_tag_name('ytd-backstage-post-thread-renderer')
    LastContent_text = FindContent[len(FindContent) - 1].text
    judgeContent = bool(re.match(r".*Forgot to post on yt but here's schedule for this week! :3.*", LastContent_text, re.S))

# 全部のcontents内容を取り出す
GetContents = browser.find_elements_by_tag_name('ytd-backstage-post-thread-renderer')
contents = []
for GetContent in GetContents:
    content = GetContent.text
    contents.append(content)
# 全PostのUrlを抽出
GetPosts = browser.find_elements_by_xpath("//*[@id='published-time-text']/a") 
Urls = []
for GetUrl in GetPosts:
    Url = GetUrl.get_attribute('href')
    Urls.append(Url)
# 全Postの記載日付を抽出
PostDates = []
for GetPostDate in GetPosts:
    PostDate = GetPostDate.text
    PostDates.append(PostDate)
print(contents)
print(Urls)
print(PostDates)

# time deltaをdateに変換
for i, Time in enumerate(PostDates):
    judgeTimeDay = bool(re.match(r".*日前.*", Time))
    judgeTimeWeek = bool(re.match(r".*週間前.*", Time))
    judgeTimeMonth = bool(re.match(r".*月前.*", Time))
    judgeTimeYear = bool(re.match(r".*年前.*", Time))
    today = datetime.date.today()
    
    if judgeTimeDay == 1:
        TimeDayNum = int(re.sub(r"\D", "", Time))
        DayDelta = datetime.timedelta(days=TimeDayNum)
        PostDay = str(today - DayDelta)
        LastPostDate = PostDay
    elif judgeTimeWeek == 1:
        TimeWeekNum = int(re.sub(r"\D", "", Time))
        WeekDelta = datetime.timedelta(weeks=TimeWeekNum)
        PostDay = str(today - WeekDelta)
        LastPostDate = "around " + PostDay
    elif judgeTimeMonth == 1:
        TimeMonthNum = int(re.sub(r"\D", "", Time))
        TimeMonthDelta = datetime.timedelta(weeks=(TimeMonthNum*4))
        PostDay = str(today - TimeMonthDelta)
        LastPostDate = "around " + PostDay
    elif judgeTimeYear == 1:
        TimeYearNum = int(re.sub(r"\D", "", Time))
        LastPostDate = TimeYearNum + " year before " + str(today)
    else:
        LastPostDate = str(today)
    new = PostDates[i]
    new = LastPostDate
    PostDates[i] = new

df = pd.DataFrame()
df['contents'] = contents
df['post time'] = PostDates
df['url'] = Urls

# google sheet api
credentials_file = 'C:\PRISM_Project\Youtube_community\YT_community\prism-yt-community-5c7b61fbbf04.json'
scopes = [
    'https://www.googleapis.com/auth/drive',
    'https://spreadsheets.google.com/feeds'
]
spreadSheet_key = '1PQCvRce8pgPJp7jfBadVzVqQULbrpUYinwtmRD4C16s'
spreadSheet_page = 'test_luto'
credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scopes)
gs = gspread.authorize(credentials)
work_sheet_book = gs.open_by_key(spreadSheet_key)
work_sheet_page = work_sheet_book.worksheet(spreadSheet_page)
set_with_dataframe(work_sheet_page, df, include_index=True)

time.sleep(1)
browser.quit()