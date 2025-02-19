import wikipedia
import re
from difflib import SequenceMatcher

# Define unwanted keywords
UNWANTED_KEYWORDS = [
    "emoji", "software", "video game", "song", "album", "character", "film",
    "television", "TV series", "manga", "anime", "fictional", "game"
]

def clean_query(query):
    """Clean the input query."""
    query = query.lower().strip()
    query = re.sub(r"\bwhat is\b|\bwho is\b|\bdefine\b|\bexplain\b", "", query)
    query = re.sub(r'[^\w\s]', '', query)
    return ' '.join(query.split())

def calculate_relevance(query, text):
    """Calculate relevance score between query and text."""
    return SequenceMatcher(None, query.lower(), text.lower()).ratio()

def get_wikipedia_summary(query):
    try:
        # Clean the query
        cleaned_query = clean_query(query)
        
        if not cleaned_query:
            return "Please ask a more specific question."

        # Search Wikipedia
        search_results = wikipedia.search(cleaned_query, results=5)
        if not search_results:
            return "I couldn't find anything related to that query."

        # Find best match
        best_match = None
        best_score = 0
        best_summary = ""

        for result in search_results:
            # Skip unwanted topics
            if any(word.lower() in result.lower() for word in UNWANTED_KEYWORDS):
                continue
                
            try:
                summary = wikipedia.summary(result, sentences=2)
                score = calculate_relevance(cleaned_query, summary)
                
                if score > best_score:
                    best_score = score
                    best_match = result
                    best_summary = summary
                    
            except (wikipedia.exceptions.DisambiguationError, 
                   wikipedia.exceptions.PageError):
                continue

        if not best_match:
            return "I found some results, but they don't seem relevant."

        # Format response
        confidence = "High" if best_score > 0.6 else "Medium" if best_score > 0.3 else "Low"
        return f"Topic: {best_match}\nConfidence: {confidence}\n\n{best_summary}"

    except wikipedia.exceptions.DisambiguationError as e:
        return f"Please be more specific. Did you mean:\n- " + "\n- ".join(e.options[:3])
    except wikipedia.exceptions.PageError:
        return "I couldn't find a specific article about that."
    except Exception as e:
        return f"An error occurred: {str(e)}"

def chatbot():
    print("Wikipedia Chatbot")
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
