import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import subprocess

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
    "username": "",  # Replace with your Twitter username
    "password": ""   # Replace with your Twitter password
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

    for i in range(250):  # Scrolls through the feed for 250 iterations
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'lxml')

        video_divs = soup.find_all('div', style=True)
        found_video = False

        for video_div in video_divs:
            if any(ignored_class.lower() in child.get('class', []) for child in video_div.find_all(True)):
                continue  # Skip if ignored class is found

            style = video_div.get('style', '')
            if 'translateY' in style:  # Checks for video component
                video_component = video_div.find('div', {'data-testid': 'videoComponent'})
                if not video_component:
                    continue

                post_div = video_div.find('div', class_='css-175oi2r r-18u37iz r-1q142lx')

                if post_div:
                    post_link = post_div.find('a', href=True)
                    time_element = post_div.find('time')
                    post_date = time_element['datetime'] if time_element else None

                    if post_date:
                        if "Pinned" in post_div.text:  # Always skip pinned posts
                            continue  # Skip the pinned post, no matter the date

                        if post_date[:10] > input_date:  # Ignore posts after the input date
                            if "Reposted" in post_div.text:
                                continue
                            else:
                                continue

                        if post_date[:10] == input_date:
                            pass
                        elif post_date[:10] < input_date:
                            return post_data_list  # Stop if we go before the input date

                    if post_link:
                        post_url = post_link['href']
                        if post_url not in seen_urls:
                            post_data_list.append({"url": f"https://x.com{post_url}", "datetime": post_date})
                            seen_urls.add(post_url)
                            found_video = True

        driver.execute_script("window.scrollBy(0, 850);")  # Scroll down
        time.sleep(scroll_pause_time)

    return post_data_list

# Function to extract video/audio stream URLs from browser logs
def extract_stream_urls(logs):
    video_urls = []
    audio_urls = []
    for log in logs:
        message = json.loads(log['message'])['message']
        if message['method'] == 'Network.requestWillBeSent':
            request_url = message['params']['request']['url']
            if '.m3u8' in request_url:
                # Prioritize main video first by checking if it appears before replies
                if 'mp4a' in request_url:
                    audio_urls.append(request_url)
                elif 'avc1' in request_url:
                    video_urls.append(request_url)
    return video_urls, audio_urls

# Function to get stream URLs from a post (with retries)
def get_stream_urls(driver, post_url, max_retries=2, wait_time=5):
    for retries in range(max_retries):
        driver.get(post_url)
        time.sleep(wait_time)  # Wait for the page to load and network requests to be captured
        logs = driver.get_log('performance')
        
        # Extract the main video/audio URLs from the logs
        video_urls, audio_urls = extract_stream_urls(logs)

        if video_urls or audio_urls:
            # Return the first found video and audio URLs (main video)
            return video_urls[:1], audio_urls[:1]  # Return only the main video, if found
        print(f"Retry {retries + 1}/{max_retries}: No .m3u8 URL found, refreshing...")
        time.sleep(3)

    return [], []  # Return empty lists if no URLs are found

# Function to download and merge video and audio
def download_and_merge(video_url, audio_url, output_file):
    try:
        print(f"Downloading and merging video: {video_url} and audio: {audio_url}...")
        command = [
            'ffmpeg', 
            '-i', video_url, 
            '-i', audio_url, 
            '-c:v', 'copy',  # Copy video without re-encoding
            '-c:a', 'aac',   # Re-encode audio to AAC
            '-strict', 'experimental',  # Allow AAC encoding
            output_file
        ]
        subprocess.run(command, check=True)
        print(f"Video and audio combined into {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading and merging: {e}")

# Function to process the video and audio URLs
def process_urls(video_urls, audio_urls):
    for i in range(min(len(video_urls), len(audio_urls))):
        output_file = f"output_video_{i}.mp4"  # Define the output filename
        download_and_merge(video_urls[i], audio_urls[i], output_file)

# Main cycle for scraping and downloading videos
def main(input_date):
    cooldown_period = 30  # Cooldown period in seconds
    cycles = 2  # Number of cycles to run
    post_data_list = []

    for cycle in range(cycles):
        print(f"Cycle {cycle + 1}/{cycles} started at {time.strftime('%Y-%m-%d %H:%M:%S')}")

        for url in urls_to_scrape:
            print(f"Processing URL: {url}")
            driver.get(url)
            post_data = scroll_and_capture_video_urls(input_date)

            # Extend the main post data list
            post_data_list.extend(post_data)

            # Append new post data to the CSV file
            if post_data:
                post_data_df = pd.DataFrame(post_data)  # Create DataFrame from the list
                post_data_df.to_csv('post_data.csv', mode='a', header=False, index=False)  # Append to CSV

        print(f"Cycle {cycle + 1}/{cycles} completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Now process the URLs for downloading
        all_video_urls = []
        all_audio_urls = []

        for post in post_data_list:
            print(f"Fetching stream URLs for: {post['url']}")
            video_urls, audio_urls = get_stream_urls(driver, post['url'])

            # Store only the main video/audio URLs
            if video_urls:
                all_video_urls.append(video_urls[0])  # First (main) video URL
            if audio_urls:
                all_audio_urls.append(audio_urls[0])  # First (main) audio URL

        # Download and merge audio and video files
        process_urls(all_video_urls, all_audio_urls)

        if cycle < cycles - 1:  # Don't wait after the last cycle
            print(f"Cooling down for {cooldown_period} seconds...")
            time.sleep(cooldown_period)

    driver.quit()  # Close the browser when done

# Call the main function with the desired date
if __name__ == "__main__":
    input_date = "2024-10-10"  # Specify the date to scrape posts from
    main(input_date)
