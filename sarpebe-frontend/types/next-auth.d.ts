import type { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    user: DefaultSession["user"] & {
      id: string;
      role: string;
    };
    accessToken?: string;
    /** Set to "RefreshAccessTokenError" when the session can no longer be renewed. */
    error?: string;
  }

  interface User {
    role?: string;
    accessToken?: string;
    refreshToken?: string;
    /** Epoch milliseconds. */
    accessTokenExpires?: number;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id?: string;
    role?: string;
    accessToken?: string;
    refreshToken?: string;
    accessTokenExpires?: number;
    error?: string;
  }
}
