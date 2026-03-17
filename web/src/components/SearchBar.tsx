"use client";

import { useState, useRef, useEffect } from "react";
import { Search, X, Mic, Camera } from "lucide-react";
import { searchAPI, SuggestResult } from "@/lib/api";
import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/navigation";

interface SearchBarProps {
  initialQuery?: string;
  onSearch?: (query: string) => void;
  centered?: boolean;
}

export default function SearchBar({ initialQuery = "", onSearch, centered = false }: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState<SuggestResult[]>([]);
  const [isFocused, setIsFocused] = useState(false);
  const router = useRouter();
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Close suggestions when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsFocused(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Fetch suggestions with debounce-like behavior
  useEffect(() => {
    if (query.length >= 2 && isFocused) {
      const fetchSuggestions = async () => {
        const results = await searchAPI.suggest(query);
        setSuggestions(results);
      };
      
      const timeoutId = setTimeout(fetchSuggestions, 200);
      return () => clearTimeout(timeoutId);
    } else {
      setSuggestions([]);
    }
  }, [query, isFocused]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;
    
    setIsFocused(false);
    if (onSearch) {
      onSearch(query.trim());
    } else {
      router.push(`/?q=${encodeURIComponent(query.trim())}`);
    }
  };

  const handleClear = () => {
    setQuery("");
    setSuggestions([]);
  };

  return (
    <div ref={wrapperRef} className={`relative w-full ${centered ? "max-w-3xl mx-auto" : "max-w-2xl"}`}>
      <motion.form 
        onSubmit={handleSubmit}
        initial={false}
        animate={{ 
          boxShadow: isFocused 
            ? "0 1px 6px rgba(32, 33, 36, 0.28)" 
            : "0 1px 2px rgba(0, 0, 0, 0)",
          borderRadius: (isFocused && suggestions.length > 0) ? "24px 24px 0 0" : "24px",
          borderBottomColor: (isFocused && suggestions.length > 0) ? "transparent" : "#dfe1e5"
        }}
        className={`flex items-center px-4 py-2 border border-gray-200 bg-white hover:shadow-md transition-shadow
          ${centered ? "py-3 text-lg" : ""}`}
      >
        <Search className="text-gray-400 w-5 h-5 mr-3" />
        
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsFocused(true)}
          className="flex-1 bg-transparent outline-none text-gray-800"
          placeholder="Nhập tên công ty..."
          autoComplete="off"
        />

        {query && (
          <button 
            type="button" 
            onClick={handleClear} 
            className="text-gray-500 hover:text-gray-700 p-1 mr-2"
          >
            <X className="w-5 h-5" />
          </button>
        )}
        
        <span className="w-px h-6 bg-gray-300 mx-2 hidden sm:block"></span>
        <span title="Google Voice Demo"><Mic className="text-blue-500 w-5 h-5 mx-2 cursor-pointer hidden sm:block" /></span>
        <span title="Google Lens Demo"><Camera className="text-blue-500 w-5 h-5 ml-2 cursor-pointer hidden sm:block" /></span>
      </motion.form>

      {/* Autocomplete Dropdown */}
      <AnimatePresence>
        {isFocused && suggestions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.1 }}
            className="absolute top-full left-0 right-0 bg-white border border-t-0 border-gray-200 shadow-lg z-50 overflow-hidden"
            style={{ borderRadius: "0 0 24px 24px", paddingBottom: "8px" }}
          >
            <div className="w-full h-[1px] bg-gray-200 mx-4 w-[calc(100%-32px)] mb-2"></div>
            <ul>
              {suggestions.map((s, idx) => (
                <li 
                  key={idx}
                  onClick={() => {
                    setQuery(s.suggestion);
                    setIsFocused(false);
                    if (onSearch) {
                      onSearch(s.suggestion);
                    } else {
                      router.push(`/?q=${encodeURIComponent(s.suggestion)}`);
                    }
                  }}
                  className="px-5 py-2 hover:bg-gray-100 flex items-center cursor-pointer text-gray-800"
                >
                  <Search className="text-gray-400 w-4 h-4 mr-3" />
                  {/* Basic Keyword bolding for autocomplete */}
                  <span className="font-semibold">{s.suggestion.slice(0, query.length)}</span>
                  <span>{s.suggestion.slice(query.length)}</span>
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
