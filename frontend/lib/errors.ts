/**
 * lib/errors.ts
 * =============
 * Custom ApiError class with status-code mapping and helper methods.
 */

export interface ApiErrorInit {
  message?: string;
  status?: number;
  code?: string;
  userMessage?: string;
}

const STATUS_CODE_MAP: Record<number, string> = {
  400: "BAD_REQUEST",
  401: "UNAUTHORIZED",
  403: "FORBIDDEN",
  404: "NOT_FOUND",
  409: "CONFLICT",
  422: "VALIDATION_ERROR",
  500: "SERVER_ERROR",
};

const DEFAULT_USER_MESSAGES: Record<string, string> = {
  BAD_REQUEST: "The request could not be processed due to invalid parameters.",
  UNAUTHORIZED: "You must be authenticated to access this resource.",
  FORBIDDEN: "You do not have permission to perform this action.",
  NOT_FOUND: "The requested resource could not be found.",
  CONFLICT: "The request conflict with current state.",
  VALIDATION_ERROR: "Validation failed for the submitted data.",
  SERVER_ERROR: "A server error occurred. Please try again later.",
  NETWORK_ERROR: "Unable to reach the server. Please check your network connection.",
  UNKNOWN_ERROR: "An unexpected error occurred.",
};

export class ApiError extends Error {
  readonly _isApiError: boolean;
  readonly status: number;
  readonly code: string;
  readonly userMessage: string;

  constructor(init: string | ApiErrorInit = "API error", status = 500, code?: string) {
    const msg = typeof init === "string" ? init : (init.message ?? "API error");
    super(msg);
    this._isApiError = true;

    if (typeof init === "string") {
      this.status = status;
      this.code = code ?? STATUS_CODE_MAP[status] ?? "UNKNOWN_ERROR";
      this.userMessage = DEFAULT_USER_MESSAGES[this.code] ?? init;
    } else {
      this.status = init.status ?? 500;
      this.code = init.code ?? STATUS_CODE_MAP[this.status] ?? "UNKNOWN_ERROR";
      this.userMessage = init.userMessage ?? DEFAULT_USER_MESSAGES[this.code] ?? this.message;
    }

    Object.setPrototypeOf(this, ApiError.prototype);
  }

  get isNotFound(): boolean {
    return this.status === 404 || this.code === "NOT_FOUND";
  }

  get isServerError(): boolean {
    return this.status >= 500 || this.code === "SERVER_ERROR";
  }

  get isNetworkError(): boolean {
    return this.status === 0 || this.code === "NETWORK_ERROR";
  }

  static fromStatus(status: number, message?: string): ApiError {
    const code = STATUS_CODE_MAP[status] ?? "UNKNOWN_ERROR";
    const msg = message ?? (code === "UNKNOWN_ERROR" ? `HTTP error ${status}` : code);
    return new ApiError({
      status,
      code,
      message: msg,
      userMessage: message ?? DEFAULT_USER_MESSAGES[code] ?? msg,
    });
  }

  static network(message = "Network error: unable to connect to server"): ApiError {
    return new ApiError({
      status: 0,
      code: "NETWORK_ERROR",
      message,
      userMessage: message,
    });
  }
}

export function isApiError(err: unknown): err is ApiError {
  if (err instanceof ApiError) return true;
  if (err && typeof err === "object" && "_isApiError" in err && (err as any)._isApiError === true) {
    return true;
  }
  return false;
}
