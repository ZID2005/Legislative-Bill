/**
 * lib/api/portfolio.ts
 * ====================
 * Task 8.28 — Client API module for Portfolio & Personalized Decision Intelligence.
 */

import apiClient from "@/lib/api/client";
import type {
  ExplainRelevanceResponse,
  PersonalizedChangeFeedItem,
  PersonalizedDashboardResponse,
  PersonalizedImpactReportResponse,
  PortfolioHoldingItem,
  PortfolioLegislativeExposureResponse,
  UserPortfolioItem,
} from "@/types/api";

export const portfolioApi = {
  listPortfolios(): Promise<UserPortfolioItem[]> {
    return apiClient.get<UserPortfolioItem[]>("/api/v1/portfolio");
  },

  getDefaultPortfolio(): Promise<UserPortfolioItem> {
    return apiClient.get<UserPortfolioItem>("/api/v1/portfolio/default");
  },

  getPortfolio(portfolioId: string): Promise<UserPortfolioItem> {
    return apiClient.get<UserPortfolioItem>(`/api/v1/portfolio/${portfolioId}`);
  },

  createPortfolio(data: { name: string; description?: string; holdings?: any[] }): Promise<UserPortfolioItem> {
    return apiClient.post<UserPortfolioItem>("/api/v1/portfolio", data);
  },

  updatePortfolio(portfolioId: string, data: { name?: string; description?: string; is_active?: boolean }): Promise<UserPortfolioItem> {
    return apiClient.put<UserPortfolioItem>(`/api/v1/portfolio/${portfolioId}`, data);
  },

  deletePortfolio(portfolioId: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/portfolio/${portfolioId}`);
  },

  addHolding(portfolioId: string, data: Partial<PortfolioHoldingItem>): Promise<PortfolioHoldingItem> {
    return apiClient.post<PortfolioHoldingItem>(`/api/v1/portfolio/${portfolioId}/holdings`, data);
  },

  removeHolding(portfolioId: string, holdingId: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/portfolio/${portfolioId}/holdings/${holdingId}`);
  },

  importHoldings(portfolioId: string, holdings: any[], replace: boolean = false): Promise<UserPortfolioItem> {
    return apiClient.post<UserPortfolioItem>(`/api/v1/portfolio/${portfolioId}/import`, { holdings, replace });
  },

  getExposure(portfolioId?: string): Promise<PortfolioLegislativeExposureResponse> {
    const endpoint = portfolioId ? `/api/v1/portfolio/${portfolioId}/exposure` : "/api/v1/portfolio/exposure";
    return apiClient.get<PortfolioLegislativeExposureResponse>(endpoint);
  },

  getDecisionIntelligence(): Promise<PersonalizedDashboardResponse> {
    return apiClient.get<PersonalizedDashboardResponse>("/api/v1/workspace/decision-intelligence");
  },

  getChangeFeed(limit: number = 50): Promise<PersonalizedChangeFeedItem[]> {
    return apiClient.get<PersonalizedChangeFeedItem[]>(`/api/v1/workspace/change-feed?limit=${limit}`);
  },

  explainRelevance(billId: string): Promise<ExplainRelevanceResponse> {
    return apiClient.get<ExplainRelevanceResponse>(`/api/v1/workspace/explain-relevance?bill_id=${encodeURIComponent(billId)}`);
  },

  generateReport(portfolioId?: string): Promise<PersonalizedImpactReportResponse> {
    if (portfolioId) {
      return apiClient.post<PersonalizedImpactReportResponse>(`/api/v1/portfolio/${portfolioId}/report`);
    }
    return apiClient.get<PersonalizedImpactReportResponse>("/api/v1/workspace/report");
  },
};

export default portfolioApi;
