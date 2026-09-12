"use client";

import { useSession, signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";

export function LessonPlanDashboard() {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return <div className="p-8">Loading session...</div>;
  }

  if (status === "unauthenticated") {
    return <div className="p-8">Access Denied. Please log in.</div>;
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">Lesson Plans Dashboard</h1>
      <p className="mb-6 text-gray-600">
        Welcome, <strong>{session?.user?.name || session?.user?.email}</strong>! You are authenticated.
      </p>

      <Button onClick={() => signOut({ callbackUrl: "/login" })} variant="destructive">
        Log Out
      </Button>
    </div>
  );
}
