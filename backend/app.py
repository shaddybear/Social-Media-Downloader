
from flask import Flask, request, send_file, send_from_directory, jsonify
import yt_dlp
import instaloader
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')

@app.route('/')
def index():
    logger.info("Serving index.html")
    return send_from_directory('../frontend', 'index.html')

@app.route('/check', methods=['POST'])
def check_media():
    url = request.form.get('url')
    logger.info(f"Received check request: URL={url}")

    if not url:
        logger.error("No URL provided in the request")
        return jsonify({"error": "No URL provided"}), 400

    # Check if URL is Instagram
    if 'instagram.com' in url:
        try:
            L = instaloader.Instaloader()
            shortcode = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
            if 'p/' in url or 'reel/' in url:
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                metadata = {
                    "title": post.caption or 'Instagram Post',
                    "duration": post.video_duration if post.is_video else 0,
                    "thumbnail": post.url if not post.is_video else post.video_url,
                    "quality": "HD"
                }
                logger.info(f"Instagram metadata extracted: {metadata}")
                return jsonify(metadata)
            else:
                return jsonify({"error": "Only Instagram posts and reels are supported"}), 400
        except Exception as e:
            logger.exception(f"Error checking Instagram media: {str(e)}")
            return jsonify({"error": str(e)}), 400

    # YouTube metadata
    options = {
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
            metadata = {
                "title": info.get('title', 'Unknown Title'),
                "duration": info.get('duration', 0),
                "thumbnail": info.get('thumbnail', ''),
                "quality": info.get('resolution', 'Unknown Quality'),
            }
            logger.info(f"YouTube metadata extracted: {metadata}")
            return jsonify(metadata)
    except Exception as e:
        logger.exception(f"Error checking YouTube media: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/download', methods=['POST'])
def download_video():
    url = request.form.get('url')
    format_type = request.form.get('format', 'mp4')
    
    logger.info(f"Received download request: URL={url}, Format={format_type}")

    if not url:
        logger.error("No URL provided in the request")
        return jsonify({"error": "No URL provided"}), 400

    # Instagram download
    if 'instagram.com' in url:
        try:
            L = instaloader.Instaloader()
            shortcode = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
            if 'p/' in url or 'reel/' in url:
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                if post.is_video:
                    file_path = f"downloads/{post.owner_username}_{shortcode}.mp4"
                    L.download_post(post, target='downloads')
                    for file in os.listdir('downloads'):
                        if file.endswith('.mp4') and shortcode in file:
                            file_path = os.path.join('downloads', file)
                            break
                else:
                    return jsonify({"error": "Only video posts are supported"}), 400

                if not os.path.exists(file_path):
                    logger.error(f"Instagram file not found at {file_path}")
                    return jsonify({"error": "File not downloaded"}), 500

                file_size = os.path.getsize(file_path)
                logger.info(f"Instagram file size: {file_size} bytes")

                download_name = f"{post.owner_username}_{shortcode}.mp4"
                logger.info(f"Sending Instagram file: {file_path} as {download_name}")
                response = send_file(file_path, as_attachment=True, download_name=download_name)

                logger.info(f"Cleaning up: Removing {file_path}")
                os.remove(file_path)

                return response
            else:
                return jsonify({"error": "Only Instagram posts and reels are supported"}), 400
        except Exception as e:
            logger.exception(f"Error downloading Instagram media: {str(e)}")
            return jsonify({"error": str(e)}), 400

    # YouTube download
    options = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
    }

    if format_type == 'mp4':
        options.update({
            'format': 'bestvideo[vcodec~="^h264$"][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'merge_output_format': 'mp4',
            'recode_video': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        })
    else:  # MP3
        options.update({
            'format': 'bestaudio[ext=m4a]/bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })

    try:
        if not os.path.exists('downloads'):
            logger.info("Creating downloads directory")
            os.makedirs('downloads')

        logger.debug(f"yt-dlp options: {options}")
        with yt_dlp.YoutubeDL(options) as ydl:
            logger.info(f"Starting download for URL: {url}")
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if format_type == 'mp4' and not file_path.endswith('.mp4'):
                file_path = file_path.rsplit('.', 1)[0] + '.mp4'
            elif format_type == 'mp3':
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'
            logger.info(f"Download completed. File path: {file_path}")

        if not os.path.exists(file_path):
            logger.error(f"File not found at {file_path} after download")
            return jsonify({"error": "File not downloaded"}), 500

        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size} bytes")

        download_name = f"{info.get('title', 'media')}.{format_type}"
        logger.info(f"Sending file: {file_path} as {download_name}")
        response = send_file(file_path, as_attachment=True, download_name=download_name)

        logger.info(f"Cleaning up: Removing {file_path}")
        os.remove(file_path)

        return response
    except Exception as e:
        logger.exception(f"Error downloading video: {str(e)}")
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    logger.info("Starting Flask app")
    app.run(debug=True)


#2nd video##################################################################################
# from flask import Flask, request, send_file, send_from_directory, jsonify
# import yt_dlp
# import instaloader
# import os
# import logging
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()
# INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
# INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

# # Configure logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[logging.StreamHandler()]
# )
# logger = logging.getLogger(__name__)

# app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')

# # Initialize instaloader with login
# L = instaloader.Instaloader()
# try:
#     L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
#     logger.info("Successfully logged into Instagram with instaloader")
# except Exception as e:
#     logger.error(f"Failed to log into Instagram: {str(e)}")
#     raise

# @app.route('/')
# def index():
#     logger.info("Serving index.html")
#     return send_from_directory('../frontend', 'index.html')

# @app.route('/check', methods=['POST'])
# def check_media():
#     url = request.form.get('url')
#     logger.info(f"Received check request: URL={url}")

#     if not url:
#         logger.error("No URL provided in the request")
#         return jsonify({"error": "No URL provided"}), 400

#     # Check if URL is Instagram
#     if 'instagram.com' in url:
#         try:
#             # Extract shortcode or username from URL
#             parts = url.split('/')
#             shortcode = parts[-2] if url.endswith('/') else parts[-1]

#             # Handle Posts and Reels
#             if 'p/' in url or 'reel/' in url:
#                 post = instaloader.Post.from_shortcode(L.context, shortcode)
#                 metadata = {
#                     "title": post.caption or 'Instagram Post',
#                     "duration": post.video_duration if post.is_video else 0,
#                     "thumbnail": post.url if not post.is_video else post.video_url,
#                     "quality": "HD"
#                 }
#                 logger.info(f"Instagram metadata extracted: {metadata}")
#                 return jsonify(metadata)

#             # Handle Stories
#             elif '/s/' in url or '/stories/' in url and 'highlights' not in url:
#                 # Extract username and story media ID
#                 username = parts[parts.index('stories') + 1]
#                 profile = instaloader.Profile.from_username(L.context, username)
#                 for story in profile.get_stories():
#                     for item in story.get_items():
#                         story_id = url.split('story_media_id=')[1].split('&')[0] if 'story_media_id=' in url else None
#                         if str(item.mediaid) == story_id:
#                             metadata = {
#                                 "title": f"Story by {username}",
#                                 "duration": item.video_duration if item.is_video else 0,
#                                 "thumbnail": item.url if not item.is_video else item.video_url,
#                                 "quality": "HD"
#                             }
#                             logger.info(f"Instagram story metadata extracted: {metadata}")
#                             return jsonify(metadata)
#                 return jsonify({"error": "Story not found"}), 404

#             # Handle Highlights
#             elif 'highlights' in url:
#                 highlight_id = shortcode
#                 profile_username = parts[parts.index('stories') + 1]
#                 profile = instaloader.Profile.from_username(L.context, profile_username)
#                 for highlight in profile.get_highlights():
#                     if str(highlight.unique_id) == highlight_id:
#                         # Get the first item from the highlight (for simplicity)
#                         items = list(highlight.get_items())
#                         if not items:
#                             return jsonify({"error": "Highlight is empty"}), 404
#                         item = items[0]
#                         metadata = {
#                             "title": highlight.title or f"Highlight by {profile_username}",
#                             "duration": item.video_duration if item.is_video else 0,
#                             "thumbnail": item.url if not item.is_video else item.video_url,
#                             "quality": "HD"
#                         }
#                         logger.info(f"Instagram highlight metadata extracted: {metadata}")
#                         return jsonify(metadata)
#                 return jsonify({"error": "Highlight not found"}), 404

#             # Handle Profile Pictures
#             elif len(parts) <= 5 and parts[-1] and parts[-1] != '':
#                 username = parts[-1] if not url.endswith('/') else parts[-2]
#                 profile = instaloader.Profile.from_username(L.context, username)
#                 metadata = {
#                     "title": f"Profile Picture of {username}",
#                     "duration": 0,
#                     "thumbnail": profile.profile_pic_url,
#                     "quality": "HD"
#                 }
#                 logger.info(f"Instagram profile picture metadata extracted: {metadata}")
#                 return jsonify(metadata)

#             else:
#                 return jsonify({"error": "Unsupported Instagram content type"}), 400

#         except Exception as e:
#             logger.exception(f"Error checking Instagram media: {str(e)}")
#             return jsonify({"error": str(e)}), 400

#     # YouTube metadata
#     options = {
#         'format': 'best',
#         'noplaylist': True,
#         'quiet': True,
#     }
#     try:
#         with yt_dlp.YoutubeDL(options) as ydl:
#             info = ydl.extract_info(url, download=False)
#             metadata = {
#                 "title": info.get('title', 'Unknown Title'),
#                 "duration": info.get('duration', 0),
#                 "thumbnail": info.get('thumbnail', ''),
#                 "quality": info.get('resolution', 'Unknown Quality'),
#             }
#             logger.info(f"YouTube metadata extracted: {metadata}")
#             return jsonify(metadata)
#     except Exception as e:
#         logger.exception(f"Error checking YouTube media: {str(e)}")
#         return jsonify({"error": str(e)}), 400

# @app.route('/download', methods=['POST'])
# def download_video():
#     url = request.form.get('url')
#     format_type = request.form.get('format', 'mp4')
    
#     logger.info(f"Received download request: URL={url}, Format={format_type}")

#     if not url:
#         logger.error("No URL provided in the request")
#         return jsonify({"error": "No URL provided"}), 400

#     # Instagram download
#     if 'instagram.com' in url:
#         try:
#             parts = url.split('/')
#             shortcode = parts[-2] if url.endswith('/') else parts[-1]

#             # Handle Posts and Reels
#             if 'p/' in url or 'reel/' in url:
#                 post = instaloader.Post.from_shortcode(L.context, shortcode)
#                 if post.is_video:
#                     file_path = f"downloads/{post.owner_username}_{shortcode}.mp4"
#                     L.download_post(post, target='downloads')
#                     for file in os.listdir('downloads'):
#                         if file.endswith('.mp4') and shortcode in file:
#                             file_path = os.path.join('downloads', file)
#                             break
#                 else:
#                     return jsonify({"error": "Only video posts are supported"}), 400

#             # Handle Stories
#             elif '/s/' in url or '/stories/' in url and 'highlights' not in url:
#                 username = parts[parts.index('stories') + 1]
#                 profile = instaloader.Profile.from_username(L.context, username)
#                 for story in profile.get_stories():
#                     for item in story.get_items():
#                         story_id = url.split('story_media_id=')[1].split('&')[0] if 'story_media_id=' in url else None
#                         if str(item.mediaid) == story_id:
#                             if item.is_video:
#                                 file_path = f"downloads/{username}_story_{item.mediaid}.mp4"
#                                 L.download_storyitem(item, target='downloads')
#                                 for file in os.listdir('downloads'):
#                                     if file.endswith('.mp4') and str(item.mediaid) in file:
#                                         file_path = os.path.join('downloads', file)
#                                         break
#                             else:
#                                 return jsonify({"error": "Only video stories are supported"}), 400
#                             break
#                     else:
#                         continue
#                     break
#                 else:
#                     return jsonify({"error": "Story not found"}), 404

#             # Handle Highlights
#             elif 'highlights' in url:
#                 highlight_id = shortcode
#                 profile_username = parts[parts.index('stories') + 1]
#                 profile = instaloader.Profile.from_username(L.context, profile_username)
#                 for highlight in profile.get_highlights():
#                     if str(highlight.unique_id) == highlight_id:
#                         items = list(highlight.get_items())
#                         if not items:
#                             return jsonify({"error": "Highlight is empty"}), 404
#                         item = items[0]  # Download the first item
#                         if item.is_video:
#                             file_path = f"downloads/{profile_username}_highlight_{highlight_id}.mp4"
#                             L.download_storyitem(item, target='downloads')
#                             for file in os.listdir('downloads'):
#                                 if file.endswith('.mp4') and str(item.mediaid) in file:
#                                     file_path = os.path.join('downloads', file)
#                                     break
#                         else:
#                             return jsonify({"error": "Only video highlights are supported"}), 400
#                         break
#                 else:
#                     return jsonify({"error": "Highlight not found"}), 404

#             # Handle Profile Pictures
#             elif len(parts) <= 5 and parts[-1] and parts[-1] != '':
#                 username = parts[-1] if not url.endswith('/') else parts[-2]
#                 profile = instaloader.Profile.from_username(L.context, username)
#                 file_path = f"downloads/{username}_profile_pic.jpg"
#                 L.download_profilepic(profile)
#                 for file in os.listdir('downloads'):
#                     if file.endswith('.jpg') and username in file:
#                         file_path = os.path.join('downloads', file)
#                         break

#             else:
#                 return jsonify({"error": "Unsupported Instagram content type"}), 400

#             if not os.path.exists(file_path):
#                 logger.error(f"Instagram file not found at {file_path}")
#                 return jsonify({"error": "File not downloaded"}), 500

#             file_size = os.path.getsize(file_path)
#             logger.info(f"Instagram file size: {file_size} bytes")

#             download_name = os.path.basename(file_path)
#             logger.info(f"Sending Instagram file: {file_path} as {download_name}")
#             response = send_file(file_path, as_attachment=True, download_name=download_name)

#             logger.info(f"Cleaning up: Removing {file_path}")
#             os.remove(file_path)

#             return response

#         except Exception as e:
#             logger.exception(f"Error downloading Instagram media: {str(e)}")
#             return jsonify({"error": str(e)}), 400

#     # YouTube download
#     options = {
#         'outtmpl': 'downloads/%(title)s.%(ext)s',
#         'noplaylist': True,
#     }

#     if format_type == 'mp4':
#         options.update({
#             'format': 'bestvideo[vcodec~="^h264$"][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
#             'merge_output_format': 'mp4',
#             'recode_video': 'mp4',
#             'postprocessors': [{
#                 'key': 'FFmpegVideoConvertor',
#                 'preferedformat': 'mp4',
#             }],
#         })
#     else:  # MP3
#         options.update({
#             'format': 'bestaudio[ext=m4a]/bestaudio',
#             'postprocessors': [{
#                 'key': 'FFmpegExtractAudio',
#                 'preferredcodec': 'mp3',
#                 'preferredquality': '192',
#             }],
#         })

#     try:
#         if not os.path.exists('downloads'):
#             logger.info("Creating downloads directory")
#             os.makedirs('downloads')

#         logger.debug(f"yt-dlp options: {options}")
#         with yt_dlp.YoutubeDL(options) as ydl:
#             logger.info(f"Starting download for URL: {url}")
#             info = ydl.extract_info(url, download=True)
#             file_path = ydl.prepare_filename(info)
#             if format_type == 'mp4' and not file_path.endswith('.mp4'):
#                 file_path = file_path.rsplit('.', 1)[0] + '.mp4'
#             elif format_type == 'mp3':
#                 file_path = file_path.rsplit('.', 1)[0] + '.mp3'
#             logger.info(f"Download completed. File path: {file_path}")

#         if not os.path.exists(file_path):
#             logger.error(f"File not found at {file_path} after download")
#             return jsonify({"error": "File not downloaded"}), 500

#         file_size = os.path.getsize(file_path)
#         logger.info(f"File size: {file_size} bytes")

#         download_name = f"{info.get('title', 'media')}.{format_type}"
#         logger.info(f"Sending file: {file_path} as {download_name}")
#         response = send_file(file_path, as_attachment=True, download_name=download_name)

#         logger.info(f"Cleaning up: Removing {file_path}")
#         os.remove(file_path)

#         return response
#     except Exception as e:
#         logger.exception(f"Error downloading video: {str(e)}")
#         return jsonify({"error": str(e)}), 400

# if __name__ == '__main__':
#     logger.info("Starting Flask app")
#     app.run(debug=True)

#3rd one code##################################################################################
# # Inside the `/check` endpoint
# # Handle Stories
# from flask import Flask, request, send_file, send_from_directory, jsonify
# import yt_dlp
# import instaloader
# import os
# import logging
# import time

# # Configure logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[logging.StreamHandler()]
# )
# logger = logging.getLogger(__name__)

# app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')

# # Instagram credentials (hardcoded for testing)
# INSTAGRAM_USERNAME = "your_username"  # Replace with your Instagram username
# INSTAGRAM_PASSWORD = "your_password"  # Replace with your Instagram password

# # Initialize instaloader with login
# L = instaloader.Instaloader()
# if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
#     logger.error("Instagram credentials not provided")
#     raise ValueError("Instagram credentials not provided")
# try:
#     L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
#     logger.info("Successfully logged into Instagram with instaloader")
# except instaloader.exceptions.TwoFactorAuthRequiredException:
#     logger.error("Two-factor authentication is required. Please disable 2FA or handle it manually.")
#     raise
# except instaloader.exceptions.BadCredentialsException:
#     logger.error("Invalid Instagram credentials provided.")
#     raise
# except Exception as e:
#     logger.error(f"Failed to log into Instagram: {str(e)}")
#     raise

# @app.route('/')
# def index():
#     logger.info("Serving index.html")
#     return send_from_directory('../frontend', 'index.html')

# @app.route('/check', methods=['POST'])
# def check_media():
#     time.sleep(1)  # Add delay to avoid rate limits
#     url = request.form.get('url')
#     logger.info(f"Received check request: URL={url}")

#     if not url:
#         logger.error("No URL provided in the request")
#         return jsonify({"error": "No URL provided"}), 400

#     # Check if URL is Instagram
#     if 'instagram.com' in url:
#         try:
#             # Extract shortcode or username from URL
#             parts = url.split('/')
#             shortcode = parts[-2] if url.endswith('/') else url.split('?')[0].split('/')[-1]

#             # Handle Posts and Reels
#             if 'p/' in url or 'reel/' in url:
#                 logger.debug(f"Fetching Instagram post/reel with shortcode: {shortcode}")
#                 post = instaloader.Post.from_shortcode(L.context, shortcode)
#                 metadata = {
#                     "title": post.caption or 'Instagram Post',
#                     "duration": post.video_duration if post.is_video else 0,
#                     "thumbnail": post.url if not post.is_video else post.video_url,
#                     "quality": "HD"
#                 }
#                 logger.info(f"Instagram metadata extracted: {metadata}")
#                 return jsonify(metadata)

#             # Handle Stories
#             elif '/s/' in url or '/stories/' in url and 'highlights' not in url:
#                 logger.debug("Fetching Instagram story")
#                 username = parts[parts.index('stories') + 1]
#                 profile = instaloader.Profile.from_username(L.context, username)
#                 for story in profile.get_stories():
#                     for item in story.get_items():
#                         story_id = url.split('story_media_id=')[1].split('&')[0] if 'story_media_id=' in url else None
#                         if str(item.mediaid) == story_id:
#                             metadata = {
#                                 "title": f"Story by {username}",
#                                 "duration": item.video_duration if item.is_video else 0,
#                                 "thumbnail": item.url if not item.is_video else item.video_url,
#                                 "quality": "HD"
#                             }
#                             logger.info(f"Instagram story metadata extracted: {metadata}")
#                             return jsonify(metadata)
#                 return jsonify({"error": "Story not found or has expired"}), 404

#             # Handle Highlights
#             elif 'highlights' in url:
#                 logger.debug("Fetching Instagram highlight")
#                 highlight_id = shortcode
#                 profile_username = parts[parts.index('stories') + 1]
#                 profile = instaloader.Profile.from_username(L.context, profile_username)
#                 for highlight in profile.get_highlights():
#                     if str(highlight.unique_id) == highlight_id:
#                         items = list(highlight.get_items())
#                         if not items:
#                             return jsonify({"error": "Highlight is empty"}), 404
#                         item = items[0]
#                         metadata = {
#                             "title": highlight.title or f"Highlight by {profile_username}",
#                             "duration": item.video_duration if item.is_video else 0,
#                             "thumbnail": item.url if not item.is_video else item.video_url,
#                             "quality": "HD"
#                         }
#                         logger.info(f"Instagram highlight metadata extracted: {metadata}")
#                         return jsonify(metadata)
#                 return jsonify({"error": "Highlight not found"}), 404

#             # Handle Profile Pictures
#             elif len(parts) <= 5 and parts[-1] and parts[-1] != '':
#                 username = parts[-1] if not url.endswith('/') else parts[-2]
#                 logger.debug(f"Fetching Instagram profile for username: {username}")
#                 profile = instaloader.Profile.from_username(L.context, username)
#                 metadata = {
#                     "title": f"Profile Picture of {username}",
#                     "duration": 0,
#                     "thumbnail": profile.profile_pic_url,
#                     "quality": "HD"
#                 }
#                 logger.info(f"Instagram profile picture metadata extracted: {metadata}")
#                 return jsonify(metadata)

#             else:
#                 logger.error("Unsupported Instagram content type")
#                 return jsonify({"error": "Unsupported Instagram content type"}), 400

#         except instaloader.exceptions.ProfileNotExistsException as e:
#             logger.error(f"Profile does not exist: {str(e)}")
#             return jsonify({"error": "Profile does not exist"}), 404
#         except instaloader.exceptions.PrivateProfileNotFollowedException as e:
#             logger.error(f"Profile is private and not followed: {str(e)}")
#             return jsonify({"error": "Profile is private and not followed by the logged-in account"}), 403
#         except instaloader.exceptions.LoginRequiredException as e:
#             logger.error(f"Login required to access content: {str(e)}")
#             return jsonify({"error": "Login required to access this content"}), 401
#         except instaloader.exceptions.BadResponseException as e:
#             logger.error(f"Instagram blocked the request: {str(e)}")
#             return jsonify({"error": "Instagram blocked the request. Try again later or use a different IP."}), 429
#         except Exception as e:
#             logger.exception(f"Error checking Instagram media: {str(e)}")
#             return jsonify({"error": f"Failed to fetch Instagram content: {str(e)}"}), 400

#     # YouTube metadata
#     options = {
#         'format': 'best',
#         'noplaylist': True,
#         'quiet': True,
#     }
#     try:
#         with yt_dlp.YoutubeDL(options) as ydl:
#             info = ydl.extract_info(url, download=False)
#             metadata = {
#                 "title": info.get('title', 'Unknown Title'),
#                 "duration": info.get('duration', 0),
#                 "thumbnail": info.get('thumbnail', ''),
#                 "quality": info.get('resolution', 'Unknown Quality'),
#             }
#             logger.info(f"YouTube metadata extracted: {metadata}")
#             return jsonify(metadata)
#     except Exception as e:
#         logger.exception(f"Error checking YouTube media: {str(e)}")
#         return jsonify({"error": str(e)}), 400

# @app.route('/download', methods=['POST'])
# def download_video():
#     time.sleep(1)  # Add delay to avoid rate limits
#     url = request.form.get('url')
#     format_type = request.form.get('format', 'mp4')
    
#     logger.info(f"Received download request: URL={url}, Format={format_type}")

#     if not url:
#         logger.error("No URL provided in the request")
#         return jsonify({"error": "No URL provided"}), 400

#     # Instagram download
#     if 'instagram.com' in url:
#         try:
#             parts = url.split('/')
#             shortcode = parts[-2] if url.endswith('/') else url.split('?')[0].split('/')[-1]

#             # Handle Posts and Reels
#             if 'p/' in url or 'reel/' in url:
#                 logger.debug(f"Downloading Instagram post/reel with shortcode: {shortcode}")
#                 post = instaloader.Post.from_shortcode(L.context, shortcode)
#                 if post.is_video:
#                     file_path = f"downloads/{post.owner_username}_{shortcode}.mp4"
#                     L.download_post(post, target='downloads')
#                     for file in os.listdir('downloads'):
#                         if file.endswith('.mp4') and shortcode in file:
#                             file_path = os.path.join('downloads', file)
#                             break
#                 else:
#                     return jsonify({"error": "Only video posts are supported"}), 400

#             # Handle Stories
#             elif '/s/' in url or '/stories/' in url and 'highlights' not in url:
#                 logger.debug("Downloading Instagram story")
#                 username = parts[parts.index('stories') + 1]
#                 profile = instaloader.Profile.from_username(L.context, username)
#                 for story in profile.get_stories():
#                     for item in story.get_items():
#                         story_id = url.split('story_media_id=')[1].split('&')[0] if 'story_media_id=' in url else None
#                         if str(item.mediaid) == story_id:
#                             if item.is_video:
#                                 file_path = f"downloads/{username}_story_{item.mediaid}.mp4"
#                                 L.download_storyitem(item, target='downloads')
#                                 for file in os.listdir('downloads'):
#                                     if file.endswith('.mp4') and str(item.mediaid) in file:
#                                         file_path = os.path.join('downloads', file)
#                                         break
#                             else:
#                                 return jsonify({"error": "Only video stories are supported"}), 400
#                             break
#                     else:
#                         continue
#                     break
#                 else:
#                     return jsonify({"error": "Story not found or has expired"}), 404

#             # Handle Highlights
#             elif 'highlights' in url:
#                 logger.debug("Downloading Instagram highlight")
#                 highlight_id = shortcode
#                 profile_username = parts[parts.index('stories') + 1]
#                 profile = instaloader.Profile.from_username(L.context, profile_username)
#                 for highlight in profile.get_highlights():
#                     if str(highlight.unique_id) == highlight_id:
#                         items = list(highlight.get_items())
#                         if not items:
#                             return jsonify({"error": "Highlight is empty"}), 404
#                         item = items[0]
#                         if item.is_video:
#                             file_path = f"downloads/{profile_username}_highlight_{highlight_id}.mp4"
#                             L.download_storyitem(item, target='downloads')
#                             for file in os.listdir('downloads'):
#                                 if file.endswith('.mp4') and str(item.mediaid) in file:
#                                     file_path = os.path.join('downloads', file)
#                                     break
#                         else:
#                             return jsonify({"error": "Only video highlights are supported"}), 400
#                         break
#                 else:
#                     return jsonify({"error": "Highlight not found"}), 404

#             # Handle Profile Pictures
#             elif len(parts) <= 5 and parts[-1] and parts[-1] != '':
#                 username = parts[-1] if not url.endswith('/') else parts[-2]
#                 logger.debug(f"Downloading Instagram profile picture for username: {username}")
#                 profile = instaloader.Profile.from_username(L.context, username)
#                 file_path = f"downloads/{username}_profile_pic.jpg"
#                 L.download_profilepic(profile)
#                 for file in os.listdir('downloads'):
#                     if file.endswith('.jpg') and username in file:
#                         file_path = os.path.join('downloads', file)
#                         break

#             else:
#                 logger.error("Unsupported Instagram content type")
#                 return jsonify({"error": "Unsupported Instagram content type"}), 400

#             if not os.path.exists(file_path):
#                 logger.error(f"Instagram file not found at {file_path}")
#                 return jsonify({"error": "File not downloaded"}), 500

#             file_size = os.path.getsize(file_path)
#             logger.info(f"Instagram file size: {file_size} bytes")

#             download_name = os.path.basename(file_path)
#             logger.info(f"Sending Instagram file: {file_path} as {download_name}")
#             response = send_file(file_path, as_attachment=True, download_name=download_name)

#             logger.info(f"Cleaning up: Removing {file_path}")
#             os.remove(file_path)

#             return response

#         except instaloader.exceptions.ProfileNotExistsException as e:
#             logger.error(f"Profile does not exist: {str(e)}")
#             return jsonify({"error": "Profile does not exist"}), 404
#         except instaloader.exceptions.PrivateProfileNotFollowedException as e:
#             logger.error(f"Profile is private and not followed: {str(e)}")
#             return jsonify({"error": "Profile is private and not followed by the logged-in account"}), 403
#         except instaloader.exceptions.LoginRequiredException as e:
#             logger.error(f"Login required to access content: {str(e)}")
#             return jsonify({"error": "Login required to access this content"}), 401
#         except instaloader.exceptions.BadResponseException as e:
#             logger.error(f"Instagram blocked the request: {str(e)}")
#             return jsonify({"error": "Instagram blocked the request. Try again later or use a different IP."}), 429
#         except Exception as e:
#             logger.exception(f"Error downloading Instagram media: {str(e)}")
#             return jsonify({"error": f"Failed to download Instagram content: {str(e)}"}), 400

#     # YouTube download
#     options = {
#         'outtmpl': 'downloads/%(title)s.%(ext)s',
#         'noplaylist': True,
#     }

#     if format_type == 'mp4':
#         options.update({
#             'format': 'bestvideo[vcodec~="^h264$"][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
#             'merge_output_format': 'mp4',
#             'recode_video': 'mp4',
#             'postprocessors': [{
#                 'key': 'FFmpegVideoConvertor',
#                 'preferedformat': 'mp4',
#             }],
#         })
#     else:  # MP3
#         options.update({
#             'format': 'bestaudio[ext=m4a]/bestaudio',
#             'postprocessors': [{
#                 'key': 'FFmpegExtractAudio',
#                 'preferredcodec': 'mp3',
#                 'preferredquality': '192',
#             }],
#         })

#     try:
#         if not os.path.exists('downloads'):
#             logger.info("Creating downloads directory")
#             os.makedirs('downloads')

#         logger.debug(f"yt-dlp options: {options}")
#         with yt_dlp.YoutubeDL(options) as ydl:
#             logger.info(f"Starting download for URL: {url}")
#             info = ydl.extract_info(url, download=True)
#             file_path = ydl.prepare_filename(info)
#             if format_type == 'mp4' and not file_path.endswith('.mp4'):
#                 file_path = file_path.rsplit('.', 1)[0] + '.mp4'
#             elif format_type == 'mp3':
#                 file_path = file_path.rsplit('.', 1)[0] + '.mp3'
#             logger.info(f"Download completed. File path: {file_path}")

#         if not os.path.exists(file_path):
#             logger.error(f"File not found at {file_path} after download")
#             return jsonify({"error": "File not downloaded"}), 500

#         file_size = os.path.getsize(file_path)
#         logger.info(f"File size: {file_size} bytes")

#         download_name = f"{info.get('title', 'media')}.{format_type}"
#         logger.info(f"Sending file: {file_path} as {download_name}")
#         response = send_file(file_path, as_attachment=True, download_name=download_name)

#         logger.info(f"Cleaning up: Removing {file_path}")
#         os.remove(file_path)

#         return response
#     except Exception as e:
#         logger.exception(f"Error downloading video: {str(e)}")
#         return jsonify({"error": str(e)}), 400

# if __name__ == '__main__':
#     logger.info("Starting Flask app")
#     app.run(debug=True)

#     from flask import Flask, request, send_file, send_from_directory, jsonify
# import yt_dlp
# import instaloader
# import os
# import logging
# import time

# # Configure logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[logging.StreamHandler()]
# )
# logger = logging.getLogger(__name__)

# app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')

# # Instagram credentials (hardcoded for testing)
# INSTAGRAM_USERNAME = "your_username"  # Replace with your Instagram username
# INSTAGRAM_PASSWORD = "your_password"  # Replace with your Instagram password

# # Initialize instaloader with login
# L = instaloader.Instaloader()
# if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
#     logger.error("Instagram credentials not provided")
#     raise ValueError("Instagram credentials not provided")
# try:
#     L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
#     logger.info("Successfully logged into Instagram with instaloader")
# except instaloader.exceptions.TwoFactorAuthRequiredException:
#     logger.error("Two-factor authentication is required. Please disable 2FA or handle it manually.")
#     raise
# except instaloader.exceptions.BadCredentialsException:
#     logger.error("Invalid Instagram credentials provided.")
#     raise
# except Exception as e:
#     logger.error(f"Failed to log into Instagram: {str(e)}")
#     raise

# @app.route('/')
# def index():
#     logger.info("Serving index.html")
#     return send_from_directory('../frontend', 'index.html')

# @app.route('/check', methods=['POST'])
# def check_media():
#     time.sleep(1)  # Add delay to avoid rate limits
#     url = request.form.get('url')
#     logger.info(f"Received check request: URL={url}")

#     if not url:
#         logger.error("No URL provided in the request")
#         return jsonify({"error": "No URL provided"}), 400

#     # Check if URL is Instagram
#     if 'instagram.com' in url:
#         try:
#             # Extract shortcode or username from URL
#             parts = url.split('/')
#             shortcode = parts[-2] if url.endswith('/') else url.split('?')[0].split('/')[-1]

#             # Handle Posts and Reels
#             if 'p/' in url or 'reel/' in url:
#                 logger.debug(f"Fetching Instagram post/reel with shortcode: {shortcode}")
#                 post = instaloader.Post.from_shortcode(L.context, shortcode)
#                 metadata = {
#                     "title": post.caption or 'Instagram Post',
#                     "duration": post.video_duration if post.is_video else 0,
#                     "thumbnail": post.url if not post.is_video else post.video_url,
#                     "quality": "HD"
#                 }
#                 logger.info(f"Instagram metadata extracted: {metadata}")
#                 return jsonify(metadata)

#             # Handle Stories
#             elif '/s/' in url or '/stories/' in url and 'highlights' not in url:
#                 logger.debug("Fetching Instagram story")
#                 username = parts[parts.index('stories') + 1]
#                 profile = instaloader.Profile.from_username(L.context, username)
#                 for story in profile.get_stories():
#                     for item in story.get_items():
#                         story_id = url.split('story_media_id=')[1].split('&')[0] if 'story_media_id=' in url else None
#                         if str(item.mediaid) == story_id:
#                             metadata = {
#                                 "title": f"Story by {username}",
#                                 "duration": item.video_duration if item.is_video else 0,
#                                 "thumbnail": item.url if not item.is_video else item.video_url,
#                                 "quality": "HD"
#                             }
#                             logger.info(f"Instagram story metadata extracted: {metadata}")
#                             return jsonify(metadata)
#                 return jsonify({"error": "Story not found or has expired"}), 404

#             # Handle Highlights
#             elif 'highlights' in url:
#                 logger.debug("Fetching Instagram highlight")
#                 highlight_id = shortcode
#                 profile_username = parts[parts.index('stories') + 1]
#                 profile = instaloader.Profile.from_username(L.context, profile_username)
#                 for highlight in profile.get_highlights():
#                     if str(highlight.unique_id) == highlight_id:
#                         items = list(highlight.get_items())
#                         if not items:
#                             return jsonify({"error": "Highlight is empty"}), 404
#                         item = items[0]
#                         metadata = {
#                             "title": highlight.title or f"Highlight by {profile_username}",
#                             "duration": item.video_duration if item.is_video else 0,
#                             "thumbnail": item.url if not item.is_video else item.video_url,
#                             "quality": "HD"
#                         }
#                         logger.info(f"Instagram highlight metadata extracted: {metadata}")
#                         return jsonify(metadata)
#                 return jsonify({"error": "Highlight not found"}), 404

#             # Handle Profile Pictures
#             elif len(parts) <= 5 and parts[-1] and parts[-1] != '':
#                 username = parts[-1] if not url.endswith('/') else parts[-2]
#                 logger.debug(f"Fetching Instagram profile for username: {username}")
#                 profile = instaloader.Profile.from_username(L.context, username)
#                 metadata = {
#                     "title": f"Profile Picture of {username}",
#                     "duration": 0,
#                     "thumbnail": profile.profile_pic_url,
#                     "quality": "HD"
#                 }
#                 logger.info(f"Instagram profile picture metadata extracted: {metadata}")
#                 return jsonify(metadata)

#             else:
#                 logger.error("Unsupported Instagram content type")
#                 return jsonify({"error": "Unsupported Instagram content type"}), 400

#         except instaloader.exceptions.ProfileNotExistsException as e:
#             logger.error(f"Profile does not exist: {str(e)}")
#             return jsonify({"error": "Profile does not exist"}), 404
#         except instaloader.exceptions.PrivateProfileNotFollowedException as e:
#             logger.error(f"Profile is private and not followed: {str(e)}")
#             return jsonify({"error": "Profile is private and not followed by the logged-in account"}), 403
#         except instaloader.exceptions.LoginRequiredException as e:
#             logger.error(f"Login required to access content: {str(e)}")
#             return jsonify({"error": "Login required to access this content"}), 401
#         except instaloader.exceptions.BadResponseException as e:
#             logger.error(f"Instagram blocked the request: {str(e)}")
#             return jsonify({"error": "Instagram blocked the request. Try again later or use a different IP."}), 429
#         except Exception as e:
#             logger.exception(f"Error checking Instagram media: {str(e)}")
#             return jsonify({"error": f"Failed to fetch Instagram content: {str(e)}"}), 400

#     # YouTube metadata
#     options = {
#         'format': 'best',
#         'noplaylist': True,
#         'quiet': True,
#     }
#     try:
#         with yt_dlp.YoutubeDL(options) as ydl:
#             info = ydl.extract_info(url, download=False)
#             metadata = {
#                 "title": info.get('title', 'Unknown Title'),
#                 "duration": info.get('duration', 0),
#                 "thumbnail": info.get('thumbnail', ''),
#                 "quality": info.get('resolution', 'Unknown Quality'),
#             }
#             logger.info(f"YouTube metadata extracted: {metadata}")
#             return jsonify(metadata)
#     except Exception as e:
#         logger.exception(f"Error checking YouTube media: {str(e)}")
#         return jsonify({"error": str(e)}), 400

# @app.route('/download', methods=['POST'])
# def download_video():
#     time.sleep(1)  # Add delay to avoid rate limits
#     url = request.form.get('url')
#     format_type = request.form.get('format', 'mp4')
    
#     logger.info(f"Received download request: URL={url}, Format={format_type}")

#     if not url:
#         logger.error("No URL provided in the request")
#         return jsonify({"error": "No URL provided"}), 400

#     # Instagram download
#     if 'instagram.com' in url:
#         try:
#             parts = url.split('/')
#             shortcode = parts[-2] if url.endswith('/') else url.split('?')[0].split('/')[-1]

#             # Handle Posts and Reels
#             if 'p/' in url or 'reel/' in url:
#                 logger.debug(f"Downloading Instagram post/reel with shortcode: {shortcode}")
#                 post = instaloader.Post.from_shortcode(L.context, shortcode)
#                 if post.is_video:
#                     file_path = f"downloads/{post.owner_username}_{shortcode}.mp4"
#                     L.download_post(post, target='downloads')
#                     for file in os.listdir('downloads'):
#                         if file.endswith('.mp4') and shortcode in file:
#                             file_path = os.path.join('downloads', file)
#                             break
#                 else:
#                     return jsonify({"error": "Only video posts are supported"}), 400

#             # Handle Stories
#             elif '/s/' in url or '/stories/' in url and 'highlights' not in url:
#                 logger.debug("Downloading Instagram story")
#                 username = parts[parts.index('stories') + 1]
#                 profile = instaloader.Profile.from_username(L.context, username)
#                 for story in profile.get_stories():
#                     for item in story.get_items():
#                         story_id = url.split('story_media_id=')[1].split('&')[0] if 'story_media_id=' in url else None
#                         if str(item.mediaid) == story_id:
#                             if item.is_video:
#                                 file_path = f"downloads/{username}_story_{item.mediaid}.mp4"
#                                 L.download_storyitem(item, target='downloads')
#                                 for file in os.listdir('downloads'):
#                                     if file.endswith('.mp4') and str(item.mediaid) in file:
#                                         file_path = os.path.join('downloads', file)
#                                         break
#                             else:
#                                 return jsonify({"error": "Only video stories are supported"}), 400
#                             break
#                     else:
#                         continue
#                     break
#                 else:
#                     return jsonify({"error": "Story not found or has expired"}), 404

#             # Handle Highlights
#             elif 'highlights' in url:
#                 logger.debug("Downloading Instagram highlight")
#                 highlight_id = shortcode
#                 profile_username = parts[parts.index('stories') + 1]
#                 profile = instaloader.Profile.from_username(L.context, profile_username)
#                 for highlight in profile.get_highlights():
#                     if str(highlight.unique_id) == highlight_id:
#                         items = list(highlight.get_items())
#                         if not items:
#                             return jsonify({"error": "Highlight is empty"}), 404
#                         item = items[0]
#                         if item.is_video:
#                             file_path = f"downloads/{profile_username}_highlight_{highlight_id}.mp4"
#                             L.download_storyitem(item, target='downloads')
#                             for file in os.listdir('downloads'):
#                                 if file.endswith('.mp4') and str(item.mediaid) in file:
#                                     file_path = os.path.join('downloads', file)
#                                     break
#                         else:
#                             return jsonify({"error": "Only video highlights are supported"}), 400
#                         break
#                 else:
#                     return jsonify({"error": "Highlight not found"}), 404

#             # Handle Profile Pictures
#             elif len(parts) <= 5 and parts[-1] and parts[-1] != '':
#                 username = parts[-1] if not url.endswith('/') else parts[-2]
#                 logger.debug(f"Downloading Instagram profile picture for username: {username}")
#                 profile = instaloader.Profile.from_username(L.context, username)
#                 file_path = f"downloads/{username}_profile_pic.jpg"
#                 L.download_profilepic(profile)
#                 for file in os.listdir('downloads'):
#                     if file.endswith('.jpg') and username in file:
#                         file_path = os.path.join('downloads', file)
#                         break

#             else:
#                 logger.error("Unsupported Instagram content type")
#                 return jsonify({"error": "Unsupported Instagram content type"}), 400

#             if not os.path.exists(file_path):
#                 logger.error(f"Instagram file not found at {file_path}")
#                 return jsonify({"error": "File not downloaded"}), 500

#             file_size = os.path.getsize(file_path)
#             logger.info(f"Instagram file size: {file_size} bytes")

#             download_name = os.path.basename(file_path)
#             logger.info(f"Sending Instagram file: {file_path} as {download_name}")
#             response = send_file(file_path, as_attachment=True, download_name=download_name)

#             logger.info(f"Cleaning up: Removing {file_path}")
#             os.remove(file_path)

#             return response

#         except instaloader.exceptions.ProfileNotExistsException as e:
#             logger.error(f"Profile does not exist: {str(e)}")
#             return jsonify({"error": "Profile does not exist"}), 404
#         except instaloader.exceptions.PrivateProfileNotFollowedException as e:
#             logger.error(f"Profile is private and not followed: {str(e)}")
#             return jsonify({"error": "Profile is private and not followed by the logged-in account"}), 403
#         except instaloader.exceptions.LoginRequiredException as e:
#             logger.error(f"Login required to access content: {str(e)}")
#             return jsonify({"error": "Login required to access this content"}), 401
#         except instaloader.exceptions.BadResponseException as e:
#             logger.error(f"Instagram blocked the request: {str(e)}")
#             return jsonify({"error": "Instagram blocked the request. Try again later or use a different IP."}), 429
#         except Exception as e:
#             logger.exception(f"Error downloading Instagram media: {str(e)}")
#             return jsonify({"error": f"Failed to download Instagram content: {str(e)}"}), 400

#     # YouTube download
#     options = {
#         'outtmpl': 'downloads/%(title)s.%(ext)s',
#         'noplaylist': True,
#     }

#     if format_type == 'mp4':
#         options.update({
#             'format': 'bestvideo[vcodec~="^h264$"][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
#             'merge_output_format': 'mp4',
#             'recode_video': 'mp4',
#             'postprocessors': [{
#                 'key': 'FFmpegVideoConvertor',
#                 'preferedformat': 'mp4',
#             }],
#         })
#     else:  # MP3
#         options.update({
#             'format': 'bestaudio[ext=m4a]/bestaudio',
#             'postprocessors': [{
#                 'key': 'FFmpegExtractAudio',
#                 'preferredcodec': 'mp3',
#                 'preferredquality': '192',
#             }],
#         })

#     try:
#         if not os.path.exists('downloads'):
#             logger.info("Creating downloads directory")
#             os.makedirs('downloads')

#         logger.debug(f"yt-dlp options: {options}")
#         with yt_dlp.YoutubeDL(options) as ydl:
#             logger.info(f"Starting download for URL: {url}")
#             info = ydl.extract_info(url, download=True)
#             file_path = ydl.prepare_filename(info)
#             if format_type == 'mp4' and not file_path.endswith('.mp4'):
#                 file_path = file_path.rsplit('.', 1)[0] + '.mp4'
#             elif format_type == 'mp3':
#                 file_path = file_path.rsplit('.', 1)[0] + '.mp3'
#             logger.info(f"Download completed. File path: {file_path}")

#         if not os.path.exists(file_path):
#             logger.error(f"File not found at {file_path} after download")
#             return jsonify({"error": "File not downloaded"}), 500

#         file_size = os.path.getsize(file_path)
#         logger.info(f"File size: {file_size} bytes")

#         download_name = f"{info.get('title', 'media')}.{format_type}"
#         logger.info(f"Sending file: {file_path} as {download_name}")
#         response = send_file(file_path, as_attachment=True, download_name=download_name)

#         logger.info(f"Cleaning up: Removing {file_path}")
#         os.remove(file_path)

#         return response
#     except Exception as e:
#         logger.exception(f"Error downloading video: {str(e)}")
#         return jsonify({"error": str(e)}), 400

# if __name__ == '__main__':
#     logger.info("Starting Flask app")
#     app.run(debug=True)

# elif '/s/' in url or '/stories/' in url:
#     logger.debug("Processing Instagram story or highlight")
#     username = parts[parts.index('stories') + 1] if 'stories' in parts else None
#     if not username:
#         # Extract username from the URL if it's in the /s/ format
#         decoded_id = parts[parts.index('s') + 1].split('?')[0]
#         if decoded_id.startswith('aGlnaGxpZ2h0Oj'):
#             # This is a highlight URL in /s/ format
#             highlight_id = decoded_id.replace('aGlnaGxpZ2h0Oj', 'highlight:')
#             profile = instaloader.Profile.from_username(L.context, username)
#             for highlight in profile.get_highlights():
#                 if highlight_id == f"highlight:{highlight.unique_id}":
#                     items = list(highlight.get_items())
#                     if not items:
#                         return jsonify({"error": "Highlight is empty"}), 404
#                     # Find the specific item if story_media_id is provided
#                     story_id = url.split('story_media_id=')[1].split('&')[0] if 'story_media_id=' in url else None
#                     for item in items:
#                         if story_id and str(item.mediaid) == story_id:
#                             metadata = {
#                                 "title": highlight.title or f"Highlight by {username}",
#                                 "duration": item.video_duration if item.is_video else 0,
#                                 "thumbnail": item.url if not item.is_video else item.video_url,
#                                 "quality": "HD"
#                             }
#                             logger.info(f"Instagram highlight metadata extracted: {metadata}")
#                             return jsonify(metadata)
#                     # If no specific item is found, return the first item
#                     item = items[0]
#                     metadata = {
#                         "title": highlight.title or f"Highlight by {username}",
#                         "duration": item.video_duration if item.is_video else 0,
#                         "thumbnail": item.url if not item.is_video else item.video_url,
#                         "quality": "HD"
#                     }
#                     logger.info(f"Instagram highlight metadata extracted: {metadata}")
#                     return jsonify(metadata)
#             return jsonify({"error": "Highlight not found"}), 404
#         else:
#             return jsonify({"error": "Invalid story or highlight URL"}), 400

#     profile = instaloader.Profile.from_username(L.context, username)
#     if 'highlights' in url:
#         logger.debug("Fetching Instagram highlight")
#         highlight_id = shortcode
#         for highlight in profile.get_highlights():
#             if str(highlight.unique_id) == highlight_id:
#                 items = list(highlight.get_items())
#                 if not items:
#                     return jsonify({"error": "Highlight is empty"}), 404
#                 item = items[0]
#                 metadata = {
#                     "title": highlight.title or f"Highlight by {username}",
#                     "duration": item.video_duration if item.is_video else 0,
#                     "thumbnail": item.url if not item.is_video else item.video_url,
#                     "quality": "HD"
#                 }
#                 logger.info(f"Instagram highlight metadata extracted: {metadata}")
#                 return jsonify(metadata)
#         return jsonify({"error": "Highlight not found"}), 404
#     else:
#         logger.debug("Fetching Instagram story")
#         for story in profile.get_stories():
#             for item in story.get_items():
#                 story_id = url.split('story_media_id=')[1].split('&')[0] if 'story_media_id=' in url else None
#                 if str(item.mediaid) == story_id:
#                     metadata = {
#                         "title": f"Story by {username}",
#                         "duration": item.video_duration if item.is_video else 0,
#                         "thumbnail": item.url if not item.is_video else item.video_url,
#                         "quality": "HD"
#                     }
#                     logger.info(f"Instagram story metadata extracted: {metadata}")
#                     return jsonify(metadata)
#         return jsonify({"error": "Story not found or has expired"}), 404

# # Inside the `/download` endpoint
# # Handle Stories
# elif '/s/' in url or '/stories/' in url:
#     logger.debug("Downloading Instagram story or highlight")
#     username = parts[parts.index('stories') + 1] if 'stories' in parts else None
#     if not username:
#         # Extract username from the URL if it's in the /s/ format
#         decoded_id = parts[parts.index('s') + 1].split('?')[0]
#         if decoded_id.startswith('aGlnaGxpZ2h0Oj'):
#             # This is a highlight URL in /s/ format
#             highlight_id = decoded_id.replace('aGlnaGxpZ2h0Oj', 'highlight:')
#             profile = instaloader.Profile.from_username(L.context, username)
#             for highlight in profile.get_highlights():
#                 if highlight_id == f"highlight:{highlight.unique_id}":
#                     items = list(highlight.get_items())
#                     if not items:
#                         return jsonify({"error": "Highlight is empty"}), 404
#                     # Find the specific item if story_media_id is provided
#                     story_id = url.split('story_media_id=')[1].split('&')[0] if 'story_media_id=' in url else None
#                     for item in items:
#                         if story_id and str(item.mediaid) == story_id:
#                             if item.is_video:
#                                 file_path = f"downloads/{username}_highlight_{highlight_id}_{item.mediaid}.mp4"
#                                 L.download_storyitem(item, target='downloads')
#                                 for file in os.listdir('downloads'):
#                                     if file.endswith('.mp4') and str(item.mediaid) in file:
#                                         file_path = os.path.join('downloads', file)
#                                         break
#                             else:
#                                 return jsonify({"error": "Only video highlights are supported"}), 400
#                             break
#                     else:
#                         # If no specific item is found, download the first item
#                         item = items[0]
#                         if item.is_video:
#                             file_path = f"downloads/{username}_highlight_{highlight_id}.mp4"
#                             L.download_storyitem(item, target='downloads')
#                             for file in os.listdir('downloads'):
#                                 if file.endswith('.mp4') and str(item.mediaid) in file:
#                                     file_path = os.path.join('downloads', file)
#                                     break
#                         else:
#                             return jsonify({"error": "Only video highlights are supported"}), 400
#                     break
#             else:
#                 return jsonify({"error": "Highlight not found"}), 404
#         else:
#             return jsonify({"error": "Invalid story or highlight URL"}), 400

#     profile = instaloader.Profile.from_username(L.context, username)
#     if 'highlights' in url:
#         logger.debug("Downloading Instagram highlight")
#         highlight_id = shortcode
#         for highlight in profile.get_highlights():
#             if str(highlight.unique_id) == highlight_id:
#                 items = list(highlight.get_items())
#                 if not items:
#                     return jsonify({"error": "Highlight is empty"}), 404
#                 item = items[0]
#                 if item.is_video:
#                     file_path = f"downloads/{username}_highlight_{highlight_id}.mp4"
#                     L.download_storyitem(item, target='downloads')
#                     for file in os.listdir('downloads'):
#                         if file.endswith('.mp4') and str(item.mediaid) in file:
#                             file_path = os.path.join('downloads', file)
#                             break
#                 else:
#                     return jsonify({"error": "Only video highlights are supported"}), 400
#                 break
#         else:
#             return jsonify({"error": "Highlight not found"}), 404
#     else:
#         logger.debug("Downloading Instagram story")
#         for story in profile.get_stories():
#             for item in story.get_items():
#                 story_id = url.split('story_media_id=')[1].split('&')[0] if 'story_media_id=' in url else None
#                 if str(item.mediaid) == story_id:
#                     if item.is_video:
#                         file_path = f"downloads/{username}_story_{item.mediaid}.mp4"
#                         L.download_storyitem(item, target='downloads')
#                         for file in os.listdir('downloads'):
#                             if file.endswith('.mp4') and str(item.mediaid) in file:
#                                 file_path = os.path.join('downloads', file)
#                                 break
#                     else:
#                         return jsonify({"error": "Only video stories are supported"}), 400
#                     break
#             else:
#                 continue
#             break
#         else:
#             return jsonify({"error": "Story not found or has expired"}), 404