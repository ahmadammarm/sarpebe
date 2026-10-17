"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { registerSchema, RegisterFormData, zodFieldErrors } from "@/lib/utils/validators";
import { useRegister } from "@/lib/hooks/useAuth";
import { getErrorMessage } from "@/lib/utils/errors";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

export function RegisterForm() {
  const register = useRegister();
  const [formData, setFormData] = useState<RegisterFormData>({ fullName: "", email: "", password: "" });
  const [errors, setErrors] = useState<Partial<RegisterFormData>>({});
  const [globalError, setGlobalError] = useState("");
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setGlobalError("");

    const parsed = registerSchema.safeParse(formData);
    if (!parsed.success) {
      setErrors(zodFieldErrors(parsed.error));
      return;
    }

    try {
      await register.mutateAsync(parsed.data);
      setRegisteredEmail(parsed.data.email);
    } catch (error) {
      setGlobalError(getErrorMessage(error, "Could not create the account. Please try again."));
    }
  };

  if (registeredEmail) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <CardTitle>Check your email</CardTitle>
          <CardDescription>One more step to activate your account</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-gray-600">
          <p>
            If <strong>{registeredEmail}</strong> can be registered, we have sent a verification link to it.
            Open the link, then sign in.
          </p>
          <p>
            Already have an account with this email? You can{" "}
            <Link href="/forgot-password" className="text-blue-600 hover:underline">reset your password</Link>.
          </p>
          <Link href="/login" className="block text-center text-blue-600 hover:underline">Back to Sign In</Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle>Create an Account</CardTitle>
        <CardDescription>Get started with SARPEBE</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label htmlFor="fullName">Full Name</Label>
            <Input
              id="fullName"
              autoComplete="name"
              placeholder="Jane Doe"
              value={formData.fullName}
              onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
              className={errors.fullName ? "border-destructive" : ""}
            />
            {errors.fullName && <p className="text-sm font-medium text-destructive mt-1">{errors.fullName}</p>}
          </div>
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
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className={errors.password ? "border-destructive" : ""}
            />
            {errors.password ? (
              <p className="text-sm font-medium text-destructive mt-1">{errors.password}</p>
            ) : (
              <p className="text-xs text-gray-500">At least 8 characters.</p>
            )}
          </div>

          {globalError && (
            <div className="text-sm font-medium text-red-500 bg-red-50 p-3 rounded-md" role="alert">
              {globalError}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={register.isPending}>
            {register.isPending ? "Signing Up..." : "Sign Up"}
          </Button>

          <div className="text-center text-sm mt-4 text-gray-600">
            Already have an account? <Link href="/login" className="text-blue-600 hover:underline">Sign In</Link>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
