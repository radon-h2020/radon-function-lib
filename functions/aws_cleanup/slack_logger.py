import requests
from config import SLACK_CONFIG as CONFIG


def post(text):
    # Print also for the CloudWatch Logs
    print(text)
    # TODO should it still print to slack?
    return

    # Slack configurations
    url = CONFIG["webhook_url"]
    bot_name = CONFIG["bot_name"]
    icon_emoji = CONFIG["icon_emoji"]
    channel_override = CONFIG["channel_override"]

    payload = """
  {{
    "username": "{}",
    "icon_emoji": "{}",
    "channel": "{}",
    "text": "{}",
  }}
  """.format(
        bot_name, icon_emoji, channel_override, text
    )
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }

    response = requests.request("POST", url, data=payload, headers=headers)
    if response.text != "ok":
        print(response.text)
