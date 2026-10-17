"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useVerifyEmail } from "@/lib/hooks/useAuth";
import { getErrorMessage } from "@/lib/utils/errors";

export function VerifyEmailStatus() {
  const token = useSearchParams().get("token");
  const verify = useVerifyEmail();
  const { mutate } = verify;
  // React strict mode runs effects twice in development; a link must only be redeemed once.
  const requested = useRef(false);

  useEffect(() => {
    if (token && !requested.current) {
      requested.current = true;
      mutate(token);
    }
  }, [token, mutate]);

  if (!token || verify.isError) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <CardTitle>Verification failed</CardTitle>
          <CardDescription>
            {token
              ? getErrorMessage(verify.error, "This verification link is invalid or has expired.")
              : "This link is missing its token."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-gray-600 text-center">
          <p>Sign in to request a new verification email.</p>
          <Link href="/login">
            <Button className="w-full">Go to Sign In</Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  if (verify.isSuccess) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <CardTitle>Email verified</CardTitle>
          <CardDescription>Your account is ready to use</CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/login">
            <Button className="w-full">Sign In</Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle>Verifying your email...</CardTitle>
        <CardDescription>This only takes a moment</CardDescription>
      </CardHeader>
    </Card>
  );
}
