
# Twitter/X Video Scraper and Downloader

This Python project automates the process of scraping video posts from Twitter/X and downloads the corresponding video and audio streams. The script then merges the video and audio files using `ffmpeg`.

## Features
- **Automated Twitter/X Login**: Uses Selenium WebDriver to log in and access the feed.
- **Scrolling and Scraping**: Automatically scrolls through a Twitter/X feed to find video posts.
- **Date Filtering**: Filters posts based on the provided date to capture only relevant posts.
- **Video and Audio Extraction**: Extracts video and audio stream URLs from network logs using browser performance logs.
- **Video and Audio Merging**: Downloads and merges the video and audio using `ffmpeg` without re-encoding.

## Requirements
- Python 3.x
- Chrome WebDriver
- Twitter/X account credentials
- `ffmpeg` (for video and audio merging)

### Python Libraries:
- `selenium`
- `pandas`
- `beautifulsoup4`
- `json`
- `subprocess`
  
You can install the required libraries with the following command:
```bash
pip install selenium pandas beautifulsoup4
```

## Usage

### 1. Set Up the Environment
- Download and install the Chrome WebDriver compatible with your Chrome version.
- Ensure `ffmpeg` is installed and accessible in your system's PATH.

### 2. Update Credentials
- Open the script and replace the placeholders for your Twitter/X credentials in the `credentials` dictionary:
  ```python
  credentials = {
      "username": "your_username",
      "password": "your_password"
  }
  ```

### 3. Prepare the Input Data
- Create a CSV file named `urls.csv` with a column `url` that contains the Twitter/X URLs you wish to scrape.

### 4. Run the Script
- The script will automatically log in, scroll through the feed, and capture video and audio URLs based on the provided date.
- To start the scraping process, execute the script with:
  ```bash
  python script_name.py
  ```

### 5. Download and Merge Videos
- The script will download the video and audio streams and merge them into `.mp4` files in the current directory.
- You can modify the `input_date` in the script to filter posts after a specific date:
  ```python
  input_date = "2024-10-10"  # Specify the date to scrape posts from
  ```

### Example Command for Video/Audio Merging
If you want to manually run the ffmpeg command for merging:
```bash
ffmpeg -i video_url -i audio_url -c:v copy -c:a aac -strict experimental output_file.mp4
```

## Notes
- Make sure that you have the necessary permissions to scrape content from Twitter/X.
- This script relies on browser automation, so the performance may vary depending on network speed and Twitter/X's interface updates.

## License
This project is licensed under the MIT License.
