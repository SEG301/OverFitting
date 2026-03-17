"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { SearchResult } from "@/lib/api";

interface ResultItemProps {
  result: SearchResult;
  index: number;
}

export default function ResultItem({ result, index }: ResultItemProps) {
  // Extracting URL to highlight as a breadcrumb logic for the UI
  const urlDomain = "infodoanhnghiep.com";
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="mb-8 w-full max-w-3xl"
    >
      <div className="flex flex-col">
        {/* Breadcrumb / Context Source */}
        <div className="flex items-center text-sm text-gray-700 mb-1">
          <div className="flex items-center bg-gray-100 rounded-full h-7 w-7 justify-center mr-2">
            <span className="text-xs font-bold w-4 h-4 rounded-full bg-blue-500 text-white flex items-center justify-center">I</span>
          </div>
          <p className="truncate">
            <span className="text-gray-900">{urlDomain}</span>
            <span className="text-gray-500"> › thong-tin › {result.universal_id}</span>
          </p>
        </div>

        {/* Title Link */}
        <Link href={`/company/${encodeURIComponent(result.universal_id)}`}>
          <h3 className="text-xl font-normal text-[var(--color-google-blue)] hover:underline cursor-pointer">
            {result.company_name}
          </h3>
        </Link>
        
        {/* Descriptive snippet with score */}
        <div className="mt-1 text-sm text-[var(--color-google-gray)] line-clamp-3">
          <span className="text-gray-500 font-medium mr-1">{new Date().toLocaleDateString('vi-VN')} —</span> 
          {result.description}
        </div>
        
        {/* Badges / Metrics */}
        <div className="mt-2 flex gap-2">
          <span className="inline-flex items-center rounded-md bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">
            BM25 + Semantic
          </span>
          <span className="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10">
            Score: {result.score.toFixed(4)}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
