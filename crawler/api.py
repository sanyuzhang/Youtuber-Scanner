from constants import *

import googleapiclient.discovery
import requests
import json
import os


def get_date_by_offset(date, offset):
    """
    Return the string of a date, which is @offset days from @date.
    """
    date = datetime.datetime.strptime(date, "%Y-%m-%d")
    target = date + datetime.timedelta(days=offset)
    return target.strftime("%Y-%m-%d")


def get_channels():
    channels = dict()
    f = open(CHANNELS_PATH, "r")
    for line in f:
        if '/channel/' in line:
            channel_id = line.split('/channel/')[1]
            channel = get_channels_by_id(channel_id)
        elif '/user/' in line:
            user = line.split('/user/')[1]
            channel = get_channels_by_user(user)
        if channel is not None:
            channels.update(channel)
        break  # TODO
    f.close()
    write_to_file(channels)


def get_channels_by_user(user):
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics,id,topicDetails",
        forUsername=user
    )
    return gen_json_data(request.execute())


def get_channels_by_id(channel_id):
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics,id,topicDetails",
        id=channel_id
    )
    return gen_json_data(request.execute())


def gen_json_data(response):
    if len(response['items']) == 0:
        return None

    channel_id = response['items'][0]['id']
    all_playlists_titles, all_playlists_desc, all_videos_titles, all_videos_desc = get_corpus_by_channel_id(channel_id)

    channel = {
        channel_id: {
            "channel_id": channel_id,
            "channel_title": response['items'][0]['snippet']['title'],
            "channel_desc": response['items'][0]['snippet']['description'],
            "channel_create_date": response['items'][0]['snippet']['publishedAt'],
            "channel_url": CHANNEL_URL_PREFIX + response['items'][0]['id'],
            "view_count": int(response['items'][0]['statistics']['viewCount']),
            "video_count": int(response['items'][0]['statistics']['videoCount']),
            "subscriber_count": int(response['items'][0]['statistics']['subscriberCount']),
            "image_url": response['items'][0]['snippet']['thumbnails']['default']['url'],
            "categories": response['items'][0]['topicDetails']['topicCategories'],
            "all_playlists_titles": all_playlists_titles,
            "all_playlists_desc": all_playlists_desc,
            "all_videos_titles": all_videos_titles,
            "all_videos_desc": all_videos_desc
        }
    }
    return channel


def get_corpus_by_channel_id(channel_id):
    if channel_id is None:
        return None, None

    all_playlists_titles, all_playlists_desc, all_videos_titles, all_videos_desc = None, None, None, None

    all_playlists_titles, all_playlists_desc, playlist_ids = get_playlists_by_channel_id(channel_id)

    for id in playlist_ids:
        videos_ids = get_videos_by_playlist_id(id)
        #  TODO

    return all_playlists_titles, all_playlists_desc, all_videos_titles, all_videos_desc


def get_playlists_by_channel_id(channel_id):
    request = youtube.playlists().list(
        part="snippet,contentDetails",
        channelId=channel_id,
        maxResults=50
    )
    response = request.execute()
    all_playlists_titles, all_playlists_desc, playlist_ids = '', '', []
    for playlist in response['items']:
        all_playlists_titles += playlist['snippet']['title'] + ' '
        all_playlists_desc += playlist['snippet']['description'] + ' '
        playlist_ids.append(playlist['id'])
    
    return all_playlists_titles, all_playlists_desc, playlist_ids


def write_to_file(data):
    """
    Write the json data to a file.
    """
    output = json.dumps(data, indent=4)
    file = open(CHANNELS_CORPUS, 'w')
    file.write(output)
    file.close()


if __name__ == '__main__':

    # API Setup
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"

    DEVELOPER_KEY = "AIzaSyAjMXLQV2VFoAiwxYtVrRCkT404E4_lx_I"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=DEVELOPER_KEY)

    # Get channels data
    get_channels()
