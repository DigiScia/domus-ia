# outils/outils_droit.py
import chromadb
from chromadb.utils import embedding_functions
from langchain_openai import ChatOpenAI # CHANGEMENT ICI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 

class DroitImmoRAG:
    """Classe de base pour gérer la base de connaissances et les requêtes RAG."""
    
    def __init__(self, collection_name="droit_immobilier_docs", docs_folder="docs_droit"):
        self.client = chromadb.Client()
        # On garde les embeddings par défaut de Chroma pour éviter de consommer trop de crédits OpenAI pour l'indexation locale
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction() 
        
        try:
            self.collection = self.client.get_collection(
                name=collection_name, 
                embedding_function=self.embedding_function
            )
            print(f"✅ Collection ChromaDB '{collection_name}' chargée.")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            print(f"✅ Collection ChromaDB '{collection_name}' créée.")
            self.load_documents_from_folder(docs_folder)
        
        # CHANGEMENT ICI : Modèle OpenAI pour la réponse
        self.llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, temperature=0.1)
        self.docs_folder = docs_folder
        
    def _read_pdf(self, pdf_path):
        try:
            reader = PdfReader(pdf_path)
            text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
            return "\n\n".join(text)
        except Exception:
            return None
    
    def _split_text(self, text, max_length=1000):
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > max_length:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks if chunks else [text]
        
    def load_documents_from_folder(self, folder_path):
        """Charge et indexe les documents texte/PDF d'un dossier."""
        documents = []
        ids = []
        metadatas = []
        
        folder = Path(folder_path)
        if not folder.exists():
            print(f"⚠️ Création du dossier docs/droit... Créez-y vos PDF et TXT.")
            folder.mkdir(exist_ok=True)
            return

        print(f"🔍 Indexation des documents de droit dans {folder_path}...")
        
        text_extensions = ['.txt', '.md', '.json', '.py', '.html', '.csv']
        
        for file_path in folder.rglob('*'):
            if not file_path.is_file(): continue
            try:
                content = None
                if file_path.suffix.lower() == '.pdf':
                    if not PDF_SUPPORT: continue
                    content = self._read_pdf(file_path)
                elif file_path.suffix in text_extensions:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                if content and content.strip():
                    chunks = self._split_text(content, max_length=1000)
                    for i, chunk in enumerate(chunks):
                        documents.append(chunk)
                        ids.append(f"{file_path.stem}_chunk_{i}")
                        metadatas.append({"source": str(file_path), "filename": file_path.name})
            except Exception as e:
                print(f"   ❌ Erreur d'indexation {file_path.name}: {e}")

        if documents:
            self.collection.add(documents=documents, ids=ids, metadatas=metadatas)
            print(f"✅ SUCCÈS: {len(documents)} chunks indexés.")
        else:
            print(f"⚠️ Aucun document valide trouvé.")
            
    def retrieve(self, query, n_results=3):
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        # Gestion du cas où la collection est vide
        if not results['documents']:
            return [], []
        return results['documents'][0], results.get('metadatas', [[]])[0]
    
    def generate(self, query, context):
        """Génère une réponse avec GPT-4o."""
        prompt = f"""En tant qu'expert en droit immobilier basé sur le contexte légal suivant, réponds à la question de manière précise et concise. NE RÉPONDS QU'AVEC LE CONTEXTE FOURNI.

Contexte:
{context}

Question: {query}

Réponse:"""
        
        try:
            # CHANGEMENT ICI : Appel LangChain OpenAI
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            return f"❌ Erreur lors de la génération: {e}"

    def query_rag(self, question: str) -> str:
        relevant_docs, metadatas = self.retrieve(question, n_results=4)
        if not relevant_docs:
            return "Je n'ai pas trouvé d'information spécifique dans mes documents juridiques."
            
        context = "\n\n".join(relevant_docs)
        answer = self.generate(question, context)
        
        sources = " | ".join(set([m.get('filename', 'Source Inconnue') for m in metadatas]))
        
        return f"Réponse Juridique: {answer}\n\n[Sources: {sources}]"

try:
    RAG_ADVISOR = DroitImmoRAG(docs_folder="docs_droit")
except Exception as e:
    print(f"Erreur fatale d'initialisation du RAG: {e}")
    RAG_ADVISOR = None

@tool
def query_droit_immobilier(question: str) -> str:
    """
    Utilisez cet outil pour répondre à des questions précises sur le droit immobilier
    (contrats, taxes, procédures, etc.) en utilisant la base de documents RAG.
    """
    if not RAG_ADVISOR:
        return "Le système RAG n'a pas pu être initialisé."
        
    return RAG_ADVISOR.query_rag(question)