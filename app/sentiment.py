import logging
from textblob import TextBlob
import re
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Sentiment analysis using TextBlob"""
    
    def __init__(self):
        self.positive_words = {
            'excellent', 'amazing', 'fantastic', 'great', 'good', 'wonderful',
            'awesome', 'outstanding', 'brilliant', 'perfect', 'love', 'like',
            'happy', 'pleased', 'satisfied', 'impressed', 'helpful', 'useful',
            'easy', 'simple', 'quick', 'fast', 'efficient', 'reliable'
        }
        
        self.negative_words = {
            'terrible', 'awful', 'horrible', 'bad', 'worst', 'hate', 'dislike',
            'disappointed', 'frustrated', 'angry', 'upset', 'annoyed', 'useless',
            'broken', 'failed', 'error', 'problem', 'issue', 'bug', 'slow',
            'difficult', 'confusing', 'complicated', 'expensive', 'overpriced'
        }
        
        self.intensifiers = {
            'very', 'extremely', 'incredibly', 'absolutely', 'completely',
            'totally', 'really', 'quite', 'pretty', 'fairly'
        }
    
    def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Analyze sentiment of given text
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (sentiment_label, confidence_score)
        """
        if not text or not text.strip():
            return 'neutral', 0.0
        
        try:
            # Clean text
            clean_text = self._preprocess_text(text)
            
            # Use TextBlob for basic sentiment analysis
            blob = TextBlob(clean_text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Enhanced analysis with custom rules
            enhanced_sentiment, confidence = self._enhanced_analysis(clean_text, polarity, subjectivity)
            
            logger.info(f"Sentiment analysis: '{text[:50]}...' -> {enhanced_sentiment} ({confidence:.2f})")
            
            return enhanced_sentiment, confidence
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return 'neutral', 0.0
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove email signatures (common patterns)
        text = re.sub(r'--\s*\n.*', '', text, flags=re.DOTALL)
        text = re.sub(r'____+\s*\n.*', '', text, flags=re.DOTALL)
        text = re.sub(r'from:.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'sent:.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'to:.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'subject:.*', '', text, flags=re.IGNORECASE)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _enhanced_analysis(self, text: str, polarity: float, subjectivity: float) -> Tuple[str, float]:
        """Enhanced sentiment analysis with custom rules"""
        words = text.split()
        
        # Count positive and negative words
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        # Check for intensifiers
        has_intensifiers = any(word in self.intensifiers for word in words)
        
        # Check for negations
        negations = ['not', 'no', 'never', 'without', 'lack', 'missing', 'unable', 'cannot']
        negation_count = sum(1 for word in words if word in negations)
        
        # Check for question marks (often indicate neutral or negative sentiment)
        question_marks = text.count('?')
        
        # Check for exclamation marks (often indicate strong sentiment)
        exclamation_marks = text.count('!')
        
        # Calculate base confidence from TextBlob
        base_confidence = abs(polarity) * subjectivity
        
        # Apply custom rules
        if positive_count > negative_count:
            sentiment = 'positive'
            confidence = base_confidence + (positive_count * 0.1)
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = base_confidence + (negative_count * 0.1)
        else:
            sentiment = 'neutral'
            confidence = 0.5
        
        # Adjust for intensifiers
        if has_intensifiers and confidence > 0.3:
            confidence = min(confidence * 1.2, 1.0)
        
        # Adjust for negations (flip sentiment if negation with strong word)
        if negation_count > 0:
            if sentiment == 'positive' and confidence > 0.6:
                sentiment = 'negative'
                confidence *= 0.8
            elif sentiment == 'negative' and confidence > 0.6:
                sentiment = 'positive'
                confidence *= 0.8
        
        # Adjust for punctuation
        if exclamation_marks > 0 and confidence > 0.4:
            confidence = min(confidence * 1.1, 1.0)
        
        if question_marks > 1:  # Multiple questions often indicate frustration
            if sentiment == 'neutral':
                sentiment = 'negative'
                confidence = max(confidence, 0.6)
        
        # Ensure confidence is between 0 and 1
        confidence = max(0.0, min(1.0, confidence))
        
        return sentiment, confidence
    
    def analyze_email_sentiment(self, email_subject: str, email_body: str) -> Tuple[str, float]:
        """Analyze sentiment of email combining subject and body"""
        # Combine subject and body, giving more weight to subject
        subject_sentiment, subject_confidence = self.analyze_sentiment(email_subject or '')
        body_sentiment, body_confidence = self.analyze_sentiment(email_body or '')
        
        # Weight subject more heavily (30% subject, 70% body)
        if subject_sentiment == body_sentiment:
            # Same sentiment, average confidence with subject weighted higher
            combined_confidence = (subject_confidence * 0.3) + (body_confidence * 0.7)
            return subject_sentiment, combined_confidence
        else:
            # Different sentiments, use the one with higher confidence
            if subject_confidence > body_confidence * 1.5:  # Subject much stronger
                return subject_sentiment, subject_confidence * 0.8
            else:
                return body_sentiment, body_confidence
    
    def get_sentiment_description(self, sentiment: str, confidence: float) -> str:
        """Get human-readable description of sentiment"""
        confidence_level = "high" if confidence > 0.7 else "medium" if confidence > 0.4 else "low"
        
        descriptions = {
            'positive': {
                'high': 'Very positive sentiment detected',
                'medium': 'Generally positive sentiment',
                'low': 'Slightly positive sentiment'
            },
            'negative': {
                'high': 'Very negative sentiment detected',
                'medium': 'Generally negative sentiment',
                'low': 'Slightly negative sentiment'
            },
            'neutral': {
                'high': 'Neutral sentiment with high confidence',
                'medium': 'Neutral sentiment',
                'low': 'Unclear sentiment'
            }
        }
        
        return descriptions.get(sentiment, {}).get(confidence_level, 'Sentiment analysis unavailable')

# Global sentiment analyzer instance
sentiment_analyzer = SentimentAnalyzer()

def analyze_sentiment(text: str) -> Tuple[str, float]:
    """Convenience function for sentiment analysis"""
    return sentiment_analyzer.analyze_sentiment(text)

def analyze_email_sentiment(subject: str, body: str) -> Tuple[str, float]:
    """Convenience function for email sentiment analysis"""
    return sentiment_analyzer.analyze_email_sentiment(subject, body)