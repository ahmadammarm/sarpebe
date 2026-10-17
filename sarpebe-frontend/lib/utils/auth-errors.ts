/** Error codes `authorize()` throws; they come back to the login form as `signIn()`'s `error`. */
export const AUTH_ERRORS = {
  invalidCredentials: "INVALID_CREDENTIALS",
  emailNotVerified: "EMAIL_NOT_VERIFIED",
  tooManyAttempts: "TOO_MANY_ATTEMPTS",
  serverError: "SERVER_ERROR",
} as const;
