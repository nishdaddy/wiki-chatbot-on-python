import wikipedia
import re
from difflib import SequenceMatcher

# Enhanced unwanted keywords for better filtering
UNWANTED_KEYWORDS = [
    "emoji", "software", "video game", "song", "album", "character", "film",
    "television", "TV series", "manga", "anime", "fictional", "game",
    "painting", "artwork", "novel", "book", "movie"
]

def clean_query(query):
    """Clean and enhance the input query."""
    original = query.lower().strip()
    
    # For "what is" questions, try to get the main topic
    what_is_match = re.match(r'what\s+is\s+(?:a|an|the)?\s*(.+)', original)
    if what_is_match:
        return what_is_match.group(1).strip()
    
    # For other questions, remove question words and articles
    query = re.sub(r"\b(what|who|where|when|how|is|are|was|were|a|an|the)\b", "", original)
    query = re.sub(r'[^\w\s]', '', query)
    return ' '.join(query.split())

def is_specific_article(title, summary):
    """Check if the article is about a specific instance rather than a general topic."""
    specific_indicators = [
        'is a', 'was a', 'refers to',
        'born', 'died', 'located in',
        'written by', 'directed by', 'created by'
    ]
    
    # Check if the title is capitalized (proper noun)
    if title.istitle() and not title.isupper():
        first_sentence = summary.split('.')[0].lower()
        return any(indicator in first_sentence for indicator in specific_indicators)
    return False

def get_wikipedia_summary(query):
    try:
        # Clean the query
        original_query = query.lower()
        cleaned_query = clean_query(query)
        
        if not cleaned_query:
            return "Please ask a more specific question."

        # First try exact search
        try:
            direct_summary = wikipedia.summary(cleaned_query, sentences=2)
            if not is_specific_article(cleaned_query, direct_summary):
                return f"Topic: {cleaned_query.title()}\nConfidence: High\n\n{direct_summary}"
        except:
            pass

        # If exact search fails, try search with suggestions
        search_results = wikipedia.search(cleaned_query, results=8)
        if not search_results:
            return "I couldn't find anything related to that query."

        # Score and filter results
        scored_results = []
        for result in search_results:
            # Skip results with unwanted keywords
            if any(word.lower() in result.lower() for word in UNWANTED_KEYWORDS):
                continue
                
            try:
                summary = wikipedia.summary(result, sentences=2)
                
                # Skip if it's a specific article when we want a general definition
                if 'what is' in original_query.lower() and is_specific_article(result, summary):
                    continue
                
                # Calculate relevance score
                score = calculate_relevance(cleaned_query, summary)
                
                # Boost score for results that seem like definitions
                if f"{cleaned_query} is" in summary.lower():
                    score += 0.3
                if not is_specific_article(result, summary):
                    score += 0.2
                    
                scored_results.append((result, score, summary))
                
            except (wikipedia.exceptions.DisambiguationError, 
                   wikipedia.exceptions.PageError):
                continue

        if not scored_results:
            return "I found some results, but they don't seem relevant to your question."

        # Sort by relevance score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        best_match = scored_results[0]

        # Format response
        confidence = "High" if best_match[1] > 0.6 else "Medium" if best_match[1] > 0.3 else "Low"
        response = f"Topic: {best_match[0]}\nConfidence: {confidence}\n\n{best_match[2]}"
        
        # Add suggestion if we have other good matches
        if len(scored_results) > 1 and confidence != "High":
            alternatives = [result[0] for result in scored_results[1:3]]
            response += f"\n\nRelated topics: {', '.join(alternatives)}"
            
        return response

    except wikipedia.exceptions.DisambiguationError as e:
        return f"Please be more specific. Did you mean:\n- " + "\n- ".join(e.options[:3])
    except wikipedia.exceptions.PageError:
        return "I couldn't find a specific article about that."
    except Exception as e:
        return f"An error occurred: {str(e)}"

def calculate_relevance(query, text):
    """Calculate relevance score between query and text."""
    # Base similarity score
    base_score = SequenceMatcher(None, query.lower(), text.lower()).ratio()
    
    # Boost score if query appears in the first sentence
    first_sentence = text.split('.')[0].lower()
    if query.lower() in first_sentence:
        base_score += 0.2
        
    return base_score

def chatbot():
    print("Enhanced Wikipedia ")
    print("Ask me anything! Type 'exit' to quit.")
    
    while True:
        query = input("\nYou: ").strip()
        if query.lower() in ['exit', 'quit', 'bye']:
            print("Goodbye!")
            break
        if not query:
            print("Please type a question!")
            continue
            
        response = get_wikipedia_summary(query)
        print("\nBot:", response)

if __name__ == "__main__":
    chatbot()
