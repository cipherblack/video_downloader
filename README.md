
# Video Downloader Bot

This Telegram bot allows users to download videos from major websites like Pornhub. Users can download their desired videos by sending video links.

## Features

- Download videos from Pornhub links.
- View online and search Pornhub.
- Only users with a subscription can use the bot.
- Option to add custom websites to the bot.

## Prerequisites

You will need the following to run this bot:

- Python 3.7 or higher

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/cipherblack/video_downloader.git
   ```
   
2. Navigate to the project folder:
   ```bash
   cd video_downloader
   ```

3. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # for Linux/Mac
   venv\Scripts\activate     # for Windows
   ```

4. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Configure the settings in the main file:
   - Enter the **API Token** for your Telegram bot.
   - Specify the **Admin IDs** and **Owner ID**.
   - Specify the **admin_id** like @deviloer and **channle_id** like @durov.
   - Check and configure the SQLite database settings.

## Changes

- **To add other sites:** If you want to add new sites for downloading, you will need to modify the sections in the bot code related to the URL of the sites.
  
- **To add new features:** You can easily add new buttons and commands to the bot. For example, adding a button for sharing or creating new commands for content management.

## Security Notes

- Ensure that **only authorized users** have access to the bot.
- Use encryption for storing sensitive information like API tokens.

## For Developers

- If you plan to add new features to the bot, please create an **Issue** first to coordinate with the development team.
- To check the database and user changes, you can use database management tools like `DB Browser for SQLite`.

## Contact

For help or to report issues, please contact the bot admin:
- [@Deviloer](https://t.me/deviloer)
- [robot example](https://t.me/pornhubdownloader_bot) 
