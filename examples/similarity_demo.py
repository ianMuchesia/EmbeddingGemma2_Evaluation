from sentence_transformers import SentenceTransformer

model = SentenceTransformer("google/embeddinggemma-2")

sentences = [
    "I deposited money at the bank",
    "I sat on the river bank",
    "The bank approved my loan",
    "We had a picnic by the river",
]
vecs = model.encode(sentences)
print(vecs.shape)                       # (4, 768): one vector per sentence
print(model.similarity(vecs, vecs))     # 4x4 table of similarities
