"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { searchAPI } from "@/lib/api";
import SearchBar from "@/components/SearchBar";
import CompanyCard from "@/components/CompanyCard";
import { ArrowLeft, SearchIcon } from "lucide-react";

export default function CompanyDetail() {
  const { id } = useParams();
  const router = useRouter();
  const [company, setCompany] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      const fetchCompany = async () => {
        setLoading(true);
        // id is natively decoded by NextJS useParams, but we use it safely
        const data = await searchAPI.getCompany(id as string);
        setCompany(data);
        setLoading(false);
      };
      
      fetchCompany();
    }
  }, [id]);

  return (
    <div className="min-h-screen bg-[#f8f9fa]">
      {/* Sticky Top Header Similar to the main layout for unified UX */}
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
            {/* Keeping the search bar functional on the detail page */}
            <SearchBar initialQuery="" onSearch={(q) => router.push(`/?q=${encodeURIComponent(q)}`)} />
          </div>
          
          <div className="ml-auto flex items-center gap-3">
             <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-sm shadow-sm hidden md:flex">U</div>
          </div>
        </div>
      </header>
      
      <main className="px-4 py-8 relative">
        <button 
          onClick={() => router.back()}
          className="flex items-center text-sm text-gray-600 hover:text-blue-600 transition-colors bg-white px-4 py-2 rounded-full shadow-sm max-w-max sticky top-24 z-10 mx-auto sm:ml-[130px] my-4 border border-gray-200"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Quay Lại Kết Quả Tìm Kiếm
        </button>

        <CompanyCard company={company} loading={loading} />
      </main>
    </div>
  );
}
