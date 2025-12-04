import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

class MedicalRAGSystem:
    def __init__(self):
        print("🚀 Loading Medical RAG System...")
        
        # Load documents
        with open('documents.pkl', 'rb') as f:
            self.documents = pickle.load(f)
        
        # Load embeddings
        self.embeddings = np.load('embeddings.npy')
        
        # Load FAISS index
        self.index = faiss.read_index('faiss_index.faiss')
        
        # Initialize BM25
        tokenized_docs = [doc.split() for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_docs)
        
        # Load embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        print(f"✅ System loaded: {len(self.documents)} documents, {self.embeddings.shape[1]}D embeddings")
    
    def retrieve_with_scores(self, query, top_k=5):
        """Retrieve documents with similarity scores"""
        q_emb = self.model.encode([query]).astype('float32')
        distances, idx = self.index.search(q_emb, top_k)
        
        results = []
        for i, (doc_idx, distance) in enumerate(zip(idx[0], distances[0])):
            if doc_idx != -1 and doc_idx < len(self.documents):
                similarity = 1 / (1 + distance)
                results.append({
                    'rank': i + 1,
                    'document': self.documents[doc_idx],
                    'similarity': round(float(similarity), 4)
                })
        
        return results

# Global instance
rag_system = MedicalRAGSystem()
