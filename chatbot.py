import wikipedia
import re
from difflib import SequenceMatcher
from typing import Tuple, Optional, List, Dict
import datetime

class LanguageProcessor:
    """Handles language processing and validation."""
    
    def __init__(self):
        # Common spelling mistakes and corrections
        self.spelling_corrections = {
            'wat': 'what', 'wut': 'what', 'wht': 'what',
            'wen': 'when', 'wer': 'where', 'y': 'why',
            'hw': 'how', 'r': 'are', 'u': 'you',
            'tel': 'tell', 'abt': 'about', 'dis': 'this'
        }
        
        # Measurement-related keywords
        self.measurement_keywords = {
            'height', 'width', 'length', 'depth', 'distance',
            'weight', 'mass', 'volume', 'area', 'speed',
            'temperature', 'pressure', 'size', 'diameter'
        }
        
        # Time-related keywords
        self.time_keywords = {
            'when', 'date', 'year', 'century', 'period',
            'age', 'era', 'dynasty', 'born', 'died',
            'established', 'founded', 'discovered', 'invented'
        }
    
    def correct_spelling(self, text: str) -> str:
        """Corrects common spelling mistakes."""
        words = text.lower().split()
        corrected_words = [self.spelling_corrections.get(word, word) for word in words]
        return ' '.join(corrected_words)
    
    def is_measurement_query(self, text: str) -> bool:
        """Checks if query is asking for measurements."""
        return any(keyword in text.lower() for keyword in self.measurement_keywords)
    
    def is_time_query(self, text: str) -> bool:
        """Checks if query is asking for dates/time information."""
        return any(keyword in text.lower() for keyword in self.time_keywords)
    
    def extract_measurement_units(self, text: str) -> List[str]:
        """Extracts measurement units from text."""
        unit_pattern = r'\b(?:meters?|km|miles?|feet|inches|kg|pounds?|tons?|celsius|fahrenheit|square\s+\w+)\b'
        return re.findall(unit_pattern, text.lower())

class QueryAnalyzer:
    """Analyzes and processes search queries."""
    
    def __init__(self):
        self.language_processor = LanguageProcessor()
        
        # Categories for different types of queries
        self.query_categories = {
            'definition': r'\b(what\s+is|define|meaning\s+of)\b',
            'person': r'\b(who\s+(?:is|was)|person)\b',
            'location': r'\b(where\s+(?:is|was)|location|place)\b',
            'time': r'\b(when|date|year|time)\b',
            'reason': r'\b(why|reason|cause)\b',
            'process': r'\b(how|process|method)\b'
        }
    
    def analyze_query(self, query: str) -> Dict[str, any]:
        """Analyzes the query and returns relevant information."""
        # Correct spelling
        corrected_query = self.language_processor.correct_spelling(query)
        
        # Determine query type
        query_type = self._determine_query_type(corrected_query)
        
        # Check for special cases
        is_measurement = self.language_processor.is_measurement_query(corrected_query)
        is_time = self.language_processor.is_time_query(corrected_query)
        
        return {
            'original_query': query,
            'corrected_query': corrected_query,
            'query_type': query_type,
            'is_measurement': is_measurement,
            'is_time': is_time,
            'needs_verification': self._needs_verification(corrected_query)
        }
    
    def _determine_query_type(self, query: str) -> str:
        """Determines the type of query being asked."""
        for category, pattern in self.query_categories.items():
            if re.search(pattern, query.lower()):
                return category
        return 'general'
    
    def _needs_verification(self, query: str) -> bool:
        """Determines if the query needs additional verification."""
        verification_keywords = {'exact', 'precise', 'accurate', 'specific', 'official'}
        return any(keyword in query.lower() for keyword in verification_keywords)

class WikipediaResearcher:
    """Handles Wikipedia searches with enhanced accuracy."""
    
    def __init__(self):
        self.language_processor = LanguageProcessor()
    
    def search(self, query_info: Dict[str, any]) -> Dict[str, any]:
        """Performs an enhanced Wikipedia search."""
        try:
            # Get search results
            search_results = wikipedia.search(query_info['corrected_query'], results=8)
            if not search_results:
                return self._format_error("No results found")
            
            # Process results based on query type
            if query_info['is_measurement']:
                return self._handle_measurement_query(search_results, query_info)
            elif query_info['is_time']:
                return self._handle_time_query(search_results, query_info)
            else:
                return self._handle_general_query(search_results, query_info)
                
        except wikipedia.exceptions.DisambiguationError as e:
            return self._handle_disambiguation(e.options)
        except Exception as e:
            return self._format_error(str(e))
    
    def _handle_measurement_query(self, results: List[str], query_info: Dict[str, any]) -> Dict[str, any]:
        """Handles queries about measurements."""
        for result in results:
            try:
                page = wikipedia.page(result)
                content = page.content[:2000]  # Look in first 2000 chars
                
                # Extract measurement information
                measurements = self._extract_measurements(content)
                if measurements:
                    return {
                        'title': page.title,
                        'summary': self._format_measurement_response(measurements),
                        'confidence': 'High' if len(measurements) > 1 else 'Medium',
                        'source_url': page.url
                    }
            except:
                continue
        return self._handle_general_query(results, query_info)
    
    def _handle_time_query(self, results: List[str], query_info: Dict[str, any]) -> Dict[str, any]:
        """Handles queries about dates and times."""
        for result in results:
            try:
                page = wikipedia.page(result)
                content = page.content[:2000]
                
                # Extract date information
                dates = self._extract_dates(content)
                if dates:
                    return {
                        'title': page.title,
                        'summary': self._format_date_response(dates),
                        'confidence': 'High' if len(dates) > 1 else 'Medium',
                        'source_url': page.url
                    }
            except:
                continue
        return self._handle_general_query(results, query_info)
    
    def _handle_general_query(self, results: List[str], query_info: Dict[str, any]) -> Dict[str, any]:
        """Handles general queries with enhanced validation."""
        best_result = None
        best_score = 0
        
        for result in results:
            try:
                page = wikipedia.page(result)
                summary = wikipedia.summary(result, sentences=3)
                
                # Calculate relevance score
                score = self._calculate_relevance(query_info['corrected_query'], page.title, summary)
                
                # Verify information if needed
                if query_info['needs_verification']:
                    score = self._verify_information(score, page)
                
                if score > best_score:
                    best_score = score
                    best_result = {
                        'title': page.title,
                        'summary': summary,
                        'confidence': self._get_confidence_level(score),
                        'source_url': page.url
                    }
            except:
                continue
        
        return best_result if best_result else self._format_error("Could not find relevant information")
    
    def _extract_measurements(self, text: str) -> List[str]:
        """Extracts measurement information from text."""
        measurement_pattern = r'\b\d+(?:\.\d+)?\s*(?:meters?|km|miles?|feet|inches|kg|pounds?|tons?|celsius|fahrenheit|square\s+\w+)\b'
        return re.findall(measurement_pattern, text, re.IGNORECASE)
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extracts date information from text."""
        date_pattern = r'\b(?:\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)|(?:19|20)\d{2})\b'
        return re.findall(date_pattern, text)
    
    def _calculate_relevance(self, query: str, title: str, summary: str) -> float:
        """Calculates relevance score with enhanced accuracy."""
        # Base similarity scores
        title_score = SequenceMatcher(None, query.lower(), title.lower()).ratio()
        summary_score = SequenceMatcher(None, query.lower(), summary.lower()).ratio()
        
        # Weight factors
        score = (title_score * 0.4) + (summary_score * 0.6)
        
        # Boost score for exact matches
        if query.lower() in title.lower() or query.lower() in summary.lower():
            score += 0.2
            
        return min(score, 1.0)
    
    def _verify_information(self, base_score: float, page) -> float:
        """Additional verification for accuracy."""
        if page.references:
            base_score += 0.1
        if len(page.content) > 1000:  # Substantial article
            base_score += 0.1
        return min(base_score, 1.0)
    
    def _get_confidence_level(self, score: float) -> str:
        """Determines confidence level based on score."""
        if score > 0.8:
            return 'Very High'
        elif score > 0.6:
            return 'High'
        elif score > 0.4:
            return 'Medium'
        return 'Low'
    
    def _format_measurement_response(self, measurements: List[str]) -> str:
        """Formats measurement information into readable response."""
        if not measurements:
            return "No specific measurements found."
        return "Found measurements: " + ", ".join(measurements)
    
    def _format_date_response(self, dates: List[str]) -> str:
        """Formats date information into readable response."""
        if not dates:
            return "No specific dates found."
        return "Found dates: " + ", ".join(dates)
    
    def _format_error(self, message: str) -> Dict[str, any]:
        """Formats error response."""
        return {
            'title': 'Error',
            'summary': message,
            'confidence': 'None',
            'source_url': None
        }

class WikiBot:
    """Main chatbot class with enhanced accuracy and response handling."""
    
    def __init__(self):
        self.query_analyzer = QueryAnalyzer()
        self.researcher = WikipediaResearcher()
    
    def get_response(self, user_input: str) -> str:
        """Processes user input and returns enhanced response."""
        # Analyze query
        query_info = self.query_analyzer.analyze_query(user_input)
        
        # Get Wikipedia results
        result = self.researcher.search(query_info)
        
        # Format response
        if result['title'] == 'Error':
            return result['summary']
            
        response = f"Topic: {result['title']}\n"
        response += f"Confidence: {result['confidence']}\n\n"
        response += result['summary']
        
        if result['source_url']:
            response += f"\n\nSource: {result['source_url']}"
            
        return response

def main():
    bot = WikiBot()
    
    print("Enhanced Wikipedia Chatbot")
    print("Ask me anything! Type 'exit' to quit.")
    print("\nTips:")
    print("- Ask specific questions for better results")
    print("- For measurements, include terms like height, weight, distance")
    print("- For dates, include terms like when, year, date")
    print("- Type 'exit' to end the conversation")
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Goodbye!")
            break
            
        if not user_input:
            print("Please type a question!")
            continue
        
        response = bot.get_response(user_input)
        print("\nBot:", response)

if __name__ == "__main__":
    main()
