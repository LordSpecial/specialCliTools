#!/usr/bin/env python3


class Colors:
    """ANSI color codes using Argonaut color scheme"""
    BACKGROUND = '\033[48;2;14;16;25m'
    FOREGROUND = '\033[38;2;255;250;244m'
    RED = '\033[38;2;255;0;15m'
    GREEN = '\033[38;2;140;225;11m'
    BLUE = '\033[38;2;0;141;248m'
    YELLOW = '\033[38;2;255;185;0m'
    CYAN = '\033[38;2;0;216;235m'
    MAGENTA = '\033[38;2;109;67;166m'
    RESET = '\033[0m'

    @classmethod
    def style(cls, text, color):
        """Apply color to text"""
        return f"{color}{text}{cls.RESET}"

    @classmethod
    def error(cls, text):
        return cls.style(text, cls.RED)

    @classmethod
    def success(cls, text):
        return cls.style(text, cls.GREEN)

    @classmethod
    def info(cls, text):
        return cls.style(text, cls.BLUE)

    @classmethod
    def warning(cls, text):
        return cls.style(text, cls.YELLOW)
