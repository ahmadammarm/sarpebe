import { NextAuthOptions } from "next-auth";
import type { JWT } from "next-auth/jwt";
import CredentialsProvider from "next-auth/providers/credentials";
import axios from "axios";
import { loginRequest, logoutRequest, refreshRequest } from "@/lib/api/auth";
import { AUTH_ERRORS } from "@/lib/utils/auth-errors";
import { getErrorCode } from "@/lib/utils/errors";

// Refresh a little before the access token actually expires.
const REFRESH_MARGIN_MS = 60_000;

function loginErrorCode(error: unknown): string {
  switch (getErrorCode(error)) {
    case "invalid_credentials":
      return AUTH_ERRORS.invalidCredentials;
    case "email_not_verified":
      return AUTH_ERRORS.emailNotVerified;
    case "too_many_attempts":
      return AUTH_ERRORS.tooManyAttempts;
    default:
      return AUTH_ERRORS.serverError;
  }
}

async function refreshAccessToken(token: JWT): Promise<JWT> {
  if (!token.refreshToken) {
    return { ...token, error: "RefreshAccessTokenError" };
  }

  try {
    const refreshed = await refreshRequest(token.refreshToken);
    return {
      ...token,
      accessToken: refreshed.access_token,
      refreshToken: refreshed.refresh_token,
      accessTokenExpires: Date.now() + refreshed.expires_in * 1000,
      role: refreshed.user.role,
      name: refreshed.user.full_name,
      error: undefined,
    };
  } catch (error) {
    // The backend rejected the refresh token (expired, revoked, replayed): the session is over.
    // Anything else (network blip, backend restarting) keeps the token so the next call retries.
    if (axios.isAxiosError(error) && error.response && error.response.status < 500) {
      return { ...token, error: "RefreshAccessTokenError" };
    }
    return token;
  }
}

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Email and Password",
      credentials: {
        email: { label: "Email", type: "email", placeholder: "teacher@school.com" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error(AUTH_ERRORS.invalidCredentials);
        }

        try {
          const tokens = await loginRequest(credentials.email, credentials.password);
          return {
            id: tokens.user.id,
            email: tokens.user.email,
            name: tokens.user.full_name,
            role: tokens.user.role,
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
            accessTokenExpires: Date.now() + tokens.expires_in * 1000,
          };
        } catch (error) {
          throw new Error(loginErrorCode(error));
        }
      }
    })
  ],
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async jwt({ token, user }) {
      // Initial sign-in: copy what the backend returned into the session token.
      if (user) {
        token.id = user.id;
        token.role = user.role || "user";
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        token.accessTokenExpires = user.accessTokenExpires;
        token.error = undefined;
        return token;
      }

      // A dead session stays dead until the user signs in again.
      if (token.error) return token;

      if (token.accessTokenExpires && Date.now() < token.accessTokenExpires - REFRESH_MARGIN_MS) {
        return token;
      }
      return refreshAccessToken(token);
    },
    async session({ session, token }) {
      session.user.id = token.id ?? "";
      session.user.role = token.role || "user";
      // The refresh token is intentionally not exposed to the browser.
      session.accessToken = token.accessToken;
      session.error = token.error;
      return session;
    },
  },
  events: {
    // Revoke the server-side session so a copied refresh token stops working.
    async signOut({ token }) {
      if (!token?.refreshToken) return;
      try {
        await logoutRequest(token.refreshToken);
      } catch (error) {
        console.warn("Could not revoke refresh token on sign out:", error instanceof Error ? error.message : error);
      }
    },
  },
  pages: {
    signIn: "/login",
  }
};
