import streamlit as st
import requests
from datetime import datetime, timedelta

# YouTube API Key
API_KEY = "AIzaSyBSskhuPie--IC5apebIRpD3xwCk0lrJ4g"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# App Title
st.title("📺 YouTube Viral Topics Tool")

st.markdown("Configure your search parameters below:")

# Form for Inputs
with st.form("search_form"):
    days = st.number_input("🔁 Days to Search (1-30):", min_value=1, max_value=30, value=5)
    min_subs = st.number_input("👥 Minimum Subscribers:", min_value=0, value=0)
    max_subs = st.number_input("👥 Maximum Subscribers:", min_value=1, value=3000)
    min_duration = st.number_input("⏱️ Min Video Length (minutes):", min_value=0, value=0)
    max_duration = st.number_input("⏱️ Max Video Length (minutes):", min_value=1, value=20)
    min_channel_age = st.number_input("📆 Min Channel Age (years):", min_value=0, value=0)
    results_per_keyword = st.number_input("🎯 Videos per Keyword (1-10):", min_value=1, max_value=10, value=5)

    default_keywords = [
        "Affair Relationship Stories", "Reddit Update", "Reddit Relationship Advice", "Reddit Relationship",
        "Reddit Cheating", "AITA Update", "Open Marriage", "Open Relationship", "X BF Caught",
        "Stories Cheat", "X GF Reddit", "AskReddit Surviving Infidelity", "GurlCan Reddit",
        "Cheating Story Actually Happened", "Cheating Story Real", "True Cheating Story",
        "Reddit Cheating Story", "R/Surviving Infidelity", "Surviving Infidelity",
        "Reddit Marriage", "Wife Cheated I Can't Forgive", "Reddit AP", "Exposed Wife",
        "Cheat Exposed"
    ]

    keyword_input = st.text_area("🗝️ Keywords (comma-separated):", value=", ".join(default_keywords))
    keywords = [kw.strip() for kw in keyword_input.split(",") if kw.strip()]

    submitted = st.form_submit_button("🔍 Fetch Data")

# Main Logic
if submitted:
    try:
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        for keyword in keywords:
            st.write(f"Searching for keyword: **{keyword}**")

            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": results_per_keyword,
                "key": API_KEY,
            }

            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()

            if "items" not in data or not data["items"]:
                st.warning(f"No videos found for keyword: {keyword}")
                continue

            videos = data["items"]
            video_ids = [video["id"]["videoId"] for video in videos if "id" in video and "videoId" in video["id"]]
            channel_ids = [video["snippet"]["channelId"] for video in videos if "snippet" in video and "channelId" in video["snippet"]]

            # Video statistics & content details (for duration)
            stats_params = {
                "part": "statistics,contentDetails",
                "id": ",".join(video_ids),
                "key": API_KEY
            }
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            # Channel statistics & creation date
            channel_params = {
                "part": "statistics,snippet",
                "id": ",".join(channel_ids),
                "key": API_KEY
            }
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()

            stats = stats_data.get("items", [])
            channels = channel_data.get("items", [])

            for video, stat, channel in zip(videos, stats, channels):
                title = video["snippet"].get("title", "N/A")
                description = video["snippet"].get("description", "")[:200]
                video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                views = int(stat["statistics"].get("viewCount", 0))
                subs = int(channel["statistics"].get("subscriberCount", 0))

                # Video duration (ISO 8601 → seconds → minutes)
                iso_duration = stat["contentDetails"]["duration"]
                h, m, s = 0, 0, 0
                time_parts = iso_duration.replace("PT", "").replace("H", " H").replace("M", " M").replace("S", " S").split()
                for part in time_parts:
                    if "H" in part:
                        h = int(part.replace("H", ""))
                    elif "M" in part:
                        m = int(part.replace("M", ""))
                    elif "S" in part:
                        s = int(part.replace("S", ""))
                total_minutes = h * 60 + m + s / 60

                # Channel age in years
                published_at = channel["snippet"]["publishedAt"]
                published_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                channel_age_years = (datetime.utcnow() - published_date).days // 365

                # Filters
                if (min_subs <= subs <= max_subs) and (min_duration <= total_minutes <= max_duration) and (channel_age_years >= min_channel_age):
                    all_results.append({
                        "Title": title,
                        "Description": description,
                        "URL": video_url,
                        "Views": views,
                        "Subscribers": subs,
                        "Duration": f"{int(total_minutes)} min",
                        "Channel Age": f"{channel_age_years} yrs"
                    })

        # Sort by Views (descending)
        all_results.sort(key=lambda x: x["Views"], reverse=True)

        # Display Results
        if all_results:
            st.success(f"✅ Found {len(all_results)} results across all keywords!")
            for result in all_results:
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']:,}  \n"
                    f"**Subscribers:** {result['Subscribers']:,}  \n"
                    f"**Duration:** {result['Duration']}  \n"
                    f"**Channel Age:** {result['Channel Age']}"
                )
                st.write("---")
        else:
            st.warning("⚠️ No results found matching your filters.")

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
