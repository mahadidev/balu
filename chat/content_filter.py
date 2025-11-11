"""
Content filtering and validation for global chat system.
Handles URL detection, bad word filtering, and other content checks.
"""

import re
from typing import List


class ContentFilter:
    """Handles content filtering and validation for global chat messages."""
    
    def __init__(self):
        # URL detection patterns
        self.url_patterns = [
            r'https?://[^\s]+',           # http:// or https:// URLs
            r'www\.[^\s]+\.[a-z]{2,}',     # www. URLs
            r'[^\s]+\.[a-z]{2,}/[^\s]*',   # domain.com/path URLs
            r'[^\s]+\.(com|org|net|edu|gov|io|co|me|tv|gg|discord\.gg)[^\s]*',  # Common TLDs
            r'discord\.gg/[^\s]+',        # Discord invites
            r'bit\.ly/[^\s]+',            # Shortened URLs
            r't\.co/[^\s]+',              # Twitter short URLs
            r'youtu\.be/[^\s]+',          # YouTube short URLs
        ]
        
        # Compile regex patterns for better performance
        self.compiled_url_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.url_patterns]
        
        # Bad words list (expandable)
        self.blocked_words = [
            'spam', 'hack', 'cheat', 'exploit', 'scam', 'fraud', 'phishing',
            'malware', 'virus', 'trojan', 'bitcoin', 'crypto', 'investment',
            'get rich quick', 'click here', 'free money'
        ]
    
    def contains_blocked_content(self, content: str) -> bool:
        """
        Check if message contains blocked content.
        
        Args:
            content: Message content to check
            
        Returns:
            bool: True if content contains blocked words
        """
        content_lower = content.lower()
        for word in self.blocked_words:
            if word in content_lower:
                return True
        return False
    
    def contains_url(self, content: str) -> bool:
        """
        Check if message contains URLs or links.
        
        Args:
            content: Message content to check
            
        Returns:
            bool: True if content contains URLs
        """
        for pattern in self.compiled_url_patterns:
            if pattern.search(content):
                return True
        return False
    
    def add_blocked_word(self, word: str) -> None:
        """
        Add a word to the blocked words list.
        
        Args:
            word: Word to block
        """
        if word.lower() not in [w.lower() for w in self.blocked_words]:
            self.blocked_words.append(word.lower())
    
    def remove_blocked_word(self, word: str) -> bool:
        """
        Remove a word from the blocked words list.
        
        Args:
            word: Word to unblock
            
        Returns:
            bool: True if word was removed, False if not found
        """
        try:
            # Find and remove the word (case insensitive)
            for blocked_word in self.blocked_words[:]:  # Copy to avoid modification during iteration
                if blocked_word.lower() == word.lower():
                    self.blocked_words.remove(blocked_word)
                    return True
            return False
        except ValueError:
            return False
    
    def get_blocked_words(self) -> List[str]:
        """
        Get the current list of blocked words.
        
        Returns:
            List[str]: Current blocked words
        """
        return self.blocked_words.copy()