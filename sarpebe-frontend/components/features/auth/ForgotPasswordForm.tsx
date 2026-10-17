"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { forgotPasswordSchema, zodFieldErrors } from "@/lib/utils/validators";
import { useForgotPassword } from "@/lib/hooks/useAuth";
import { getErrorMessage } from "@/lib/utils/errors";

export function ForgotPasswordForm() {
  const forgotPassword = useForgotPassword();
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState<string | undefined>();
  const [globalError, setGlobalError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setEmailError(undefined);
    setGlobalError("");

    const parsed = forgotPasswordSchema.safeParse({ email });
    if (!parsed.success) {
      setEmailError(zodFieldErrors<"email">(parsed.error).email);
      return;
    }

    try {
      await forgotPassword.mutateAsync(parsed.data);
    } catch (error) {
      setGlobalError(getErrorMessage(error, "Could not send the reset link. Please try again."));
    }
  };

  if (forgotPassword.isSuccess) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <CardTitle>Check your email</CardTitle>
          <CardDescription>Password reset instructions</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-gray-600">
          <p>
            If an account exists for <strong>{email}</strong>, we have sent a link to reset its password.
            The link expires in one hour.
          </p>
          <Link href="/login" className="block text-center text-blue-600 hover:underline">Back to Sign In</Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle>Forgot your password?</CardTitle>
        <CardDescription>Enter your email and we will send you a reset link</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="teacher@school.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={emailError ? "border-destructive" : ""}
            />
            {emailError && <p className="text-sm font-medium text-destructive mt-1">{emailError}</p>}
          </div>

          {globalError && (
            <div className="text-sm font-medium text-red-500 bg-red-50 p-3 rounded-md" role="alert">
              {globalError}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={forgotPassword.isPending}>
            {forgotPassword.isPending ? "Sending..." : "Send reset link"}
          </Button>

          <div className="text-center text-sm mt-4 text-gray-600">
            <Link href="/login" className="text-blue-600 hover:underline">Back to Sign In</Link>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
