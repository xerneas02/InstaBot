## Disclaimer ⚠️

Instagram's terms of service discourage automated posting and can flag or ban accounts that use bots. We strongly **do not recommend** using your **main Instagram account** with this tool. Consider creating a separate or test account to avoid risking your primary account being limited, blocked, or permanently banned.

# InstaBot

InstaBot is a Python automation project that generates panoramic images from Google Street View, transforms them into creative "tiny planet" views, downloads flat images, and optionally posts images and Instagram stories via the Instagram API. The project also provides functionality to generate CO₂ evolution images for Instagram Story posts.

## Features

* **Image Generation**:
  Downloads Street View images, stitches six faces into a panorama, and creates several transformation versions (e.g. tiny planet).
* **Weather & Reverse Geocoding**:
  Retrieves weather information and reverse geocodes the location using Open-Meteo and Nominatim.
* **Instagram Integration**:
  Uses the instagrapi library to log into Instagram, publish image albums, and post Instagram Stories.
* **CO₂ Story Creator**:
  Generates an image showing CO₂ evolution over 10 years, combining matplotlib graphs and overlay texts.
* **Custom Logging**:
  A custom logger (`custom_logger.py`) to record events and errors for traceability.

## Project Structure

```
InstaBot/
├── .github/
│   └── workflows/
│       ├── post_image.yaml   # GitHub Action for posting images daily at 06:00 UTC
│       └── post_story.yaml   # GitHub Action for posting a story (every Saturday at 06:00 UTC)
├── assets/
│   ├── fonts/
│   │   └── Arial.ttf (example font)
│   └── images/
│       └── carbonBG.jpg  (background for CO₂ story)
├── src/
│   ├── carbon.py              # Generates the CO₂ evolution image and posts as story on Instagram
│   ├── custom_logger.py       # Custom logging implementation
│   ├── generate_cookie.py     # Creates and saves an Instagram session (cookie)
│   ├── image_analyzer.py      # Determines the best image among multiple candidate images
│   ├── image_generator.py     # Downloads and generates the panorama images and applies transformations
│   ├── instagram_bot.py       # Main Instagram bot thumbnail for image album posting
│   ├── meteo.py               # Retrieves current weather information
│   ├── options.py             # Config options (e.g. whether to publish on Instagram)
│   ├── streetview_downloader.py  # Downloads Street View tiles and assembles images
│   └── tiny_planet_transformer.py # Transforms images into tiny planet view
├── insta_session.json         # Saved Instagram session settings
├── requirements.txt           # Project dependencies
└── .gitignore                 # Files/folders to ignore in Git
```

## Requirements

The project requires Python 3.12 and the dependencies listed in `requirements.txt`:

```
matplotlib
geopy
numpy
opencv-python
Pillow
pyowm
instagrapi
requests
scikit-image
streetview
py360convert
```

## Setup

1. Clone the Repository:
   `bash
       git clone https://your.repo.url/InstaBot.git
       cd InstaBot
       `

2. Install Dependencies:
   On Windows, run:
   `bash
       python -m pip install --upgrade pip
       pip install -r requirements.txt
       `

3. Environment Variables:
   Set the following environment variables:

   * `LOGIN_INSTAGRAM`: Your Instagram username.
   * `PASSWORD_INSTAGRAM`: Your Instagram password.
   * `GOOGLE_KEY`: Your Google API key for Street View.
     You can create a `.env` file or configure them in your system.

4. Session Generation (optional):
   To generate the Instagram session and save it into `src/insta_session.json`, run:

   ```bash
   python src/generate_cookie.py
   ```

## Usage

* **Run Instagram Bot**:
  The main bot program is invoked from `src/instagram_bot.py`. To run the bot:

  ```bash
  python src/instagram_bot.py
  ```

  The bot will generate images, login to Instagram, and post the album if the `PUBLISH` option is set to `True`.

* **CO₂ Story Posting**:
  To generate and post a CO₂ evolution story, execute:

  ```bash
  python src/carbon.py
  ```

* **GitHub Actions**:
  The workflows defined in `post_image.yaml` and `post_story.yaml` allow scheduled or manual trigger posting of images/stories.

## Logging

All logs are managed by the custom logger defined in `custom_logger.py`. Logs are output to both the console and the file `log.log`.

## Disclaimer

⚠️ **Caution:** Instagram's terms of service discourage automated posting and can flag or ban accounts that use bots. We strongly **do not recommend** using your **main Instagram account** with this tool. Consider creating a separate or test account to avoid risking your primary account being limited, blocked, or permanently banned.
