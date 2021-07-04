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
import os
import logging
import sys

# selenium setting
headPath = os.getcwd()
options = webdriver.FirefoxOptions()
# options.headless = True
options.page_load_strategy = 'eager'
browser = webdriver.Firefox(headPath,options=options)
# logger setting
formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s (%(filename)s)')
logger = logging.getLogger(__name__)
debug_handler = logging.FileHandler('YTprogram-DEBUG.log', encoding='utf-8')
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(debug_handler)

class YTcommunity:
    def __init__(self, url, pageName, defaultEarliestText):
        self.url = url
        self.pageName = pageName
        self.defaultEarliestText = defaultEarliestText
    def accessUrl(self):
        try:
            browser.get(self.url)
            logger.debug('accessUrl to 【{}】'.format(self.url))
        except:
            browser.quit()
            logger.error('accessUrl ERROR')
            sys.exit('error')
    # 10回PageDown keyを送る
    def PgDn(self):
        for i in range(10):
            browser.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
            time.sleep(100/1000)
    # urlにあるcontentを取得し、date frameを返す
    def GetContent_to_df(self):
        GetContents = browser.find_elements_by_tag_name('ytd-backstage-post-thread-renderer')
        contents = []
        for GetContent in GetContents:
            content = GetContent.text
            contents.append(content)
        GetPosts = browser.find_elements_by_xpath("//*[@id='published-time-text']/a") 
        Urls = []
        for GetUrl in GetPosts:
            Url = GetUrl.get_attribute('href')
            Urls.append(Url)
        PostDates = []
        for GetPostDate in GetPosts:
            PostDate = GetPostDate.text
            PostDates.append(PostDate)
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
        return df
    # 毎回取得した最後のcontentをチェックし、もしその中にsheet内のデータがあるならスクロールを停止
    def CheckLatest(self):
        i = 0
        while True:
            self.PgDn()
            reContent = r".*" + self.defaultEarliestText + r".*"
            FindContents = browser.find_elements_by_tag_name('ytd-backstage-post-thread-renderer')
            FoundedContent = FindContents[len(FindContents) - 1].text
            logger.debug('CheckLatest -> FoundedContent = 【{}】'.format(FoundedContent))
            judgeContent = bool(re.match(reContent, FoundedContent, re.S))
            i = i + 1
            if judgeContent == 1:
                break
            elif i > 200:
                break
    # 毎回取得した全部のcnontentをチェックし、もしその中にsheet内のデータがあるならスクロールを停止
    def CheckLatest_each(self, LatestText):
        i = 0
        while True:
            reContent = r".*" + LatestText + r".*"
            FindContents = browser.find_elements_by_tag_name('ytd-backstage-post-thread-renderer')
            logger.debug('CheckLatest_each -> reContent = 【{}】'.format(reContent))
            judgedContents = []
            allFoundedContent = []
            for FoundedEachContent in FindContents:
                CheckContent = FoundedEachContent.text
                allFoundedContent.append(CheckContent)
                judgeContent = bool(re.match(reContent, CheckContent, re.S))
                judgedContents.append(judgeContent)
            logger.debug('CheckLatest_each -> allFoundedContent = 【{}】'.format(allFoundedContent))
            logger.debug('CheckLatest_each -> judgedContents = 【{}】'.format(judgedContents))
            i = i + 1
            if True in judgedContents:
                break
            elif i > len(judgedContents):
                break
            self.PgDn()
    # sheetから取得したtextを事前処理する
    def selectText(self, sheet_text):
        listText = sheet_text.split('\n')            
        doneText = [i for i in listText if i !='']
        pre_selectText = doneText[2]
        selectText = re.sub('[!"#$%&\'\\\\()*+,-./:;<=>?@[\\]^_`{|}~「」〔〕“”〈〉『』【】＆＊・（）＄＃＠。、？！｀＋￥％]', ".", pre_selectText)
        logger.debug('selectText -> selectText = 【{}】'.format(selectText))
        return selectText
    # google sheet apiのbookにアクセスし、bookを返す
    def accessTo_sheet_book(self):
        try:
            credentials_file = 'C:\PRISM_Project\Youtube_community\YT_community\prism-yt-community-5c7b61fbbf04.json'
            scopes = [
                'https://www.googleapis.com/auth/drive',
                'https://spreadsheets.google.com/feeds'
            ]
            spreadSheet_key = '1PQCvRce8pgPJp7jfBadVzVqQULbrpUYinwtmRD4C16s'
            credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scopes)
            gs = gspread.authorize(credentials)
            work_sheet_book = gs.open_by_key(spreadSheet_key)
            return work_sheet_book
        except:
            logger.error('accessTo_sheet_book ERROR')
            browser.quit()
            sys.exit('error')
    # pageにアクセスし、pageを返す
    def accessTo_sheet_page(self, sheet_book):
        try:
            spreadSheet_page = self.pageName
            work_sheet_page = sheet_book.worksheet(spreadSheet_page)
            return work_sheet_page
        except:
            logger.error('accessTo_sheet_page ERROR')
            browser.quit()
            sys.exit('error')
    # sheetにある最新のcontentを取得
    def GetLatestContent_inSheet(self, sheet_page) -> str:
        try:
            LatestContentText = sheet_page.acell('A2').value
            return LatestContentText
        except:
            browser.quit()
            logger.error('GetLatestContent_inSheet ERROR')
            sys.exit('error')
    # 取得したdata frameをsheetにupload
    def upload_df_toSheet(self, sheet_page, values):
        try:
            set_with_dataframe(sheet_page, values, include_index=False)
        except:
            logger.error('upload_df_toSheet ERROR')
            browser.quit()
            sys.exit('error')
    # 取得したdate frameをsheetに挿入する
    def insert_df_toSheet(self, sheet_page, df_values):
        try:
            listValues = df_values.values.tolist()
            sheet_page.insert_rows(listValues, row=2)
        except:
            logger.error('insert_df_toSheet ERROR')
            browser.quit()
            sys.exit('error')
    # 取得したdfをsheetと比較し、重複したデータを削除し、new dfを返す
    def comparedText(self, origin_df, compareText):
        try:
            ContentList = list(origin_df['contents'])
            reSelectContent = r".*" + compareText + r".*"
            judgeTexts = []
            for content in ContentList:
                judgeContent = bool(re.match(reSelectContent, content, re.S))
                judgeTexts.append(judgeContent)
            selectContent_index = judgeTexts.index(True)
            newdf = origin_df.head(selectContent_index)
            logger.debug('comparedText -> ContentList =【{}】'.format(ContentList))
            logger.debug('comparedText -> reSelectContent =【{}】'.format(reSelectContent))
            logger.debug('comparedText -> judgeTexts =【{}】'.format(judgeTexts))
            logger.debug('comparedText -> newdf =【{}】'.format(newdf))
            return newdf
        except:
            logger.error('comparedText ERROR')
            browser.quit()
            sys.exit('error')

# インスタンス化
aoi = YTcommunity('https://www.youtube.com/c/AoiTokimori/community', 'aoi', "Here's my streaming schedule for this week! Hope to see you all there")
meno = YTcommunity('https://www.youtube.com/c/MenoIbuki/community', 'meno', "Meno's schedule for this week!!!")
iku = YTcommunity('https://www.youtube.com/c/IkuHoshifuri/community', 'iku', "This is Iku’s schedule for this week!")
luto = YTcommunity('https://www.youtube.com/c/LutoAraka/community', 'luto', "Forgot to post on yt but here's schedule for this week! :3")
rita = YTcommunity('https://www.youtube.com/c/RitaKamishiro/community', 'rita', "Surprise!! To make up for my silly April Fools prank the other day")
shiki = YTcommunity('https://www.youtube.com/channel/UCswvd6_YWmd6riRk-8oT-sA/community', 'shiki', "HELLO, OCCULTREATS!!! WOW!!")
nia = YTcommunity('https://www.youtube.com/channel/UCw1KNjVqfrJSfcFd6zlcSzA/community', 'nia', 'WHEN DID I HAVE THIS OPTION')
yura = YTcommunity('https://www.youtube.com/channel/UC0ZTVxCHkZanT5dnP2FZD4Q/community', 'yura', "AH!")
pina = YTcommunity('https://www.youtube.com/channel/UCpeRj9-GaLGNUoKdI5I7vZA/community', 'pina', "Hi PenPals!")

# 実行関数
def update_talent(name):
    name.accessUrl()
    worksheet_book = name.accessTo_sheet_book()
    worksheet_page = name.accessTo_sheet_page(worksheet_book)
    Get_SheetContent = name.GetLatestContent_inSheet(worksheet_page)
    if Get_SheetContent == None:
        name.CheckLatest()
        origin_contents_df = name.GetContent_to_df()
        name.upload_df_toSheet(worksheet_page, origin_contents_df)
    else:
        selectContent = name.selectText(Get_SheetContent)
        name.CheckLatest_each(selectContent)
        origin_contents_df = name.GetContent_to_df()
        completed_df = name.comparedText(origin_contents_df, selectContent)
        name.insert_df_toSheet(worksheet_page, completed_df)

def main():
    talent_name_list = [aoi, meno, iku, luto, rita, shiki, nia, yura, pina]
    for name in talent_name_list:
        update_talent(name)
        time.sleep(1)
    logger.debug('--All Done--')
    browser.quit()

main()