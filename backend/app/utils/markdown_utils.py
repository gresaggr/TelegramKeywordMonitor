"""Markdown formatting utilities"""


def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram Markdown format
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for Markdown
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text
