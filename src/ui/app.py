"""
Search Engine Web Interface - Milestone 3
=========================================
Giao diện người dùng sử dụng Streamlit.
Chương trình tích hợp BM25, Vector Search và Hybrid Search.
"""

import streamlit as st
import os
import sys
import time

# Thêm project root vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ranking.bm25 import BM25Searcher
from src.ranking.vector import VectorSearcher
from src.ranking.hybrid import HybridSearcher

# Page Config
st.set_page_config(
    page_title="OverFitting Search Engine",
    page_icon="🔍",
    layout="wide",
)

# Custom CSS for aesthetics (glassmorphism/premium feel)
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stTextInput > div > div > input {
        border-radius: 20px;
        border: 2px solid #007bff;
        padding: 10px 20px;
        font-size: 18px;
    }
    .stButton > button {
        border-radius: 20px;
        background-color: #007bff;
        color: white;
        padding: 10px 30px;
        font-weight: bold;
    }
    .result-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 5px solid #007bff;
    }
    .company-name {
        color: #007bff;
        font-size: 22px;
        font-weight: bold;
    }
    .tax-code {
        color: #6c757d;
        font-size: 14px;
    }
    .address {
        font-size: 16px;
        margin-top: 5px;
    }
    .industry {
        background-color: #e9ecef;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 13px;
        display: inline-block;
        margin-top: 10px;
        color: #495057;
    }
    .highlight {
        color: #ff4b4b;
        font-weight: bold;
    }
    .sidebar-section {
        background-color: #f1f3f5;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Cache Loaders
@st.cache_resource
def get_searchers():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    index_dir = os.path.join(project_root, "data", "index")
    jsonl_path = os.path.join(project_root, "data", "milestone1_fixed.jsonl")
    
    bm25 = BM25Searcher(index_dir=index_dir, jsonl_path=jsonl_path)
    bm25.load_index()
    
    vector = VectorSearcher(jsonl_path=jsonl_path)
    vector.load_index()
    
    hybrid = HybridSearcher(index_dir=index_dir, jsonl_path=jsonl_path)
    # Hybrid reuse components but let's load specifically if necessary
    
    return bm25, vector, hybrid

def main():
    # Sidebar
    st.sidebar.title("🛠 Settings")
    
    search_mode = st.sidebar.radio(
        "Search Method:",
        ["BM25 (Lexical)", "Vector (Semantic)", "Hybrid (Best of both)"],
        index=2 # Default Hybrid
    )
    
    top_k = st.sidebar.slider("Number of results (top-k):", 5, 50, 10)
    
    if search_mode == "Hybrid (Best of both)":
        alpha = st.sidebar.slider("Alpha (Weight):", 0.0, 1.0, 0.5, 0.1, help="Higher alpha = more BM25, Lower alpha = more Vector.")
    else:
        alpha = 0.5
        
    st.sidebar.divider()
    
    # Stats 
    bm25, vector, hybrid = get_searchers()
    stats = bm25.get_stats()
    
    st.sidebar.markdown(f"""
    <div class="sidebar-section">
        <b>📊 System Stats</b><br>
        • Documents: {stats['total_documents']:,}<br>
        • Vocab: {stats['vocabulary_size']:,}<br>
        • Avg length: {stats['avg_document_length']:.1f}<br>
    </div>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("🔍 Vietnamese Enterprise Search")
    st.write("Project Milestone 3 - Search Engine Prototype by **OverFitting**")
    
    # Main Search Box
    col1, col2 = st.columns([6, 1])
    with col1:
        query = st.text_input("", placeholder="Nhập tên công ty, ngành nghề hoặc từ khoá cần tìm...")
    with col2:
        st.write("##") # Spacer
        search_clicked = st.button("Search")
        
    if query or search_clicked:
        if not query:
            st.warning("Vui lòng nhập từ khoá tìm kiếm.")
            return
            
        st.info(f"Đang tìm kiếm bằng phương pháp: **{search_mode}** cho query: '*{query}*'")
        
        start_time = time.time()
        
        # Execute Search
        if search_mode == "BM25 (Lexical)":
            results = bm25.search(query, top_k=top_k)
        elif search_mode == "Vector (Semantic)":
            # VectorSearcher returns (doc_id, score), we need metadata
            raw_results = vector.search(query, top_k=top_k)
            results = []
            for doc_id, score in raw_results:
                results.append((doc_id, score, bm25._get_doc_metadata(doc_id)))
        else:
            results = hybrid.search(query, top_k=top_k, alpha=alpha)
            
        search_time = time.time() - start_time
        
        # Performance Insight
        st.caption(f"Tìm được {len(results)} kết quả trong {search_time*1000:.1f}ms")
        
        # Display Results
        if not results:
            st.error("Không tìm thấy kết quả nào. Hãy thử từ khóa khác!")
        else:
            for rank, (doc_id, score, meta) in enumerate(results, 1):
                with st.container():
                    st.markdown(f"""
                    <div class="result-card">
                        <span class="company-name">{meta.get('company_name', 'Unnamed')}</span> 
                        <span class="tax-code">| MST: {meta.get('tax_code', 'N/A')}</span>
                        <div class="address">📍 {meta.get('address', 'N/A')}</div>
                        <div class="address">👤 Đại diện: {meta.get('representative', 'N/A')} | 🟢 {meta.get('status', 'N/A')}</div>
                        <div class="industry">🏢 {meta.get('industries_str_seg', 'N/A').replace('_', ' ')}</div>
                        <div style="font-size: 12px; color: #adb5bd; margin-top: 10px; text-align: right;">
                            Rank: #{rank} | Score: {score:.4f} | ID: {doc_id}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("<p style='text-align: center;'>SEG301 Project - 2026</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
