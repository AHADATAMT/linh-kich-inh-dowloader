# imports
from selenium import webdriver
import time
import requests
import logging
import re
from functions import download_file, download_sub
import config
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# specifies the path to the chromedriver.exe
driver = webdriver.Chrome(ChromeDriverManager().install())
learn_url = 'https://www.linkedin.com/learning/%s'
# driver.get method() will navigate to a page given by the URL address
driver.get('https://www.linkedin.com/login')
base_path = 'out'
video_api_url = 'https://www.linkedin.com/learning-api/detailedCourses?addParagraphsToTranscript=false&courseSlug=%s' \
    '&q=slugs&resolution=_720&videoSlug=%s'
learning_api = 'https://www.linkedin.com/learning-api/detailedCourses?fields=chapters,exerciseFileUrls,exerciseFiles,cachingKey,urn,slug&addParagraphsToTranscript=true&courseSlug=%s&q=slugs'
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/66.0.3359.181 Safari/537.36'
}

username = driver.find_element_by_name('session_key')
username.send_keys(config.USERNAME)
time.sleep(2)
password = driver.find_element_by_name('session_password')
password.send_keys(config.PASSWORD)
time.sleep(1)
sign_in_button = driver.find_element_by_xpath('//*[@type="submit"]')
sign_in_button.click()
time.sleep(0.5)
for course in config.COURSES:
    print(learn_url % course)
    time.sleep(10)
    driver.get(learn_url % course)

    session = requests.Session()
    cookies = driver.get_cookies()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])

    token = session.cookies.get('JSESSIONID').replace('"', '')
    session.headers['Csrf-Token'] = token
    session.headers.pop('Accept')
    resp = session.get(learning_api % course)
    course_data = resp.json()['elements'][0]
    course_name = course_data['slug']
    logging.info('Starting download of course [%s]...' % course_name)
    chapters_list = course_data['chapters']
    course_path = '%s/%s' % (base_path, course_name)
    chapter_index = 1
    logging.info('Parsing course\'s chapters...')
    logging.info('%d chapters found' % len(chapters_list))

    for chapter in chapters_list:
        time.sleep(10)
        chapter_name = re.sub('[^a-zA-Z0-9\n\.]', ' ',
                              chapter['title']).strip()
        logging.info('Starting download of chapter [%s]...' % chapter_name)
        chapter_path = '%s/%s - %s' % (course_path,
                                       str(chapter_index).zfill(2), chapter_name)
        if chapter_name == '':
            chapter_path = chapter_path[:-3]
        videos_list = chapter['videos']
        video_index = 1
        logging.info('Parsing chapters\'s videos')
        logging.info('%d videos found' % len(videos_list))
        for video in videos_list:
            time.sleep(10)
            video_name = re.sub('[^a-zA-Z0-9\n\.]', ' ',
                                video['slug']).strip()
            video_slug = video['slug']
            video_data = (session.get(video_api_url %
                                      (course_name, video_slug)))
            try:
                video_url = re.search('"progressiveUrl":"(.+)","expiresAt"', video_data.text).group(1)  
            except:
                logging.error(
                    'Can\'t download the video [%s], probably is only for premium users' % video_name)
                continue
            logging.info('Downloading video [%s]' % video_name)
            download_file(video_url, chapter_path, '%s - %s.mp4' %
                          (str(video_index).zfill(2), video_name), session)
            video_data = video_data.json()['elements'][0]
            try:
                subs = video_data['selectedVideo']['transcript']['lines']
            except KeyError:
                logging.info('No subtitles avaible')
            else:
                logging.info('Downloading subtitles')
                download_sub(subs, chapter_path, '%s - %s.srt' %
                             (str(video_index).zfill(2), video_name))
            video_index += 1
        chapter_index += 1

    exercises_list = course_data['exerciseFiles']
    for exercise in exercises_list:
        try:
            ex_name = exercise['name']
            ex_url = exercise['url']
        except (KeyError, IndexError):
            logging.info(
                'Can\'t download an exercise file for course [%s]' % course_name)
        else:
            download_file(ex_url, course_path, ex_name, session)
        # description = course_data['description']
        # logging.info('Downloading course description')
        # download_desc(description, 'https://www.linkedin.com/learning/%s' %
        #               course, course_path, 'Description.txt')
    logging.info('Done...!')
