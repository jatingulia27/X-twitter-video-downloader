import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By  # For locating elements in login
from selenium.webdriver.common.keys import Keys  # For sending keys
from selenium.common.exceptions import NoSuchElementException  # For handling missing elements
from bs4 import BeautifulSoup

# Set up Chrome options
chrome_options = Options()
chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
driver = webdriver.Chrome(options=chrome_options)

# Function to log into Twitter/X
def login_to_twitter(username, password):
    driver.get('https://x.com/i/flow/login')
    time.sleep(1)

    def check_element(by, value):
        try:
            element = driver.find_element(by, value)
            return element
        except:
            return None

    username_field = None
    while not username_field:
        username_field = check_element(By.NAME, "text")
        time.sleep(0.2)

    username_field.send_keys(username)

    next_button = None
    while not next_button:
        buttons = driver.find_elements(By.CSS_SELECTOR, "button[role='button'][type='button']")
        if len(buttons) > 3:
            next_button = buttons[3]
        time.sleep(0.2)

    next_button.click()

    password_field = None
    while not password_field:
        password_field = check_element(By.NAME, "password")
        time.sleep(0.2)

    password_field.send_keys(password)
    login_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="LoginForm_Login_Button"]')
    login_button.click()

    time.sleep(3)

# Example usage with credentials
credentials = {
    "username": "jatingulia27",  # Replace with your Twitter username
    "password": "Ju62diMAKgic6$L"   # Replace with your Twitter password
}

login_to_twitter(credentials['username'], credentials['password'])

# Read URLs from CSV file
urls_to_scrape = pd.read_csv('urls.csv')['url'].tolist()  # Assuming your CSV has a column named 'url'

# Function to scroll and capture video post URLs
def scroll_and_capture_video_urls(input_date):
    scroll_pause_time = 2
    seen_urls = set()
    post_data_list = []  # List to store dictionaries with post URLs and dates
    ignored_class = "css-175oi2r r-18u37iz r-1q142lx"

    for i in range(250):
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'lxml')

        video_divs = soup.find_all('div', style=True)
        found_video = False

        for video_div in video_divs:
            if any(ignored_class.lower() in child.get('class', []) for child in video_div.find_all(True)):
                continue

            style = video_div.get('style', '')
            if 'translateY' in style:
                video_component = video_div.find('div', {'data-testid': 'videoComponent'})
                if not video_component:
                    continue

                post_div = video_div.find('div', class_='css-175oi2r r-18u37iz r-1q142lx')

                if post_div:
                    post_link = post_div.find('a', href=True)
                    time_element = post_div.find('time')
                    post_date = time_element['datetime'] if time_element else None
                    
                    if post_date:
                        if post_date[:10] > input_date:
                            if any(text in post_div.text for text in ["Pinned", "Reposted"]):
                                continue
                            else:
                                continue

                        if post_date[:10] == input_date:
                            pass
                        elif post_date[:10] < input_date:
                            return post_data_list

                    if post_link:
                        post_url = post_link['href']
                        if post_url not in seen_urls:
                            post_data_list.append({"url": f"https://x.com{post_url}", "datetime": post_date})
                            seen_urls.add(post_url)
                            found_video = True

        driver.execute_script("window.scrollBy(0, 700);")
        time.sleep(scroll_pause_time)

    return post_data_list

# Get input date from user
input_date = input("Enter the input date (YYYY-MM-DD): ")

# Store post data in a list
post_data_list = []

for url in urls_to_scrape:
    print(f"Processing URL: {url}")
    driver.get(url)
    post_data = scroll_and_capture_video_urls(input_date)
    post_data_list.extend(post_data)

# Save post data to a CSV file
post_data_df = pd.DataFrame(post_data_list)  # Create DataFrame from the list
post_data_df.to_csv('post_data.csv', index=False)  # Save to CSV file


# Extract .m3u8 URLs from network logs
def extract_stream_urls(logs):
    video_urls = []
    audio_urls = []
    for log in logs:
        message = json.loads(log['message'])['message']
        if message['method'] == 'Network.requestWillBeSent':
            request_url = message['params']['request']['url']
            if '.m3u8' in request_url:
                if 'mp4a' in request_url:
                    audio_urls.append(request_url)
                elif 'avc1' in request_url:
                    video_urls.append(request_url)
    return video_urls, audio_urls

def get_stream_urls(driver, post_url, max_retries=5, wait_time=5):
    for retries in range(max_retries):
        driver.get(post_url)
        time.sleep(wait_time)
        logs = driver.get_log('performance')
        video_urls, audio_urls = extract_stream_urls(logs)

        if video_urls or audio_urls:
            return video_urls, audio_urls
        print(f"Retry {retries + 1}/{max_retries}: No .m3u8 URL found, refreshing...")
        time.sleep(3)

    return [], []

# Store audio and video URLs in separate lists
all_video_urls = []
all_audio_urls = []

# Fetch audio and video URLs from each post URL in post_data_list
for post in post_data_list:
    print(f"Fetching stream URLs for: {post['url']}")
    video_urls, audio_urls = get_stream_urls(driver, post['url'])
    
    all_video_urls.extend(video_urls)
    all_audio_urls.extend(audio_urls)

# You can use post_data_list, all_video_urls, and all_audio_urls later as needed

# Note: The driver will remain open as per your requirement.
