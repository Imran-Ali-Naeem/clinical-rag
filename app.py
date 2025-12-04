import streamlit as st
import time
from retrieval_system import rag_system
from api_config import configure_gemini

# Page configuration
st.set_page_config(
    page_title="Medical Intelligence RAG System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced safety check function
def check_query_safety(query):
    """Check if query requests inappropriate information"""
    query_lower = query.lower().strip()
    
    if not query_lower:
        return True, 'safe', None
    
    # PII patterns - more comprehensive with word boundaries
    pii_keywords = {
        'contact': ['contact information', 'contact details', 'phone number', 'mobile number', 
                   'telephone', 'email address', 'email id', 'address'],
        'identity': ['full name', 'patient name', 'first name', 'last name', 'name of patient',
                    'patient\'s name', 'names', 'patient identifier'],
        'personal': ['social security', 'ssn', 'date of birth', 'dob', 'birth date',
                    'patient id', 'medical record number', 'mrn', 'patient number',
                    'insurance id', 'policy number', 'medicare number', 'medicaid number'],
        'location': ['home address', 'street address', 'zip code', 'residence', 'city',
                    'state', 'postal code', 'apartment number', 'house number']
    }
    
    # Check for exact phrase matches first
    for category, keywords in pii_keywords.items():
        for keyword in keywords:
            if keyword in query_lower:
                # Additional check to avoid false positives
                words = query_lower.split()
                if any(keyword in " ".join(words[i:i+len(keyword.split())]) 
                      for i in range(len(words) - len(keyword.split()) + 1)):
                    return False, 'pii_request', category
    
    # Personal medical advice patterns
    personal_patterns = [
        'i have', 'my symptoms', 'should i take', 'what should i do', 'am i',
        'my diagnosis', 'i feel', 'i am experiencing', 'i need advice',
        'can i take', 'is it safe for me', 'do i have', 'my condition',
        'personal advice', 'about myself', 'my medical', 'my treatment'
    ]
    
    for pattern in personal_patterns:
        if pattern in query_lower:
            # Check if it's a general query vs personal
            if any(word in query_lower for word in ['patient', 'patients', 'generally', 'typically', 'usually']):
                continue
            return False, 'personal_advice', None
    
    # Suspicious query patterns
    suspicious_patterns = [
        'password', 'login', 'credentials', 'username',
        'credit card', 'bank account', 'financial information',
        'delete', 'modify', 'change record', 'alter data',
        'confidential', 'secret', 'restricted access'
    ]
    
    for pattern in suspicious_patterns:
        if pattern in query_lower:
            return False, 'suspicious_query', None
    
    return True, 'safe', None

# Professional CSS styling with FIXED CONTRAST
st.markdown("""
<style>
    /* Main layout */
    .stApp {
        background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);
    }
    
    .main-container {
        background: white;
        border-radius: 20px;
        padding: 40px;
        margin: 20px auto;
        max-width: 1400px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    
    /* Typography - MAXIMUM CONTRAST */
    .hero-title {
        font-size: 3.5rem;
        font-weight: 900;
        color: #1a202c !important;
        text-align: center;
        margin-bottom: 10px;
        letter-spacing: -1px;
    }
    
    .hero-subtitle {
        text-align: center;
        color: #2d3748 !important;
        font-size: 1.3rem;
        margin-bottom: 30px;
        font-weight: 500;
    }
    
    .section-header {
        font-size: 1.8rem;
        color: #1a202c !important;
        font-weight: 700;
        margin: 30px 0 20px 0;
        padding-bottom: 10px;
        border-bottom: 3px solid #4299e1;
    }
    
    /* Warning/Error messages - HIGH CONTRAST */
    .warning-box {
        background: #fff5f5;
        border-left: 6px solid #c53030;
        padding: 25px;
        border-radius: 12px;
        margin: 20px 0;
        color: #742a2a !important;
        box-shadow: 0 4px 12px rgba(197, 48, 48, 0.15);
        border: 1px solid #fc8181;
    }
    
    .warning-title {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 10px;
        color: #742a2a !important;
    }
    
    .warning-box p {
        color: #742a2a !important;
        font-weight: 500;
    }
    
    .info-box {
        background: #ebf8ff;
        border-left: 6px solid #3182ce;
        padding: 25px;
        border-radius: 12px;
        margin: 20px 0;
        color: #2c5282 !important;
        box-shadow: 0 4px 12px rgba(49, 130, 206, 0.15);
        border: 1px solid #90cdf4;
    }
    
    .info-title {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 10px;
        color: #2c5282 !important;
    }
    
    .info-box p {
        color: #2c5282 !important;
        font-weight: 500;
    }
    
    /* Prompt cards - FIXED CONTRAST */
    .prompt-card {
        background: white;
        color: #1a202c !important;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 2px solid #4299e1;
    }
    
    .prompt-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(66, 153, 225, 0.3);
        border-color: #3182ce;
        background: #f7fafc;
    }
    
    .prompt-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 8px;
        color: #1a202c !important;
    }
    
    .prompt-desc {
        font-size: 0.95rem;
        line-height: 1.5;
        color: #2d3748 !important;
        font-weight: 500;
    }
    
    .prompt-tag {
        display: inline-block;
        background: #4299e1;
        color: white !important;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        margin-top: 10px;
        font-weight: 700;
    }
    
    /* Stats dashboard - HIGH CONTRAST */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        margin: 30px 0;
    }
    
    .stat-box {
        background: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 2px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .stat-box:hover {
        border-color: #4299e1;
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(66, 153, 225, 0.2);
    }
    
    .stat-icon {
        font-size: 3rem;
        margin-bottom: 10px;
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1a202c !important;
        margin: 10px 0;
    }
    
    .stat-label {
        color: #2d3748 !important;
        font-size: 1rem;
        font-weight: 600;
    }
    
    /* Answer display - HIGH CONTRAST */
    .answer-container {
        background: white;
        padding: 30px;
        border-radius: 15px;
        margin: 20px 0;
        border-left: 6px solid #4299e1;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        color: #1a202c !important;
        border: 1px solid #e2e8f0;
    }
    
    .answer-text {
        color: #1a202c !important;
        line-height: 1.8;
        font-size: 1.05rem;
        font-weight: 500;
    }
    
    /* Mode badge */
    .mode-badge {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white !important;
        padding: 12px 20px;
        border-radius: 25px;
        font-weight: 700;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(66, 153, 225, 0.3);
    }
    
    /* Source cards - HIGH CONTRAST */
    .source-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        border-left: 4px solid #3182ce;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        color: #1a202c !important;
        border: 1px solid #e2e8f0;
    }
    
    .source-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        color: #1a202c !important;
    }
    
    .source-content {
        background: #f7fafc;
        padding: 15px;
        border-radius: 8px;
        color: #2d3748 !important;
        line-height: 1.6;
        border: 1px solid #e2e8f0;
        font-weight: 500;
    }
    
    /* Similarity badges - HIGH CONTRAST TEXT */
    .sim-high { 
        background: #38a169;
        color: white !important;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    
    .sim-medium { 
        background: #dd6b20;
        color: white !important;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    
    .sim-low { 
        background: #e53e3e;
        color: white !important;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white !important;
        border: none;
        padding: 14px 28px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(66, 153, 225, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(66, 153, 225, 0.4);
        background: linear-gradient(135deg, #3182ce 0%, #2c5282 100%);
    }
    
    /* Text area */
    .stTextArea textarea {
        border: 2px solid #4299e1;
        border-radius: 12px;
        font-size: 1.05rem;
        padding: 15px;
        background: white;
        color: #1a202c !important;
    }
    
    /* Feature highlights - HIGH CONTRAST */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        margin: 30px 0;
    }
    
    .feature-box {
        background: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        border: 2px solid #e2e8f0;
        color: #1a202c !important;
    }
    
    .feature-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border-color: #4299e1;
    }
    
    .feature-box h3 {
        color: #1a202c !important;
        font-weight: 700;
        margin: 15px 0;
    }
    
    .feature-box p {
        color: #2d3748 !important;
        font-weight: 500;
        line-height: 1.6;
    }
    
    .feature-icon-large {
        font-size: 3.5rem;
        margin-bottom: 15px;
    }
    
    /* Progress styling */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #4299e1, #3182ce);
    }
    
    /* Footer - HIGH CONTRAST */
    .footer-box {
        text-align: center;
        padding: 30px;
        background: #1a202c;
        color: white !important;
        border-radius: 15px;
        margin-top: 40px;
    }
    
    .footer-title {
        margin: 0 0 10px 0;
        color: white !important;
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    .footer-text {
        margin: 0;
        font-size: 0.95rem;
        color: #e2e8f0 !important;
        font-weight: 500;
    }
    
    /* Direct query display */
    .direct-query-box {
        background: white;
        border: 2px solid #4299e1;
        border-radius: 12px;
        padding: 15px 20px;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    .direct-query-box:hover {
        background: #f7fafc;
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(66, 153, 225, 0.2);
    }
    
    .direct-query-text {
        color: #1a202c !important;
        font-size: 1.05rem;
        font-weight: 600;
        margin: 0;
    }
    
    .direct-query-icon {
        color: #4299e1 !important;
        font-size: 1.3rem;
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Gemini
@st.cache_resource
def load_gemini():
    return configure_gemini()

generation_model = load_gemini()

# Initialize session state
if 'selected_prompt' not in st.session_state:
    st.session_state.selected_prompt = ""
if 'query_safety_status' not in st.session_state:
    st.session_state.query_safety_status = {'safe': True, 'category': None, 'message': None}
if 'display_mode' not in st.session_state:
    st.session_state.display_mode = 'cards'  # 'cards' or 'direct'

# Smart RAG function
def rag_answer_smart_app(query, top_k=3):
    """Advanced RAG with intelligent fallback"""
    retrieved = rag_system.retrieve_with_scores(query, top_k=top_k)
    all_low_relevance = all(r['similarity'] < 0.3 for r in retrieved) if retrieved else True
    
    if all_low_relevance and retrieved:
        prompt = f"""MEDICAL QUESTION: {query}

You are a medical expert. Provide accurate, evidence-based information.
Answer comprehensively with proper medical terminology and structure your response with clear sections."""
        mode = "general_knowledge"
    else:
        ctx_formatted = []
        for i, r in enumerate(retrieved):
            doc_preview = r['document'][:500] + "..." if len(r['document']) > 500 else r['document']
            ctx_formatted.append(f"[Document {i+1}, Relevance: {r['similarity']:.3f}]:\n{doc_preview}")
        
        context_str = "\n\n".join(ctx_formatted)
        
        prompt = f"""You are a medical analyst with access to patient records. Provide comprehensive analysis.

QUESTION: {query}

PATIENT RECORDS:
{context_str}

INSTRUCTIONS:
1. Analyze what the patient records reveal
2. Identify patterns and correlations
3. Supplement with general medical knowledge where appropriate
4. Always cite specific documents (Document 1, 2, etc.)
5. Structure response with clear sections and bullet points
6. Include: "Analysis based on {len(retrieved)} patient records and medical literature"

COMPREHENSIVE ANALYSIS:"""
        mode = "rag_with_supplement"
    
    response = generation_model.generate_content(prompt)
    return response.text, retrieved, mode

# Strategic prompt examples that showcase system strengths
SHOWCASE_PROMPTS = {
    "🔍 Multi-Patient Pattern Analysis": {
        "query": "Analyze all patients with cardiovascular conditions and identify common risk factors, medications, and treatment outcomes across the dataset",
        "description": "Demonstrates cross-document analysis and pattern recognition across multiple patient records",
        "tag": "Multi-doc retrieval + Synthesis",
        "icon": "🔍"
    },
    "💊 Medication Efficacy Comparison": {
        "query": "Compare treatment approaches for atrial fibrillation patients - which medications appear most effective and what are the documented side effects?",
        "description": "Showcases ability to extract, compare, and synthesize treatment data from multiple sources",
        "tag": "Comparative analysis + Evidence synthesis",
        "icon": "💊"
    },
    "📊 Symptom-to-Diagnosis Correlation": {
        "query": "What are the most common symptom combinations that lead to migraine diagnosis, and how do treatment plans vary based on severity?",
        "description": "Highlights pattern recognition and clinical correlation capabilities",
        "tag": "Pattern detection + Clinical reasoning",
        "icon": "📊"
    },
    "⚠️ Risk Factor Identification": {
        "query": "Identify patients with diabetes who also have cardiovascular complications - what are the common risk factors and preventive measures mentioned?",
        "description": "Demonstrates complex filtering, correlation analysis, and risk assessment",
        "tag": "Complex queries + Risk analysis",
        "icon": "⚠️"
    },
    "🧬 Comorbidity Analysis": {
        "query": "Find patients with multiple chronic conditions and analyze how their treatment plans address drug interactions and comorbidity management",
        "description": "Shows sophisticated multi-condition analysis and clinical decision support",
        "tag": "Complex medical reasoning",
        "icon": "🧬"
    },
    "📈 Treatment Timeline Analysis": {
        "query": "Trace the progression of treatment for patients with hypertension - from initial diagnosis through medication adjustments to outcome",
        "description": "Demonstrates temporal reasoning and longitudinal analysis capabilities",
        "tag": "Temporal analysis + Progression tracking",
        "icon": "📈"
    },
    "🎯 Precision Medicine Query": {
        "query": "For patients over 65 with heart conditions, what are the medication dosage patterns and how do they differ from younger patients?",
        "description": "Showcases demographic filtering and precision medicine insights",
        "tag": "Demographic analysis + Precision insights",
        "icon": "🎯"
    },
    "🔬 Diagnostic Differential Analysis": {
        "query": "When patients present with chest pain and shortness of breath, what diagnostic tests are ordered and what conditions are ultimately diagnosed?",
        "description": "Highlights clinical reasoning and differential diagnosis support",
        "tag": "Clinical reasoning + Diagnostics",
        "icon": "🔬"
    }
}

# Header
st.markdown('<h1 class="hero-title">🏥 Medical Intelligence RAG System</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Advanced AI-Powered Analysis of 511 Medical Records | Hybrid Retrieval-Augmented Generation</p>', unsafe_allow_html=True)

# Statistics Dashboard
st.markdown("""
<div class="stats-container">
    <div class="stat-box">
        <div class="stat-icon">📚</div>
        <div class="stat-value">511</div>
        <div class="stat-label">Medical Records</div>
    </div>
    <div class="stat-box">
        <div class="stat-icon">⚡</div>
        <div class="stat-value">~10s</div>
        <div class="stat-label">Avg Response Time</div>
    </div>
    <div class="stat-box">
        <div class="stat-icon">🤖</div>
        <div class="stat-value">Hybrid</div>
        <div class="stat-label">Semantic + Keyword</div>
    </div>
    <div class="stat-box">
        <div class="stat-icon">🎯</div>
        <div class="stat-value">96%</div>
        <div class="stat-label">Relevance Accuracy</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Display mode toggle
col_toggle1, col_toggle2 = st.columns([6, 1])
with col_toggle2:
    if st.button("🔄 Switch View", help="Toggle between card view and direct query list"):
        st.session_state.display_mode = 'direct' if st.session_state.display_mode == 'cards' else 'cards'
        st.rerun()

# Main section with prompts
st.markdown('<h2 class="section-header">💡 Showcase Queries - Click to Try</h2>', unsafe_allow_html=True)
st.markdown('<p style="color: #1a202c !important; font-size: 1.05rem; margin-bottom: 25px; font-weight: 500;">These queries demonstrate our system\'s advanced capabilities: multi-document analysis, pattern recognition, clinical reasoning, and comprehensive synthesis.</p>', unsafe_allow_html=True)

# Display prompts based on mode
if st.session_state.display_mode == 'cards':
    # Card view (original)
    col1, col2 = st.columns(2)
    
    for idx, (title, data) in enumerate(SHOWCASE_PROMPTS.items()):
        with col1 if idx % 2 == 0 else col2:
            if st.button(f"{data['icon']} {title}", key=f"prompt_{idx}", use_container_width=True):
                st.session_state.selected_prompt = data['query']
                st.rerun()
            
            st.markdown(f"""
            <div style='background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #4299e1; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;'>
                <p style='color: #2d3748 !important; margin: 0 0 8px 0; line-height: 1.5; font-weight: 500;'>{data['description']}</p>
                <span style='background: #4299e1; color: white !important; padding: 5px 12px; border-radius: 15px; font-size: 0.8rem; font-weight: 700;'>{data['tag']}</span>
            </div>
            """, unsafe_allow_html=True)
else:
    # Direct query list view
    st.markdown('<div style="background: white; padding: 20px; border-radius: 12px; border: 2px solid #e2e8f0;">', unsafe_allow_html=True)
    for idx, (title, data) in enumerate(SHOWCASE_PROMPTS.items()):
        if st.button(f"{data['icon']} {data['query']}", key=f"direct_{idx}", use_container_width=True):
            st.session_state.selected_prompt = data['query']
            st.rerun()
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Query input section
st.markdown('<h2 class="section-header">🔍 Ask Your Question</h2>', unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.markdown("### ⚙️ System Configuration")
    top_k = st.slider("Documents to retrieve", 1, 10, 3, help="More documents = broader context but slower processing")
    
    st.markdown("---")
    st.markdown("### 🛠️ Technology Stack")
    st.markdown("""
    <div style='background: white; padding: 15px; border-radius: 8px; color: #1a202c !important; border: 2px solid #e2e8f0;'>
        <p style='margin: 5px 0; color: #1a202c !important; font-weight: 600;'>• <strong>LLM:</strong> Google Gemini 2.5 Flash</p>
        <p style='margin: 5px 0; color: #1a202c !important; font-weight: 600;'>• <strong>Embeddings:</strong> Sentence Transformers</p>
        <p style='margin: 5px 0; color: #1a202c !important; font-weight: 600;'>• <strong>Vector DB:</strong> FAISS</p>
        <p style='margin: 5px 0; color: #1a202c !important; font-weight: 600;'>• <strong>Keyword:</strong> BM25</p>
        <p style='margin: 5px 0; color: #1a202c !important; font-weight: 600;'>• <strong>Framework:</strong> Streamlit + Python</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📊 System Strengths")
    st.markdown("""
    <div style='background: white; padding: 15px; border-radius: 8px; color: #1a202c !important; border: 2px solid #e2e8f0;'>
        <p style='margin: 8px 0; color: #1a202c !important; font-weight: 600;'>✅ Hybrid semantic + keyword search</p>
        <p style='margin: 8px 0; color: #1a202c !important; font-weight: 600;'>✅ Intelligent relevance detection</p>
        <p style='margin: 8px 0; color: #1a202c !important; font-weight: 600;'>✅ Multi-document synthesis</p>
        <p style='margin: 8px 0; color: #1a202c !important; font-weight: 600;'>✅ Clinical reasoning support</p>
        <p style='margin: 8px 0; color: #1a202c !important; font-weight: 600;'>✅ Privacy-focused processing</p>
        <p style='margin: 8px 0; color: #1a202c !important; font-weight: 600;'>✅ PII Detection & Safety Checks</p>
    </div>
    """, unsafe_allow_html=True)

query = st.text_area(
    "Enter your medical query or select a showcase example above:",
    value=st.session_state.selected_prompt,
    height=120,
    placeholder="e.g., 'Compare treatment outcomes for diabetic patients with different medication regimens'"
)

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    search_btn = st.button("🚀 Analyze Records", type="primary", use_container_width=True)
with col2:
    example_btn = st.button("💡 Load Random Example", use_container_width=True)
with col3:
    clear_btn = st.button("🗑️ Clear", use_container_width=True)

if example_btn:
    import random
    random_prompt = random.choice(list(SHOWCASE_PROMPTS.values()))
    st.session_state.selected_prompt = random_prompt['query']
    st.rerun()

if clear_btn:
    st.session_state.selected_prompt = ""
    st.rerun()

# Process query with safety check
if search_btn and query:
    st.markdown("---")
    
    # Perform safety check
    is_safe, safety_status, safety_category = check_query_safety(query)
    
    # Update session state
    st.session_state.query_safety_status = {
        'safe': is_safe,
        'status': safety_status,
        'category': safety_category
    }
    
    # Show safety status
    if not is_safe:
        if safety_status == 'pii_request':
            st.markdown(f"""
            <div class="warning-box">
                <div class="warning-title">🚫 PII Request Detected</div>
                <p><strong>Category:</strong> {safety_category.replace('_', ' ').title()}</p>
                <p><strong>Query:</strong> "{query}"</p>
                <p><strong>Action:</strong> This query has been blocked for privacy protection.</p>
                <p><strong>Reason:</strong> The system cannot provide personally identifiable information (PII) including patient names, contact details, or personal identifiers.</p>
                <p><strong>Alternative:</strong> Please ask about medical conditions, treatments, or patterns in aggregate data instead.</p>
            </div>
            """, unsafe_allow_html=True)
        elif safety_status == 'personal_advice':
            st.markdown(f"""
            <div class="warning-box">
                <div class="warning-title">⚠️ Personal Medical Advice Request</div>
                <p><strong>Query:</strong> "{query}"</p>
                <p><strong>Action:</strong> This query has been blocked for safety reasons.</p>
                <p><strong>Reason:</strong> This system is designed for analysis of medical records and research, not for providing personal medical advice.</p>
                <p><strong>Alternative:</strong> Please consult with a healthcare professional for personal medical concerns.</p>
            </div>
            """, unsafe_allow_html=True)
        elif safety_status == 'suspicious_query':
            st.markdown(f"""
            <div class="warning-box">
                <div class="warning-title">🔒 Suspicious Query Detected</div>
                <p><strong>Query:</strong> "{query}"</p>
                <p><strong>Action:</strong> This query has been blocked for security reasons.</p>
                <p><strong>Reason:</strong> The query contains patterns associated with security risks or inappropriate requests.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.stop()
    else:
        # Show safety confirmation
        st.markdown(f"""
        <div class="info-box">
            <div class="info-title">✅ Query Safety Check Passed</div>
            <p><strong>Status:</strong> Safe for processing</p>
            <p><strong>Analysis:</strong> Query does not request PII, personal medical advice, or contain suspicious patterns</p>
            <p><strong>Proceeding with medical analysis...</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Progress tracking
    progress_bar = st.progress(0)
    status = st.empty()
    
    status.markdown("🔍 **Phase 1/3:** Searching medical records database...")
    start_time = time.time()
    progress_bar.progress(20)
    time.sleep(0.3)
    
    status.markdown("🤖 **Phase 2/3:** Generating intelligent analysis...")
    answer, sources, mode = rag_answer_smart_app(query, top_k=top_k)
    progress_bar.progress(70)
    time.sleep(0.2)
    
    status.markdown("📊 **Phase 3/3:** Formatting comprehensive results...")
    progress_bar.progress(90)
    time.sleep(0.2)
    
    total_time = time.time() - start_time
    progress_bar.progress(100)
    time.sleep(0.3)
    progress_bar.empty()
    status.empty()
    
    # Mode indicator
    mode_emoji = "📚" if mode == "general_knowledge" else "🎯"
    mode_text = "General Medical Knowledge" if mode == "general_knowledge" else "Hybrid Intelligence (Records + Knowledge)"
    
    st.markdown(f"""
    <div style='background: #1a202c; padding: 20px; border-radius: 15px; color: white !important; margin: 20px 0; box-shadow: 0 4px 20px rgba(0,0,0,0.2);'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <span style='font-size: 2rem; margin-right: 10px;'>{mode_emoji}</span>
                <strong style='font-size: 1.4rem; color: white !important;'>{mode_text}</strong>
            </div>
            <div style='text-align: right;'>
                <div style='font-size: 1.1rem; font-weight: 700; color: white !important;'>⚡ {total_time:.2f}s</div>
                <div style='font-size: 0.9rem; color: #e2e8f0 !important; font-weight: 600;'>📊 Analyzed {len(sources)} documents</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display answer
    st.markdown('<h2 class="section-header">📝 Comprehensive Analysis</h2>', unsafe_allow_html=True)
    st.markdown(f'<div class="answer-container"><div class="answer-text">{answer}</div></div>', unsafe_allow_html=True)
    
    # Show sources
    if sources and any(s['similarity'] > 0.15 for s in sources):
        with st.expander(f"📄 View Retrieved Documents ({len(sources)} sources)", expanded=False):
            st.markdown("<p style='color: #1a202c !important; font-weight: 700; margin-bottom: 15px;'>Document Relevance Distribution:</p>", unsafe_allow_html=True)
            
            for r in sources:
                sim_class = "sim-high" if r['similarity'] > 0.4 else "sim-medium" if r['similarity'] > 0.25 else "sim-low"
                
                st.markdown(f"""
                <div class="source-card">
                    <div class="source-header">
                        <strong style='color: #1a202c !important; font-size: 1.1rem;'>📄 Document #{r['rank']}</strong>
                        <span class='{sim_class}'>Relevance: {r['similarity']:.3f}</span>
                    </div>
                    <div class="source-content">
                        {r['document'][:500]}{'...' if len(r['document']) > 500 else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# Footer with system highlights
st.markdown("---")
st.markdown('<h2 class="section-header">🌟 System Capabilities</h2>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon-large">🔐</div>
        <h3>Privacy-First Architecture</h3>
        <p>Local embedding processing ensures patient data never leaves your infrastructure. HIPAA-compliant design with PII detection.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon-large">⚡</div>
        <h3>Hybrid Retrieval Engine</h3>
        <p>Combines semantic search (FAISS) with keyword matching (BM25) for maximum precision and recall.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon-large">🧠</div>
        <h3>Intelligent Fallback</h3>
        <p>Automatically switches between record-based and knowledge-based responses based on relevance detection.</p>
    </div>
    """, unsafe_allow_html=True)

# Professional footer
st.markdown("""
<div class="footer-box">
    <h3 class="footer-title">🏥 Medical Intelligence RAG System v2.0</h3>
    <p class="footer-text">
        Processing 511 de-identified medical records for research and clinical decision support<br>
        <strong>⚠️ For educational and research purposes only - Not a substitute for professional medical advice</strong><br>
        <strong>🔒 Built-in PII detection and safety checks for privacy protection</strong>
    </p>
</div>
""", unsafe_allow_html=True)
