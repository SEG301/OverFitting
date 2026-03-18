import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface SearchResult {
  universal_id: string;
  company_name: string;
  description: string;
  score: number;
}

export interface SuggestResult {
  suggestion: string;
}

export const searchAPI = {
  search: async (query: string, topK: number = 10, skip: number = 0, useRerank: boolean = true, filters?: Record<string, string>): Promise<SearchResult[]> => {
    try {
      const response = await apiClient.get('/search', {
        params: { 
          q: query, 
          top_k: topK, 
          skip: skip,
          use_rerank: useRerank,
          location: filters?.location,
          industry: filters?.industry
        },
      });
      return response.data;
    } catch (error) {
      console.error("Search error:", error);
      return [];
    }
  },

  suggest: async (query: string): Promise<SuggestResult[]> => {
    if (query.length < 2) return [];
    try {
      const response = await apiClient.get('/suggest', {
        params: { q: query },
      });
      return response.data;
    } catch (error) {
      return [];
    }
  },

  getCompany: async (id: string): Promise<any> => {
    try {
      // Encode URL component just in case
      const response = await apiClient.get(`/company/${encodeURIComponent(id)}`);
      return response.data;
    } catch (error) {
      console.error("Company Fetch Error:", error);
      return null;
    }
  }
};
