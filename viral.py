import streamlit as st
import requests
from datetime import datetime, timedelta

# YouTube API Key
API_KEY = "AIzaSyBSskhuPie--IC5apebIRpD3xwCk0lrJ4g"  # Replace with your real API key
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Helper: Chunk a list
def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

# Helper: Safely convert to integer
def safe_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

# App Title
st.title("📺 YouTube Viral Topics Tool")
st.markdown("Configure your search parameters below:")

# Form for Inputs
with st.form("search_form"):
    days = st.number_input("🔁 Days to Search (1–30):", min_value=1, max_value=30, value=5)
    min_subs = st.number_input("👥 Minimum Subscribers:", min_value=0, value=0)
    max_subs = st.number_input("👥 Maximum Subscribers:", min_value=1, value=3000)
    min_duration = st.number_input("⏱️ Min Video Length (minutes):", min_value=0, value=0)
    max_duration = st.number_input("⏱️ Max Video Length (minutes):", min_value=1, value=20)
    min_channel_age = st.number_input("📆 Min Channel Age (years):", min_value=0, value=0)
    results_per_keyword = st.number_input("🎯 Videos per Keyword (1–10):", min_value=1, max_value=10, value=5)

    default_keywords = [
        "Real cemetery ghost stories", "Haunted graveyard encounters", "Late night cemetery experiences",
        "Paranormal cemetery footage", "Creepy cemetery at 3AM", "Voices heard in cemetery",
        "Shadow figure in graveyard", "True cemetery horror story", "Exploring haunted graveyard",
        "Scary things caught in cemetery", "Walking alone in old cemetery", "Ghost spotted near tombstone",
        "Graveyard chills and whispers", "Mysterious lights in cemetery", "Cemetery ghost caught on camera",
        "Urban legends from graveyards", "Cemetery rituals gone wrong", "Sleep paralysis after cemetery visit",
        "Strange symbols in cemetery", "Ghost child seen in graveyard"
    ]

    keyword_input = st.text_area("🗝️ Keywords (comma-separated):", value=", ".join(default_keywords))
    keywords = [kw.strip() for kw in keyword_input.split(",") if kw.strip()]

    submitted = st.form_submit_button("🔍 Fetch Data")

# Main Logic
if submitted:
    try:
        with st.spinner("🔄 Fetching and processing video data..."):
            start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
            all_results = []

            for keyword in keywords:
                st.write(f"🔎 Searching for keyword: **{keyword}**")

                search_params = {
                    "part": "snippet",
                    "q": keyword,
                    "type": "video",
                    "order": "viewCount",
                    "publishedAfter": start_date,
                    "maxResults": results_per_keyword,
                    "key": API_KEY,
                }

                try:
                    response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
                    response.raise_for_status()
                    data = response.json()
                except requests.exceptions.HTTPError as http_err:
                    st.warning(f"❌ HTTP error for '{keyword}': {http_err}")
                    continue
                except Exception as e:
                    st.warning(f"❌ General error for '{keyword}': {e}")
                    continue

                if "items" not in data or not data["items"]:
                    st.warning(f"⚠️ No videos found for: {keyword}")
                    st.write(f"📭 Raw API response for '{keyword}':", data)
                    continue

                videos = data["items"]
                video_ids = [v["id"]["videoId"] for v in videos if "videoId" in v["id"]]
                channel_ids = [v["snippet"]["channelId"] for v in videos]

                # Chunked video stats fetch
                video_stats = []
                for chunk in chunk_list(video_ids, 50):
                    stats_params = {
                        "part": "statistics,contentDetails",
                        "id": ",".join(chunk),
                        "key": API_KEY
                    }
                    stats_resp = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
                    stats_data = stats_resp.json()
                    video_stats.extend(stats_data.get("items", []))

                # Chunked channel stats fetch
                channel_stats = []
                for chunk in chunk_list(channel_ids, 50):
                    channel_params = {
                        "part": "statistics,snippet",
                        "id": ",".join(chunk),
                        "key": API_KEY
                    }
                    ch_resp = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
                    ch_data = ch_resp.json()
                    channel_stats.extend(ch_data.get("items", []))

                for video, stat, channel in zip(videos, video_stats, channel_stats):
                    try:
                        title = video["snippet"].get("title", "N/A")
                        description = video["snippet"].get("description", "")[:200]
                        video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                        views = safe_int(stat["statistics"].get("viewCount", 0))
                        subs = safe_int(channel["statistics"].get("subscriberCount", 0))

                        # Duration conversion
                        iso_duration = stat["contentDetails"]["duration"]
                        h, m, s = 0, 0, 0
                        time_parts = iso_duration.replace("PT", "").replace("H", " H").replace("M", " M").replace("S", " S").split()
                        for part in time_parts:
                            if "H" in part: h = int(part.replace("H", ""))
                            elif "M" in part: m = int(part.replace("M", ""))
                            elif "S" in part: s = int(part.replace("S", ""))
                        total_minutes = h * 60 + m + s / 60

                        # Channel age
                        published_at = channel["snippet"]["publishedAt"]
                        published_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                        channel_age_years = (datetime.utcnow() - published_date).days // 365

                        # Apply filters
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
                            st.write(f"✅ Accepted: {title} ({views} views, {subs} subs)")
                        else:
                            st.write(f"❌ Filtered out: {title} — views: {views}, subs: {subs}, duration: {total_minutes:.2f}min, age: {channel_age_years}yrs")

                    except Exception as e:
                        st.write(f"⚠️ Error processing video: {e}")

            # Sort and display
            all_results.sort(key=lambda x: x["Views"], reverse=True)

            if all_results:
                st.success(f"🎉 Found {len(all_results)} matching videos!")
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
                st.warning("⚠️ No results matched your filters.")

    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
