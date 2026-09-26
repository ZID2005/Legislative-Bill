/**
 * __tests__/api/client.test.ts
 * ============================
 * Tests for the base API client — error handling and type safety.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { ApiError, isApiError } from "@/lib/errors";

describe("ApiError", () => {
  it("creates a NOT_FOUND error from status 404", () => {
    const err = ApiError.fromStatus(404);
    expect(err.code).toBe("NOT_FOUND");
    expect(err.status).toBe(404);
    expect(err.isNotFound).toBe(true);
    expect(err.userMessage).toBeTruthy();
  });

  it("creates a SERVER_ERROR from status 500", () => {
    const err = ApiError.fromStatus(500);
    expect(err.code).toBe("SERVER_ERROR");
    expect(err.isServerError).toBe(true);
  });

  it("creates a NETWORK_ERROR from network()", () => {
    const err = ApiError.network();
    expect(err.code).toBe("NETWORK_ERROR");
    expect(err.status).toBe(0);
    expect(err.isNetworkError).toBe(true);
  });

  it("creates UNKNOWN_ERROR for unrecognized status", () => {
    const err = ApiError.fromStatus(418);
    expect(err.code).toBe("UNKNOWN_ERROR");
  });

  it("isApiError() correctly identifies ApiError instances", () => {
    const err = ApiError.fromStatus(401);
    expect(isApiError(err)).toBe(true);
    expect(isApiError(new Error("regular"))).toBe(false);
    expect(isApiError(null)).toBe(false);
    expect(isApiError("string error")).toBe(false);
  });

  it("preserves custom message when provided", () => {
    const err = ApiError.fromStatus(403, "Custom forbidden message");
    expect(err.message).toBe("Custom forbidden message");
    expect(err.code).toBe("FORBIDDEN");
  });

  it("all standard HTTP error codes map correctly", () => {
    const mapping: Array<[number, string]> = [
      [400, "BAD_REQUEST"],
      [401, "UNAUTHORIZED"],
      [403, "FORBIDDEN"],
      [404, "NOT_FOUND"],
      [409, "CONFLICT"],
      [422, "VALIDATION_ERROR"],
      [500, "SERVER_ERROR"],
    ];

    for (const [status, code] of mapping) {
      const err = ApiError.fromStatus(status);
      expect(err.code).toBe(code);
    }
  });
});

describe("API client module", () => {
  it("imports and exports correctly", async () => {
    const module = await import("@/lib/api/client");
    expect(module.apiClient).toBeDefined();
    expect(typeof module.apiClient.get).toBe("function");
    expect(typeof module.apiClient.post).toBe("function");
    expect(typeof module.apiClient.put).toBe("function");
    expect(typeof module.apiClient.patch).toBe("function");
    expect(typeof module.apiClient.delete).toBe("function");
  });
});
