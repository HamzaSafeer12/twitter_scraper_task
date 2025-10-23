# Twitter Scraper Task

A Python Selenium/Undetected Chrome scraper to fetch replies from any Twitter (X) post.  
Supports first-time manual login and subsequent automatic login using saved cookies.

---

## Features

- Open any Twitter (X) post URL.
- Fetch the latest replies/comments.
- First-time login manual, subsequent logins via saved cookies.
- Saves replies with user ID, text, and timestamp.

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/HamzaSafeer12/twitter_scraper_task.git
cd twitter_scraper_task

## Create venv and activate
python -m venv venv
.\venv\Scripts\activate

## Instal Dependencies
pip install -r requirements.txt

## RUN
python main.py
