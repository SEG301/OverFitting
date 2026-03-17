"use client";

import { motion } from "framer-motion";
import { Building2, MapPin, Tag, Flag, AlertCircle } from "lucide-react";

interface CompanyCardProps {
  company: any;
  loading?: boolean;
}

export default function CompanyCard({ company, loading = false }: CompanyCardProps) {
  if (loading) {
    return (
      <div className="animate-pulse space-y-6 max-w-4xl mx-auto mt-10 p-8 border border-gray-100 rounded-2xl shadow-sm">
        <div className="h-10 bg-gray-200 rounded w-1/2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/4"></div>
        <div className="h-32 bg-gray-200 rounded w-full"></div>
      </div>
    );
  }

  if (!company) {
    return (
      <div className="flex flex-col items-center justify-center py-20 bg-gray-50 rounded-2xl text-gray-500 mt-10">
         <AlertCircle className="w-12 h-12 mb-4 text-red-400" />
         <h2 className="text-xl font-medium text-gray-800">Không tìm thấy thông tin</h2>
         <p>Dữ liệu doanh nghiệp này không có sẵn hoặc ID không hợp lệ.</p>
      </div>
    );
  }

  const { company_name, id, address, description, reviews, tags, status, representative } = company;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="max-w-5xl mx-auto my-10 bg-white rounded-3xl overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-gray-100/50 transition-all"
    >
      {/* Premium Header Gradient */}
      <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 p-8 text-white relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full transform translate-x-20 -translate-y-20 blur-3xl"></div>
        <Building2 className="w-12 h-12 mb-4 text-white/90" />
        <h1 className="text-3xl md:text-4xl font-semibold mb-2 tracking-tight">
          {company_name || id}
        </h1>
        <div className="flex flex-wrap items-center gap-4 text-sm font-medium text-white/80">
          <span className="flex items-center">
            <Tag className="w-4 h-4 mr-1 pb-[1px]" />
            Mã Số Thuế: <strong className="ml-1 text-white">{id || "N/A"}</strong>
          </span>
          {status && (
            <span className="flex items-center">
              <span className="w-2 h-2 rounded-full bg-green-400 mr-2 shadow-[0_0_8px_rgba(74,222,128,0.8)] animate-pulse"></span>
              {status}
            </span>
          )}
        </div>
      </div>

      <div className="p-8 grid md:grid-cols-3 gap-8">
        {/* Left Content - Details */}
        <div className="md:col-span-2 space-y-8">
          {description && (
            <section>
              <h3 className="text-xl font-medium text-gray-900 mb-3 border-b pb-2 flex items-center">
                Giới Thiệu
              </h3>
              <p className="text-gray-600 leading-relaxed indent-4 text-justify">
                {description}
              </p>
            </section>
          )}

          {/* Quick Info Grid */}
          <section className="grid sm:grid-cols-2 gap-4">
            <div className="bg-gray-50/50 p-4 rounded-xl border border-gray-100">
               <span className="text-sm text-gray-500 flex items-center mb-1">
                 <Building2 className="w-4 h-4 mr-1" />
                 Người Đại Diện
               </span>
               <p className="font-medium text-gray-900">{representative || "Không có dữ liệu"}</p>
            </div>
            
            <div className="bg-gray-50/50 p-4 rounded-xl border border-gray-100">
               <span className="text-sm text-gray-500 flex items-center mb-1">
                 <MapPin className="w-4 h-4 mr-1" />
                 Trụ Sở Chính
               </span>
               <p className="font-medium text-gray-900">{address || "Không rõ."}</p>
            </div>
          </section>

          {/* Reviews Thread Display (if available array) */}
          {Array.isArray(reviews) && reviews.length > 0 && (
             <section className="mt-8">
                <h3 className="text-xl font-medium text-gray-900 mb-4 flex items-center">
                  Nhận Xét ({reviews.length})
                </h3>
                <div className="space-y-4">
                  {reviews.slice(0, 5).map((rev: any, idx) => (
                    <div key={idx} className="bg-gray-50 rounded-2xl p-5 shadow-sm border border-gray-100/60 transition-colors hover:bg-gray-100/50">
                      <div className="flex justify-between items-start mb-2">
                        <span className="font-semibold text-gray-800">{rev.reviewer_name || "Khách ẩn danh"}</span>
                        <div className="flex bg-yellow-100 text-yellow-700 px-2 py-1 rounded text-xs font-bold shadow-sm">
                           ★ {rev.rating || '5.0'}
                        </div>
                      </div>
                      <p className="text-gray-600 mt-1 italic leading-relaxed text-sm">&quot;{rev.review_content || rev.content}&quot;</p>
                      <div className="mt-3 flex gap-2">
                        {rev.pros && <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full px-3 shadow-sm border border-green-200">👍 {rev.pros}</span>}
                        {rev.cons && <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full px-3 shadow-sm border border-red-200">👎 {rev.cons}</span>}
                      </div>
                    </div>
                  ))}
                </div>
             </section>
          )}
        </div>

        {/* Right Content - Tags/Categories */}
        <div className="md:col-span-1 border-l border-gray-100 pl-8">
           <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 flex items-center">
              <Flag className="w-5 h-5 mr-2 text-[var(--color-google-blue)]" />
              Lĩnh Vực / Từ Khóa
           </h3>
           <div className="flex flex-wrap gap-2">
             {tags ? 
               (Array.isArray(tags) ? tags : [tags]).map((tag: string, idx) => (
                 <span key={idx} className="bg-blue-50/50 hover:bg-blue-100 transition-colors text-blue-700 py-1.5 px-3 rounded-xl border border-blue-100/60 text-sm font-medium cursor-default shadow-sm">
                   {tag.replace(/_/g, " ")}
                 </span>
               ))
               : <span className="text-gray-400 italic">Chưa phân loại lĩnh vực cụ thể</span>
             }
           </div>
        </div>
      </div>
    </motion.div>
  );
}
