import logging as log
import os

class CustomLogger(log.Logger):
    """Custom logger class to handle logging with different levels."""

    def __init__(self, name: str, level: int = log.DEBUG):
        super().__init__(name, level)

        # Set logger name with prefix
        self.name = f"INSTABOT.{name}"
        self.setLevel(level)

        # Prevent adding handlers multiple times
        if not self.hasHandlers():
            # Create formatter
            formatter = log.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt="%Y-%m-%d %H:%M:%S"
            )

            # Console handler
            ch = log.StreamHandler()
            ch.setLevel(level)
            ch.setFormatter(formatter)
            self.addHandler(ch)

            # File handler
            fh = log.FileHandler('log.log', mode='a+')
            fh.setLevel(level)
            fh.setFormatter(formatter)
            self.addHandler(fh)
