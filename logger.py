import logging


class EmojiFormatter(logging.Formatter):
    EMOJIS = {
        logging.DEBUG: "🪲",
        logging.INFO: "❕",
        logging.WARNING: "⚠️",
        logging.ERROR: "💥",
        logging.CRITICAL: "🔥",
    }

    def format(self, record):
        emoji = self.EMOJIS.get(record.levelno, "")
        record.msg = f"{emoji} {record.msg}"
        return super().format(record)


formatter = EmojiFormatter("%(asctime)s: %(levelname)s - %(message)s")
file_handler = logging.FileHandler("log.log", mode="w")
file_handler.setFormatter(formatter)
