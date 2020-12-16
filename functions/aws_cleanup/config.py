FILTER_CONFIG = {"keep_running": ["prod", "test"], "garbage_collect": "gc", "avoid_terminate": "keep"}
CLEANUP_CONFIG = {
    "DAYS_BEFORE_STOP": 4,
    "DAYS_BEFORE_TERMINATE": 4,
    "STOP_TAG": "Will Stop After",
    "TERMINATE_TAG": "Will Terminate After",
    "EMAIL_SOURCE": "foo@bar.io",
}
SLACK_CONFIG = {
    "webhook_url": "",
    "bot_name": "Logger Bot",
    "icon_emoji": ":aws:",
    # Empty content will post to the default channel specified in the webhook url.
    "channel_override": "",
}
