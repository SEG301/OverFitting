"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import SearchBar from "@/components/SearchBar";
import ResultItem from "@/components/ResultItem";
import { searchAPI, SearchResult } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { SearchIcon, Loader2, X } from "lucide-react";
import CompanyCard from "@/components/CompanyCard";

function SearchContent() {
  const searchParams = useSearchParams();
  const q = searchParams.get("q");

  const [query, setQuery] = useState(q || "");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [useRerank, setUseRerank] = useState(true);
  
  const [locationFilter, setLocationFilter] = useState("");
  const [industryFilter, setIndustryFilter] = useState("");
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const pageSize = 15;
  
  // Progress State
  const [searchStatus, setSearchStatus] = useState("Lexical Search Engine (BM25)...");
  const [progress, setProgress] = useState(0);

  const [modalLoading, setModalLoading] = useState(false);
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null);
  const [selectedCompanyData, setSelectedCompanyData] = useState<any>(null);
  const modeFromUrl = (searchParams.get("mode") as 'name' | 'tax_code') || 'name';
  const [searchMode, setSearchMode] = useState<'name' | 'tax_code'>(modeFromUrl);

  useEffect(() => {
    const qParam = searchParams.get("q");
    const modeParam = (searchParams.get("mode") as 'name' | 'tax_code') || 'name';
    
    if (modeParam !== searchMode) {
      setSearchMode(modeParam);
    }

    if (qParam && (qParam !== query || results.length === 0)) {
      setQuery(qParam);
      handleSearch(qParam, locationFilter, industryFilter, 0, false, modeParam);
    }
  }, [searchParams]);

  const handleSearch = async (searchQuery: string, loc: string = locationFilter, ind: string = industryFilter, currentSkip: number = 0, append: boolean = false, mode: 'name' | 'tax_code' = searchMode) => {
    if (!searchQuery.trim()) return;
    
    if (append) {
      setLoadingMore(true);
    } else {
      setResults([]); // Clear previous results to force progress bar to show
      setLoading(true);
      setHasSearched(true);
      setProgress(10);
      setSearchStatus(mode === 'name' ? "Lexical Search (BM25) - Filtering 1.8M docs..." : "Tax ID Engine - Perfect Match Lookup...");
    }
    
    // UI Progress Sequence simulation
    const progressInterval = !append ? setInterval(() => {
        setProgress(prev => {
            if (prev < 40) return prev + 5;
            if (prev < 75) return prev + 2; 
            if (prev < 95) return prev + 1;
            return prev;
        });
    }, 200) : null;

    if (!append) {
        if (mode === 'name') {
            setTimeout(() => setSearchStatus("Semantic Vector Mapping (FAISS E5)..."), 600);
            if (useRerank) setTimeout(() => setSearchStatus("Deep Neural Re-Ranking (MS-Marco AI)..."), 1300);
        } else {
            setTimeout(() => setSearchStatus("Validating Tax ID checksum..."), 400);
        }
    }

    const data = await searchAPI.search(
        searchQuery, 
        pageSize, 
        currentSkip, 
        useRerank, 
        { location: loc, industry: ind },
        mode === 'tax_code'
    );
    
    if (progressInterval) clearInterval(progressInterval);
    setProgress(100);
    
    const updateState = () => {
       setHasMore(data.length === pageSize); // Set hasMore based on actual data returned
       
       if (append) {
         setResults(prev => {
            const existingIds = new Set(prev.map(r => r.universal_id));
            const newResults = data.filter(r => !existingIds.has(r.universal_id));
            return [...prev, ...newResults];
         });
         setLoadingMore(false);
       } else {
         setResults(data);
         setLoading(false);
       }
       setSkip(currentSkip);
    };

    updateState();
  };

  const handleLoadMore = () => {
    handleSearch(query, locationFilter, industryFilter, skip + pageSize, true, searchMode);
  };

  const openCompanyModal = async (id: string) => {
    setSelectedCompanyId(id);
    setModalLoading(true);
    // Push state silently to keep URL meaningful without triggering a page-level re-search
    window.history.pushState({ modal: true, query }, '', `/company/${encodeURIComponent(id)}`);
    
    try {
      const data = await searchAPI.getCompany(id);
      setSelectedCompanyData(data);
    } catch (err) {
      console.error("Failed to fetch company details:", err);
    } finally {
      setModalLoading(false);
    }
  };

  const closeCompanyModal = () => {
    setSelectedCompanyId(null);
    setSelectedCompanyData(null);
    // Restore search URL without triggering the search useEffect (since query state remains same)
    window.history.pushState({ modal: false }, '', `/?q=${encodeURIComponent(query)}`);
  };

  // Handle browser back button to close modal
  useEffect(() => {
    const handlePopState = (event: PopStateEvent) => {
      if (selectedCompanyId) {
        setSelectedCompanyId(null);
        setSelectedCompanyData(null);
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [selectedCompanyId]);

  if (!hasSearched && !q) {
    // HOMEPAGE VIEW (Google-like)
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-[#f8f9fa]">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="w-full max-w-2xl flex flex-col items-center"
        >
          {/* Logo */}
          <h1 className="text-6xl sm:text-7xl font-semibold mb-8 tracking-tighter cursor-default">
            <span className="text-[#4285F4]">O</span>
            <span className="text-[#EA4335]">v</span>
            <span className="text-[#FBBC05]">e</span>
            <span className="text-[#4285F4]">r</span>
            <span className="text-[#34A853]">F</span>
            <span className="text-[#EA4335]">i</span>
            <span className="text-[#4285F4]">t</span>
            <span className="text-[#34A853]">t</span>
            <span className="text-[#FBBC05]">i</span>
            <span className="text-[#4285F4]">n</span>
            <span className="text-[#EA4335]">g</span>
          </h1>
          
          <SearchBar initialQuery="" centered={true} />
          
          <div className="mt-8 flex gap-3">
             <button className="bg-[#f8f9fa] border border-[#f8f9fa] hover:border-[#dadce0] hover:shadow-sm text-sm text-[#3c4043] px-4 py-2 rounded-md transition-all">
                Tìm với Google AI
             </button>
             <button className="bg-[#f8f9fa] border border-[#f8f9fa] hover:border-[#dadce0] hover:shadow-sm text-sm text-[#3c4043] px-4 py-2 rounded-md transition-all">
                Xem Data Crawler
             </button>
          </div>
          
          {/* Mock Suggestions List Section below input as requested */}
          <div className="mt-8 w-full max-w-3xl">
            <p className="text-sm text-gray-500 mb-3 text-center">Gợi ý tìm kiếm phổ biến:</p>
            <div className="flex flex-wrap justify-center gap-2">
              {[
                "FPT Software", "TMA Solutions", "NashTech", "VNG", "MoMo", 
                "VNPay", "KMS Technology", "Axon Active", "CMC Global", "Haravan"
              ].map((comp, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                     setQuery(comp);
                     // Set URL natively to trigger useEffect
                     window.history.pushState({}, '', `/?q=${encodeURIComponent(comp)}`);
                     handleSearch(comp, locationFilter, industryFilter, 0, false, 'name');
                  }}
                  className="bg-gray-100 hover:bg-gray-200 border border-gray-200 text-gray-700 text-sm py-1.5 px-4 rounded-full transition-all duration-200 hover:scale-[1.02] shadow-sm hover:shadow-md cursor-pointer"
                >
                  {comp}
                </button>
              ))}
            </div>
          </div>
          
          <div className="mt-8 text-sm text-[#70757a]">
             Ngôn ngữ được cung cấp: <a href="#" className="text-[#1a0dab] hover:underline">Tiếng Anh</a> <a href="#" className="text-[#1a0dab] hover:underline">Tiếng Việt</a>
          </div>
        </motion.div>
      </div>
    );
  }

  // RESULTS VIEW
  return (
    <div className="min-h-screen bg-white">
      {/* Sticky Header */}
      <header className="sticky top-0 z-40 bg-white border-b border-gray-200">
        <div className="flex flex-col sm:flex-row items-center p-4 sm:px-8 max-w-screen-2xl mx-auto gap-4 sm:gap-8">
          <button onClick={() => window.location.href = '/'} className="hidden sm:block">
            <h1 className="text-3xl font-semibold tracking-tighter">
              <span className="text-[#4285F4]">O</span>
              <span className="text-[#EA4335]">v</span>
              <span className="text-[#FBBC05]">e</span>
              <span className="text-[#4285F4]">r</span>
              <span className="text-[#34A853]">F</span>
              <span className="text-[#EA4335]">i</span>
              <span className="text-[#4285F4]">t</span>
            </h1>
          </button>
          
          <div className="w-full sm:max-w-3xl flex-1">
            <SearchBar 
                initialQuery={query} 
                onSearch={(q, mode) => handleSearch(q, locationFilter, industryFilter, 0, false, mode)} 
            />
          </div>
          
          <div className="ml-auto flex items-center gap-3">
             <label className="text-xs text-gray-500 flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={useRerank} 
                  onChange={(e) => setUseRerank(e.target.checked)} 
                  className="mr-1 accent-blue-600 rounded"
                /> 
                Deep Re-Rank (AI)
             </label>
             <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-sm shadow-sm hidden md:flex">U</div>
          </div>
        </div>
        
        {/* Navigation Tabs */}
        <div className="flex px-4 sm:px-[130px] gap-6 text-sm text-gray-600">
          <div className="pb-3 border-b-4 border-blue-600 text-blue-600 font-medium flex items-center gap-2 cursor-pointer">
            <SearchIcon className="w-4 h-4" /> Tất cả
          </div>
          <div className="pb-3 border-b-4 border-transparent hover:text-gray-900 flex items-center gap-2 cursor-pointer">
            Hình ảnh
          </div>
          <div className="pb-3 border-b-4 border-transparent hover:text-gray-900 flex items-center gap-2 cursor-pointer">
            Đánh giá Doanh nghiệp
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="px-4 sm:px-[130px] py-4 w-full">
        {/* Results Stats */}
        {!loading && results.length > 0 && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="text-sm text-gray-500 mb-6 font-medium"
          >
            Khoảng {results.length * 942} kết quả (0.28 giây) 
          </motion.div>
        )}

        <div className="flex flex-col md:flex-row gap-8">
          {/* Left Sidebar for Filters */}
          <div className="w-full md:w-64 flex-shrink-0">
             <div className="border border-gray-200 rounded-xl p-5 bg-white shadow-sm sticky top-40">
                <h3 className="font-semibold text-gray-800 mb-4 pb-2 border-b">Bộ Lọc Điểm Tiêu Chuẩn</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Địa điểm</label>
                    <select 
                      value={locationFilter}
                      onChange={(e) => {
                         setLocationFilter(e.target.value);
                         handleSearch(query, e.target.value, industryFilter, 0, false);
                      }}
                      className="w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                      <option value="">Tất cả địa điểm</option>
                      <option value="Hà Nội">Hà Nội</option>
                      <option value="Hồ Chí Minh">Hồ Chí Minh</option>
                      <option value="Đà Nẵng">Đà Nẵng</option>
                      <option value="Bình Dương">Bình Dương</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Ngành nghề (Từ Khóa)</label>
                    <input 
                      type="text" 
                      placeholder="vd: Công nghệ..."
                      value={industryFilter}
                      onChange={(e) => setIndustryFilter(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSearch(query, locationFilter, industryFilter, 0, false);
                      }}
                      className="w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                  </div>

                  <button 
                    onClick={() => handleSearch(query, locationFilter, industryFilter, 0, false)}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors text-sm"
                  >
                    Áp dụng bộ lọc
                  </button>
                  <button 
                    onClick={() => {
                        setLocationFilter('');
                        setIndustryFilter('');
                        handleSearch(query, '', '', 0, false);
                    }}
                    className="w-full mt-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-4 rounded-md transition-colors text-sm"
                  >
                    Xóa bộ lọc
                  </button>
                </div>
             </div>
          </div>

          {/* Main Results Column */}
          <div className="flex-1 max-w-3xl">
            <AnimatePresence>
            {loading && results.length === 0 ? (
                <motion.div 
                   key="loader"
                   initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                   className="py-10 flex flex-col items-center justify-center space-y-6"
                >
                  <div className="w-full max-w-md bg-gray-100 h-1 rounded-full overflow-hidden">
                     <motion.div 
                        initial={{ width: "0%" }}
                        animate={{ width: `${progress}%` }}
                        className="h-full bg-blue-600 shadow-[0_0_8px_rgba(37,99,235,0.6)]"
                     />
                  </div>
                  <div className="flex items-center space-x-3">
                    <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
                    <p className="text-gray-500 font-medium text-sm tracking-wide">{searchStatus}</p>
                  </div>
                </motion.div>
              ) : (
                <motion.div key="results" className="space-y-1">
                  {results.length === 0 ? (
                    <div className="pt-8">
                      <p className="text-xl text-gray-800 mb-4">Không tìm thấy <strong>{query}</strong> trong bất kỳ tài liệu doanh nghiệp nào.</p>
                      <p className="text-gray-600">Đề xuất:</p>
                      <ul className="list-disc pl-6 mt-2 text-gray-600 space-y-1">
                        <li>Xin chắc chắn rằng tất cả các từ đều đúng chính tả.</li>
                        <li>Hãy thử những từ khóa khác.</li>
                        <li>Hãy thử những từ khóa chung hơn.</li>
                      </ul>
                    </div>
                  ) : (
                    results.map((item, index) => (
                      <ResultItem 
                        key={item.universal_id} 
                        result={item} 
                        index={index} 
                        onClick={() => openCompanyModal(item.universal_id)}
                      />
                    ))
                  )}
                  
                  {/* Pagination Section */}
                  {results.length > 0 && hasMore && (
                    <div className="mt-12 mb-20 flex flex-col items-center">
                       {loadingMore ? (
                        <div className="flex items-center space-x-2 text-blue-500 py-4">
                          <Loader2 className="w-5 h-5 animate-spin" />
                          <span className="text-sm font-medium">Đang tải thêm...</span>
                        </div>
                       ) : (
                        <button 
                            onClick={handleLoadMore}
                            className="flex h-[36px] bg-[#f1f3f4] rounded-[18px] px-6 text-[var(--color-google-blue)] font-bold items-center mb-8 hover:bg-[#e8eaed] cursor-pointer shadow-sm transition-all text-sm"
                        >
                            Hiện thêm kết quả
                        </button>
                       )}
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          
          {/* Right Sidebar (Knowledge Panel Stub) */}
          <div className="hidden lg:block w-[350px] ml-16 mt-4">
             {results.length > 0 && (
                <div className="border border-gray-200 rounded-xl p-5 bg-white shadow-sm sticky top-40 hover:shadow-md transition-shadow">
                   <h2 className="text-xl text-gray-800 font-semibold mb-2">Vietnamese Enterprise Search</h2>
                   <p className="text-sm text-gray-600 mb-4">Powered by OverFitting NLP Pipeline</p>
                   
                   <div className="space-y-3 pt-3 border-t">
                     <div className="flex justify-between items-center text-sm">
                       <span className="text-gray-500 font-medium">Hybrid Search:</span>
                       <span className="text-gray-800 bg-gray-100 px-2 py-0.5 rounded">BM25 + Dense Vectors</span>
                     </div>
                     <div className="flex justify-between items-center text-sm">
                       <span className="text-gray-500 font-medium">Re-Ranker:</span>
                       <span className="text-blue-700 bg-blue-50 px-2 py-0.5 rounded font-medium border border-blue-100">MS-Marco M3</span>
                     </div>
                     <div className="flex justify-between items-center text-sm">
                       <span className="text-gray-500 font-medium">Corpus Size:</span>
                       <span className="text-gray-800 bg-gray-100 px-2 py-0.5 rounded">1.84M Rows</span>
                     </div>
                   </div>
                </div>
             )}
          </div>
        </div>
      </main>

      {/* DETAIL MODAL - Premium Zero-Reload UI */}
      <AnimatePresence>
        {selectedCompanyId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-10">
            {/* Backdrop */}
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={closeCompanyModal}
              className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            />
            
            {/* Modal Content */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-5xl max-h-full overflow-y-auto bg-white rounded-3xl shadow-2xl z-10 custom-scrollbar"
            >
              <button 
                onClick={closeCompanyModal}
                className="absolute top-6 right-6 p-2 rounded-full bg-white/20 hover:bg-white/40 text-white z-20 transition-all backdrop-blur-md border border-white/30"
              >
                <X className="w-6 h-6" />
              </button>
              
              <div className="p-0">
                <CompanyCard company={selectedCompanyData} loading={modalLoading} />
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Ensure proper suspense wrapper for next/navigation hooks in client components
export default function SearchPage() {
  return (
    <Suspense fallback={
       <div className="min-h-screen flex items-center justify-center">
         <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
       </div>
    }>
      <SearchContent />
    </Suspense>
  )
}
