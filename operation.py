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
from GetAllContentsClass import YTcommunity

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
    sys.exit()

main()