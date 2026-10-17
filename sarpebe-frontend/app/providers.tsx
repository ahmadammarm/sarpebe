"use client";

import { SessionProvider, signOut, useSession } from "next-auth/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";

// Re-check the session periodically so the access token is renewed before it expires,
// even if the user keeps a tab open without interacting.
const SESSION_REFETCH_SECONDS = 4 * 60;

/** Signs the user out once the backend refuses to renew their session. */
function SessionGuard() {
  const { data: session } = useSession();
  const sessionError = session?.error;

  useEffect(() => {
    if (sessionError === "RefreshAccessTokenError") {
      void signOut({ callbackUrl: "/login" });
    }
  }, [sessionError]);

  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  return (
    <SessionProvider refetchInterval={SESSION_REFETCH_SECONDS}>
      <QueryClientProvider client={queryClient}>
        <SessionGuard />
        {children}
      </QueryClientProvider>
    </SessionProvider>
  );
}
