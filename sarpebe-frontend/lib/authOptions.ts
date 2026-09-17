import { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { createClient } from "@supabase/supabase-js";
import axios from "axios";

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
          return null;
        }

        const supabase = createClient(
          process.env.NEXT_PUBLIC_SUPABASE_URL as string,
          process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string
        );

        const { data, error } = await supabase.auth.signInWithPassword({
          email: credentials.email,
          password: credentials.password,
        });

        if (error || !data.user || !data.session) {
          console.error("Supabase Auth Error:", error?.message);
          return null;
        }

        const accessToken = data.session.access_token;
        let role = "user";

        // Fetch user profile from backend to get accurate role
        try {
          const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
          const res = await axios.get(`${apiBaseUrl}/api/users/me`, {
            headers: { Authorization: `Bearer ${accessToken}` },
          });
          if (res.data?.role) {
            role = res.data.role;
          }
        } catch (e) {
          console.warn("Could not fetch user profile role from backend, defaulting to 'user':", (e as any)?.message);
        }

        return {
          id: data.user.id,
          email: data.user.email,
          name: data.user.user_metadata?.full_name || "Educator",
          role,
          access_token: accessToken,
        } as any;
      }
    })
  ],
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = (user as any).role || "user";
        token.accessToken = (user as any).access_token;
      }
      return token;
    },
    async session({ session, token }) {
      if (token) {
        (session.user as any).id = token.id;
        (session.user as any).role = token.role || "user";
        (session as any).supabaseAccessToken = token.accessToken;
      }
      return session;
    },
  },
  pages: {
    signIn: "/login",
  }
};
