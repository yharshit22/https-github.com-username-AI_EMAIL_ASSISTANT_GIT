import logging
import re
from typing import Tuple
from datetime import datetime
from app.models import Email

logger = logging.getLogger(__name__)

class PriorityClassifier:
    """Email priority classification using rules and ML-like approach"""
    
    def __init__(self):
        # High priority keywords
        self.high_priority_keywords = {
            'urgent', 'asap', 'immediately', 'emergency', 'critical', 'urgently',
            'breaking', 'deadline', 'expired', 'overdue', 'complaint', 'escalate',
            'legal', 'lawsuit', 'violation', 'breach', 'security', 'fraud',
            'unauthorized', 'suspicious', 'alert', 'warning', 'danger',
            'server down', 'system down', 'outage', 'crash', 'failure',
            'ceo', 'cfo', 'director', 'manager', 'president', 'vice president'
        }
        
        # Medium priority keywords
        self.medium_priority_keywords = {
            'meeting', 'appointment', 'schedule', 'reschedule', 'calendar',
            'reminder', 'follow up', 'update', 'status', 'progress',
            'report', 'review', 'approval', 'approve', 'request',
            'question', 'inquiry', 'information', 'details', 'clarification',
            'support', 'help', 'assistance', 'troubleshoot', 'issue'
        }
        
        # Low priority keywords (newsletters, promotions, etc.)
        self.low_priority_keywords = {
            'newsletter', 'unsubscribe', 'subscribe', 'promotion', 'sale',
            'discount', 'offer', 'deal', 'coupon', 'advertisement', 'ad',
            'marketing', 'campaign', 'notification', 'update available',
            'social', 'linkedin', 'facebook', 'twitter', 'instagram',
            'news', 'blog', 'article', 'digest', 'weekly', 'monthly',
            'automatic', 'automated', 'noreply', 'no-reply', 'do-not-reply'
        }
        
        # Sender patterns
        self.newsletter_senders = {
            'newsletter', 'noreply', 'no-reply', 'donotreply', 'automated',
            'notification', 'alert', 'updates', 'info', 'support'
        }
        
        # High priority senders (internal, important contacts)
        self.high_priority_senders = {
            'ceo', 'cfo', 'cto', 'president', 'director', 'manager',
            'admin', 'administrator', 'boss', 'supervisor'
        }
    
    def classify_priority(self, email: Email) -> Tuple[str, float]:
        """
        Classify email priority
        
        Args:
            email: Email object to classify
            
        Returns:
            Tuple of (priority_level, confidence_score)
        """
        try:
            score = 0.0
            reasons = []
            
            # Analyze subject
            subject_lower = email.subject.lower() if email.subject else ''
            subject_words = set(subject_lower.split())
            
            # Analyze body
            body_lower = email.body.lower() if email.body else ''
            body_words = set(body_lower.split())
            
            # Analyze sender
            sender_lower = email.from_address.lower() if email.from_address else ''
            sender_username = sender_lower.split('@')[0] if '@' in sender_lower else sender_lower
            
            # High priority indicators
            high_priority_score = self._calculate_keyword_score(
                subject_words.union(body_words), 
                self.high_priority_keywords
            )
            
            if high_priority_score > 0:
                score += high_priority_score * 3.0
                reasons.append(f"High priority keywords found")
            
            # Medium priority indicators
            medium_priority_score = self._calculate_keyword_score(
                subject_words.union(body_words), 
                self.medium_priority_keywords
            )
            
            if medium_priority_score > 0:
                score += medium_priority_score * 1.5
                reasons.append(f"Medium priority keywords found")
            
            # Low priority indicators
            low_priority_score = self._calculate_keyword_score(
                subject_words.union(body_words), 
                self.low_priority_keywords
            )
            
            if low_priority_score > 0:
                score -= low_priority_score * 2.0
                reasons.append(f"Low priority keywords found")
            
            # Sender analysis
            sender_priority = self._analyze_sender(sender_username)
            score += sender_priority
            
            if sender_priority > 0.5:
                reasons.append("High priority sender")
            elif sender_priority < -0.5:
                reasons.append("Low priority sender")
            
            # Sentiment impact
            if email.sentiment == 'negative':
                score += 1.0  # Negative sentiment often indicates higher priority
                reasons.append("Negative sentiment detected")
            elif email.sentiment == 'positive':
                score -= 0.5  # Positive sentiment might indicate lower priority
            
            # Length analysis
            body_length = len(email.body) if email.body else 0
            if body_length < 100:  # Very short emails might be urgent
                score += 0.5
                reasons.append("Very short email")
            elif body_length > 2000:  # Very long emails might be detailed reports (lower priority)
                score -= 0.3
            
            # Question marks indicate need for response
            question_count = email.body.count('?') if email.body else 0
            if question_count > 2:
                score += 0.8
                reasons.append("Multiple questions detected")
            elif question_count > 0:
                score += 0.3
            
            # Exclamation marks indicate urgency
            exclamation_count = email.body.count('!') if email.body else 0
            if exclamation_count > 2:
                score += 1.0
                reasons.append("Multiple exclamations detected")
            
            # All caps words indicate urgency
            caps_words = re.findall(r'\b[A-Z]{2,}\b', email.body) if email.body else []
            if len(caps_words) > 2:
                score += 0.8
                reasons.append("Multiple all-caps words")
            
            # Time sensitivity
            time_keywords = ['today', 'tomorrow', 'this week', 'by', 'deadline', 'due']
            time_matches = sum(1 for keyword in time_keywords if keyword in body_lower)
            if time_matches > 1:
                score += 1.0
                reasons.append("Time-sensitive content")
            
            # Determine final priority
            if score >= 2.0:
                priority = 'high'
                confidence = min(0.9, 0.6 + (score * 0.1))
            elif score >= 0.5:
                priority = 'medium'
                confidence = min(0.8, 0.4 + (score * 0.1))
            else:
                priority = 'low'
                confidence = min(0.7, 0.3 + (abs(score) * 0.1))
            
            logger.info(f"Priority classification for '{email.subject[:50]}...': {priority} ({confidence:.2f}) - Score: {score:.2f}")
            if reasons:
                logger.info(f"Reasons: {'; '.join(reasons)}")
            
            return priority, confidence
            
        except Exception as e:
            logger.error(f"Error in priority classification: {str(e)}")
            return 'medium', 0.5
    
    def _calculate_keyword_score(self, words: set, keywords: set) -> float:
        """Calculate keyword matching score"""
        matches = words.intersection(keywords)
        return len(matches) / len(keywords) if keywords else 0.0
    
    def _analyze_sender(self, sender_username: str) -> float:
        """Analyze sender for priority indicators"""
        sender_parts = sender_username.split('.') + sender_username.split('_')
        
        # Check for newsletter patterns
        for newsletter_pattern in self.newsletter_senders:
            if newsletter_pattern in sender_username:
                return -1.0
        
        # Check for high priority patterns
        for high_priority_pattern in self.high_priority_senders:
            if high_priority_pattern in sender_parts:
                return 1.5
        
        # Check for personal vs corporate
        if len(sender_parts) == 2 and all(len(part) > 2 for part in sender_parts):
            # Likely personal name format (john.smith, jane_doe)
            return 0.5
        
        return 0.0
    
    def get_priority_description(self, priority: str, confidence: float) -> str:
        """Get human-readable description of priority"""
        confidence_level = "high" if confidence > 0.7 else "medium" if confidence > 0.4 else "low"
        
        descriptions = {
            'high': {
                'high': 'High priority email requiring immediate attention',
                'medium': 'Likely high priority email',
                'low': 'Possibly high priority email'
            },
            'medium': {
                'high': 'Medium priority email requiring timely response',
                'medium': 'Standard priority email',
                'low': 'Lower medium priority email'
            },
            'low': {
                'high': 'Low priority email (newsletter, promotion, etc.)',
                'medium': 'Likely low priority email',
                'low': 'Possibly low priority email'
            }
        }
        
        return descriptions.get(priority, {}).get(confidence_level, 'Priority classification unavailable')

# Global priority classifier instance
priority_classifier = PriorityClassifier()

def classify_priority(email: Email) -> Tuple[str, float]:
    """Convenience function for priority classification"""
    return priority_classifier.classify_priority(email)