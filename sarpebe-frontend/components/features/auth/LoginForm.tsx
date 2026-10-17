"use client";

import React, { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { loginSchema, LoginFormData, zodFieldErrors } from "@/lib/utils/validators";
import { AUTH_ERRORS } from "@/lib/utils/auth-errors";
import { useResendVerification } from "@/lib/hooks/useAuth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const LOGIN_ERROR_MESSAGES: Record<string, string> = {
  [AUTH_ERRORS.invalidCredentials]: "Invalid email or password.",
  [AUTH_ERRORS.emailNotVerified]: "Your email address has not been verified yet.",
  [AUTH_ERRORS.tooManyAttempts]: "Too many failed attempts. Please wait a few minutes and try again.",
  [AUTH_ERRORS.serverError]: "Could not reach the server. Please try again.",
};

export function LoginForm() {
  const router = useRouter();
  const resendVerification = useResendVerification();
  const [formData, setFormData] = useState<LoginFormData>({ email: "", password: "" });
  const [errors, setErrors] = useState<Partial<LoginFormData>>({});
  const [loginError, setLoginError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const needsVerification = loginError === AUTH_ERRORS.emailNotVerified;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setLoginError(null);
    resendVerification.reset();

    const parsed = loginSchema.safeParse(formData);
    if (!parsed.success) {
      setErrors(zodFieldErrors(parsed.error));
      return;
    }

    setIsLoading(true);
    try {
      const res = await signIn("credentials", {
        redirect: false,
        email: parsed.data.email,
        password: parsed.data.password,
      });

      if (res?.error) {
        setLoginError(res.error in LOGIN_ERROR_MESSAGES ? res.error : AUTH_ERRORS.serverError);
      } else {
        router.push("/lesson-plans");
        router.refresh();
      }
    } catch {
      setLoginError(AUTH_ERRORS.serverError);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle>Welcome Back</CardTitle>
        <CardDescription>Sign in to your SARPEBE account</CardDescription>
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
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className={errors.email ? "border-destructive" : ""}
            />
            {errors.email && <p className="text-sm font-medium text-destructive mt-1">{errors.email}</p>}
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Password</Label>
              <Link href="/forgot-password" className="text-sm text-blue-600 hover:underline">
                Forgot password?
              </Link>
            </div>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className={errors.password ? "border-destructive" : ""}
            />
            {errors.password && <p className="text-sm font-medium text-destructive mt-1">{errors.password}</p>}
          </div>

          {loginError && (
            <div className="text-sm font-medium text-red-500 bg-red-50 p-3 rounded-md space-y-2" role="alert">
              <p>{LOGIN_ERROR_MESSAGES[loginError]}</p>
              {needsVerification && !resendVerification.isSuccess && (
                <button
                  type="button"
                  className="text-blue-600 hover:underline disabled:opacity-50"
                  disabled={resendVerification.isPending}
                  onClick={() => resendVerification.mutate(formData.email)}
                >
                  {resendVerification.isPending ? "Sending..." : "Resend verification email"}
                </button>
              )}
            </div>
          )}

          {resendVerification.isSuccess && (
            <div className="text-sm font-medium text-green-700 bg-green-50 p-3 rounded-md" role="status">
              If your account is waiting for verification, a new link is on its way. Check your inbox.
            </div>
          )}

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? "Signing In..." : "Sign In"}
          </Button>

          <div className="text-center text-sm mt-4 text-gray-600">
            Don&apos;t have an account? <Link href="/register" className="text-blue-600 hover:underline">Sign Up</Link>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
