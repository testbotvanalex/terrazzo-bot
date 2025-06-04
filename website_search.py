import requests
from bs4 import BeautifulSoup
import openai
import numpy as np

PAGES = [
    "https://terrazzowebshop.nl/kleurstalen/",
    "https://terrazzowebshop.nl/verzending/",
    "https://terrazzowebshop.nl/faq/",
    "https://terrazzowebshop.nl/contact/"
]

def load_website_data():
    texts = []
    for url in PAGES:
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            content = soup.get_text(separator=' ', strip=True)
            texts.append((url, content))
        except Exception as e:
            print(f"Fout bij ophalen {url}: {e}")

    only_texts = [text for _, text in texts]
    embeddings = get_embeddings(only_texts)
    return texts, embeddings

def get_embeddings(texts):
    client = openai.OpenAI()  # новый способ
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [d.embedding for d in response.data]

def find_best_match(query, texts, embeddings, threshold=0.82):
    query_embedding = get_embeddings([query])[0]

    def cosine_similarity(a, b):
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    sims = [cosine_similarity(query_embedding, emb) for emb in embeddings]
    best_idx = int(np.argmax(sims))
    if sims[best_idx] >= threshold:
        url, text = texts[best_idx]
        return f"{text[:1000]}...\n\n🔗 Meer info: {url}"
    else:
        return None