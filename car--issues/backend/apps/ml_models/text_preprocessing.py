"""
Text preprocessing utilities for cleaning complaint text.
Matches the preprocessing from the notebook.
"""
import re
import string
import html
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)


class TextPreprocessor:
    """
    Text preprocessing class for complaint text cleaning.
    Uses the same preprocessing pipeline as the training notebook.
    """

    def __init__(self):
        """Initialize the text preprocessor with lemmatizer."""
        self.lemmatizer = WordNetLemmatizer()

    def normalize_text(self, text, remove_numbers=True, remove_punct=True):
        """
        Preprocess and normalize text.

        Args:
            text: Input text to clean
            remove_numbers: Replace numbers with 'NUM' token
            remove_punct: Remove punctuation

        Returns:
            str: Cleaned and normalized text
        """
        if not isinstance(text, str):
            return ""

        # 1. Lowercase and unescape HTML entities
        text = html.unescape(text.lower())

        # 2. Replace HTML line breaks & multiple spaces
        text = re.sub(r'<br\s*/?>', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        # 3. Remove or replace numbers
        if remove_numbers:
            text = re.sub(r'\d+', 'NUM', text)

        # 4. Remove punctuation
        if remove_punct:
            translator = str.maketrans('', '', string.punctuation)
            text = text.translate(translator)

        # 5. Strip extra spaces
        text = text.strip()

        # 6. Tokenize
        words = word_tokenize(text)

        # 7. Lemmatize
        words = [self.lemmatizer.lemmatize(w) for w in words]

        # 8. Return cleaned text as string
        return ' '.join(words)

    def clean_complaint(self, complaint_text):
        """
        Clean a complaint text for ML model prediction.

        Args:
            complaint_text: Raw complaint text

        Returns:
            str: Cleaned complaint text
        """
        return self.normalize_text(complaint_text)


# Global preprocessor instance
preprocessor = TextPreprocessor()


def clean_text(text):
    """
    Convenience function to clean text using global preprocessor.

    Args:
        text: Input text to clean

    Returns:
        str: Cleaned text
    """
    return preprocessor.clean_complaint(text)
