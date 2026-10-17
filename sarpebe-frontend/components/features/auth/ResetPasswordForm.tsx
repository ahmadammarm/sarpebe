"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { resetPasswordSchema, ResetPasswordInput, zodFieldErrors } from "@/lib/utils/validators";
import { useResetPassword } from "@/lib/hooks/useAuth";
import { getErrorMessage } from "@/lib/utils/errors";

export function ResetPasswordForm() {
  const token = useSearchParams().get("token") ?? "";
  const resetPassword = useResetPassword(token);
  const [formData, setFormData] = useState<ResetPasswordInput>({ password: "", confirmPassword: "" });
  const [errors, setErrors] = useState<Partial<ResetPasswordInput>>({});
  const [globalError, setGlobalError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setGlobalError("");

    const parsed = resetPasswordSchema.safeParse(formData);
    if (!parsed.success) {
      setErrors(zodFieldErrors(parsed.error));
      return;
    }

    try {
      await resetPassword.mutateAsync(parsed.data);
    } catch (error) {
      setGlobalError(getErrorMessage(error, "Could not reset the password. Please try again."));
    }
  };

  if (!token) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <CardTitle>Invalid reset link</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-gray-600">
          <p>This link is missing its token. Request a new one.</p>
          <Link href="/forgot-password" className="block text-center text-blue-600 hover:underline">
            Request a new link
          </Link>
        </CardContent>
      </Card>
    );
  }

  if (resetPassword.isSuccess) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <CardTitle>Password updated</CardTitle>
          <CardDescription>You have been signed out of all devices</CardDescription>
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
        <CardTitle>Choose a new password</CardTitle>
        <CardDescription>Use at least 8 characters</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label htmlFor="password">New password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className={errors.password ? "border-destructive" : ""}
            />
            {errors.password && <p className="text-sm font-medium text-destructive mt-1">{errors.password}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm new password</Label>
            <Input
              id="confirmPassword"
              type="password"
              autoComplete="new-password"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              className={errors.confirmPassword ? "border-destructive" : ""}
            />
            {errors.confirmPassword && (
              <p className="text-sm font-medium text-destructive mt-1">{errors.confirmPassword}</p>
            )}
          </div>

          {globalError && (
            <div className="text-sm font-medium text-red-500 bg-red-50 p-3 rounded-md space-y-2" role="alert">
              <p>{globalError}</p>
              <Link href="/forgot-password" className="text-blue-600 hover:underline">Request a new link</Link>
            </div>
          )}

          <Button type="submit" className="w-full" disabled={resetPassword.isPending}>
            {resetPassword.isPending ? "Saving..." : "Update password"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
