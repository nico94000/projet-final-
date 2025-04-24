from flask import Flask, request, jsonify
from flask_cors import CORS
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
import string

# Téléchargement des ressources NLTK
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('vader_lexicon')
nltk.download('punkt_tab')

# Initialisation
app = Flask(__name__)
CORS(app)

sia = SentimentIntensityAnalyzer()
stop_words = set(stopwords.words('french'))
stop_words.update(['intelligence', 'artificielle', 'lia', 'ia', 'intelligenceartificielle'])

def calculate_engagement_score(text):
    longueur = len(text)
    nb_emojis = sum(1 for c in text if c in "😀😂🔥💡🚀✨🎯🤖🧠")
    nb_mots = len(word_tokenize(text))
    return min(100, longueur / 10 + nb_emojis * 5 + nb_mots)

def analyze_sentiment(text):
    return sia.polarity_scores(text)

def extract_keywords(text):
    words = word_tokenize(text.lower())
    filtered = [w for w in words if w.isalnum() and w not in stop_words]
    freq = Counter(filtered)
    return freq.most_common(5)

def generate_suggestions(text, score):
    suggestions = []
    if len(text) > 1000:
        suggestions.append("Post trop long, raccourcissez-le.")
    if "#" not in text:
        suggestions.append("Ajoutez des hashtags.")
    if "?" not in text:
        suggestions.append("Ajoutez une question.")
    if not any(e in text for e in ["😀", "🚀", "✨", "🔥", "🤖", "🧠"]):
        suggestions.append("Ajoutez des emojis pertinents.")
    if score < 40:
        suggestions.append("Score bas. Revoir ton style ou la structure.")
    if score > 85:
        suggestions.append("Excellent post !")
    return suggestions

@app.route('/analyser', methods=['POST'])
def analyser_post():
    data = request.get_json()
    texte = data.get('texte', '')
    score = calculate_engagement_score(texte)
    sentiment = analyze_sentiment(texte)
    keywords = extract_keywords(texte)
    suggestions = generate_suggestions(texte, score)
    return jsonify({
        "score": score,
        "sentiment": sentiment,
        "keywords": keywords,
        "suggestions": suggestions
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)

