# setup configuration for DumpsterDiver
CONFIG = {
    "logfile": "./errors.log",
    "base64_chars": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",
    "archive_types": [".zip", ".tar.gz", ".tgz", ".tar.bz2", ".tbz"],
    "excluded_files": [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".svg",
        ".mp4",
        ".mp3",
        ".webm",
        ".ttf",
        ".woff",
        ".eot",
        ".css",
        ".DS_Store",
        ".pdf",
    ],
    "bad_expressions": [],
    "min_key_length": 20,
    "max_key_length": 80,
    "high_entropy_edge": 3.2,
    "min_pass_length": 8,
    "max_pass_length": 256,
    "password_complexity": 8,
}

#  define rules
RULES = {
    "filetype": [".*"],
    "filetype_weight": 0,
    "grep_words": ["*pass*", "*secret*"],
    "grep_word_occurrence": 1,
    "grep_words_weight": 10,
}
