import requests
import telebot
import yt_dlp
import os
from configparser import ConfigParser
import re
import mega_helpers

# REQUIREMENTS
# sudo apt-get install ffmpeg
# pip install telebot yt_dlp

config = ConfigParser()
config.read("config.ini")
TELEGRAM_BOT_TOKEN = config.get("Telegram", "access_token")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def get_available_formats(video_info):
    formats_list = []

    index = 2  # Start index at 1
    # Mp3 music
    formats_dict = {"index": 1,
                    "resolution": "Default",
                    "format_note": "music",
                    "ext": "mp3",
                    "format_id": "000",
                    }
    formats_list.append(formats_dict)

    # Other formats
    for vformat in video_info['formats']:
        f_size_bytes = vformat.get('filesize', 'N/A')
        format_note = vformat.get('format_note', 'N/A')
        resolution = vformat.get('resolution', 'N/A')
        ext = vformat.get('ext', 'N/A')
        format_id = vformat.get('format_id', 'N/A')
        audio_codec = vformat.get('acodec', 'N/A')

        if format_note != "N/A" \
                and ext != "mhtml" and format_id != "N/A" \
                and (audio_codec != "N/A" and audio_codec != "none") \
                and (resolution != "audio only" and format_note != "Default"):
            formats_dict = {"index": index,
                            "resolution": resolution,
                            "format_note": format_note,
                            "ext": ext,
                            "format_id": format_id,
                            }
            formats_list.append(formats_dict)
            index += 1  # Only increment for valid formats
    return formats_list

def is_integer(string):
    try:
        int(string)
        return True
    except ValueError:
        return False
def clean_filename(s: str) -> str:
    parts = s.rsplit('.', 1)
    if len(parts) == 2:
        name, extension = parts
    else:
        name, extension = s, ''
    cleaned_name = re.sub('[^a-zA-Z0-9]+', '-', name)
    cleaned_string = cleaned_name + ('.' + extension if extension else '')
    return cleaned_string


def is_valid_youtube_link(link):
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)

            # Check if the video is part of a playlist
            if 'entries' in info_dict:
                return False

            # Check if the video has multiple parts (e.g., is not a direct video link)
            if 'parts' in info_dict:
                return False

            # If none of the above conditions are met, consider it a valid direct video link
            return True
    except yt_dlp.utils.DownloadError:
        return False
def download_video_audio(url, selected_format, output_path, file_name,file_extension):
    file_name = clean_filename(file_name)
    # AUDIO
    if selected_format == "000":
        output_file = os.path.join(output_path, clean_filename(
            f'{file_name}'))  # for some reason this adds the extension to the name
        # Audio download
        ydl_opts = {
            'outtmpl': output_file,
        }
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }]
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        try:
            os.remove(output_file) # Remove video source after extracting audio
        except Exception as e:
            print ("Exception: ", e)
        output_file = output_file + '.mp3'  # put the right file extension
        print("output_file_updated", output_file)
    else:
        output_file = os.path.join(output_path, clean_filename(f'{file_name}.{file_extension}'))
        with yt_dlp.YoutubeDL({'format': selected_format, 'outtmpl': output_file}) as ydl:
            ydl.download([url])

    return output_file

def yt_dl_init(url):
    # Create a YouTubeDL object
    ydl_opts = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Get video information
        video_info = ydl.extract_info(url, download=False)

        # Print available formats and ask the user to choose one
        formats = get_available_formats(video_info)
        return formats, video_info

# Dictionary to store user states
user_states = {}
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    # Check if the user is in the middle of the conversation
    if chat_id in user_states:
        handle_user_response(message)
    else:
        handle_initial_message(message)

def handle_initial_message(message):
    if '\n' not in message.text \
            and (message.text.startswith('https://www.youtube.com/')
            or message.text.startswith('https://youtu.be/')
            or message.text.startswith('https://m.youtube.com/')):
        chat_id = message.chat.id
        user_states[chat_id] = {'state': "CHECKING_LINK"}
        if is_valid_youtube_link(message.text):
            formats, video_info = yt_dl_init(message.text)
            message_formats=[] # variable to nicely print the formats in the chat
            for dic in formats:
                line = str(dic[list(dic.keys())[0]]) + ". " + "-".join([str(dic[k]) for k in list(dic.keys())[1:4]])
                message_formats.append(line)
            bot.send_message(message.chat.id, '\n'.join(message_formats))


            user_states[chat_id]['video_info'] =video_info
            user_states[chat_id]['url'] = message.text
            user_states[chat_id]['formats'] = formats
            user_states[chat_id]['state'] = "WAITING_FOR_RESPONSE"
            bot.send_message(message.chat.id, "Please respond with the index of your choice or type \"cancel\"")
        else:
            bot.send_message(message.chat.id, "Only direct video link allowed (no playlists or others)")
    else:
        bot.send_message(message.chat.id, "Only Youtube links are allowed")

def handle_user_response(message):
    chat_id = message.chat.id
    downloads_folder = "./downloads"
    if message.text == "cancel" and user_states[chat_id]['state'] != "SENDING_VIDEO":
        bot.send_message(chat_id, "Ok")
        del user_states[chat_id]
    else:
        if user_states[chat_id]['state'] == "WAITING_FOR_RESPONSE":
            selected_index = message.text
            if is_integer(selected_index): # if integer provided
                selected_index = int(message.text) -1 #reads the selected format
                print (selected_index)
                print (user_states[chat_id]['formats'])
                if (selected_index < len(user_states[chat_id]['formats']) and selected_index >= 0): # if selection in the list

                    user_states[chat_id]['state'] = "SENDING_VIDEO"

                    selected_format_id = user_states[chat_id]['formats'][selected_index]['format_id']
                    file_name = user_states[chat_id]['video_info']['title']
                    file_extension=user_states[chat_id]['formats'][selected_index]['ext']
                    url = user_states[chat_id]['url']

                    bot.send_message(chat_id, "Processing request")
                    downloaded_file=download_video_audio(url, selected_format_id, downloads_folder, file_name, file_extension)

                    file_size = os.path.getsize(downloaded_file) # Telegram file-size limits
                    if file_size < 50000000:
                        # Upload to Telegram
                        bot.send_message(chat_id, "Download completed!")
                        try:
                            with open(downloaded_file, 'rb') as file:
                                bot.send_document(chat_id, file, timeout=200)
                                print ("File sent via Telegram")
                            if os.path.exists(downloaded_file):
                                os.remove(downloaded_file)
                                print("Deleting local file1 : ", downloaded_file)
                        except requests.exceptions.SSLError as e:
                            bot.send_message(chat_id, "There was a communication problem, please try again")
                            if os.path.exists(downloaded_file):
                                os.remove(downloaded_file)
                                print("Deleting local file2 : ", downloaded_file)
                    else:
                        bot.send_message(chat_id, "File exceeds the size limits for Bots, a download link will be provided, "
                                                  "\nThis might take a while,"
                                                  "\nPlease wait")
                        # Upload to Mega
                        link = mega_helpers.upload(downloaded_file)
                        bot.send_message(chat_id, link)  # sends link to dropbox file

                        if os.path.exists(downloaded_file):
                            os.remove(downloaded_file)
                            print("removed: ", downloaded_file)
                    del user_states[chat_id] # REQUEST COMPLETED, DELETE SESSION
                else:
                    bot.send_message(chat_id, "Provide a number in the list")
            else:
                bot.send_message(chat_id, "Only numbers are allowed")

            # Cleanup user state

        elif user_states[chat_id]['state'] == "SENDING_VIDEO":
            bot.send_message(chat_id, "Max 1 request at a time, please wait")
        else:
            bot.send_message(chat_id, "Be patient")

bot.polling()
