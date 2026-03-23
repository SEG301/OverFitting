"use client";

import { useState, useRef, useEffect } from "react";
import { Search, X, Mic, Camera } from "lucide-react";
import { searchAPI, SuggestResult } from "@/lib/api";
import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/navigation";

interface SearchBarProps {
  initialQuery?: string;
  onSearch?: (query: string, mode: 'name' | 'tax_code') => void;
  centered?: boolean;
}

export default function SearchBar({ initialQuery = "", onSearch, centered = false }: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState<SuggestResult[]>([]);
  const [isFocused, setIsFocused] = useState(false);
  const [searchMode, setSearchMode] = useState<'name' | 'tax_code'>('name');
  const [error, setError] = useState<string | null>(null);

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
    if (query.length >= 2 && isFocused && searchMode === 'name') {
      const fetchSuggestions = async () => {
        const results = await searchAPI.suggest(query);
        setSuggestions(results);
      };

      const timeoutId = setTimeout(fetchSuggestions, 200);
      return () => clearTimeout(timeoutId);
    } else {
      setSuggestions([]);
    }
  }, [query, isFocused, searchMode]);

  // Clear error when typing
  useEffect(() => {
    if (error) setError(null);
  }, [query]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    if (searchMode === 'tax_code') {
      // Validation for Tax Code mode: strictly numbers only
      const isNumeric = /^\d+$/.test(query.trim());
      if (!isNumeric) {
        setError("Mã số thuế không hợp lệ: Chỉ được nhập các con số (0-9).");
        return;
      }
    }

    setIsFocused(false);
    if (onSearch) {
      onSearch(query.trim(), searchMode);
    } else {
      router.push(`/?q=${encodeURIComponent(query.trim())}&mode=${searchMode}`);
    }
  };

  const handleClear = () => {
    setQuery("");
    setSuggestions([]);
  };

  return (
    <div ref={wrapperRef} className={`relative w-full ${centered ? "max-w-3xl mx-auto" : "max-w-2xl"}`}>
      {/* Mode Switcher */}
      <div className="flex bg-gray-100 p-1 rounded-t-xl mb-0 w-max border-x border-t border-gray-200 ml-4 translate-y-[1px] relative z-20">
        <button
          onClick={() => setSearchMode('name')}
          className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all ${searchMode === 'name' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
        >
          TÌM THEO TÊN
        </button>
        <button
          type="button"
          onClick={() => setSearchMode('tax_code')}
          className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all ${searchMode === 'tax_code' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
        >
          TÌM THEO MST
        </button>
      </div>

      <motion.form
        onSubmit={handleSubmit}
        initial={false}
        animate={{
          boxShadow: isFocused
            ? "0 1px 6px rgba(32, 33, 36, 0.28)"
            : "0 1px 2px rgba(0, 0, 0, 0)",
          borderRadius: (isFocused && suggestions.length > 0) ? "0 24px 0 0" : (centered ? "24px" : "0 24px 24px 24px"),
          borderBottomColor: (isFocused && suggestions.length > 0) ? "transparent" : "#dfe1e5",
          borderColor: error ? "#ef4444" : "#dfe1e5"
        }}
        className={`flex items-center px-4 py-2 border border-gray-200 bg-white hover:shadow-md transition-shadow relative z-10
          ${centered ? "py-3 text-lg" : ""}`}
      >
        <Search className={`${error ? 'text-red-500' : 'text-gray-400'} w-5 h-5 mr-3`} />

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsFocused(true)}
          className="flex-1 bg-transparent outline-none text-gray-800 placeholder-gray-400"
          placeholder={searchMode === 'name' ? "Nhập tên công ty..." : "Nhập mã số thuế..."}
          autoComplete="off"
        />

        {query && (
          <button
            type="button"
            onClick={handleClear}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
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
                      onSearch(s.suggestion, searchMode);
                    } else {
                      router.push(`/?q=${encodeURIComponent(s.suggestion)}&mode=${searchMode}`);
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

      {/* Error Tooltip */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="absolute left-4 -bottom-10 bg-red-50 text-red-600 text-xs px-3 py-1.5 rounded-lg border border-red-100 shadow-sm z-30 flex items-center gap-2"
          >
            <div className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse"></div>
            {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
