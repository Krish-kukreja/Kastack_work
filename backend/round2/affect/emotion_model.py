import time
from transformers import pipeline

_model = None
_load_time = None

def get_model():
    global _model, _load_time
    if _model is None:
        t0 = time.perf_counter()
        # top_k=None returns probabilities for all classes
        _model = pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion", top_k=None, framework="pt")
        _load_time = time.perf_counter() - t0
    return _model

def score_model(text):
    model = get_model()
    results = model(text)[0]
    return {res['label']: float(res['score']) for res in results}
