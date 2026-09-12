"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@supabase/supabase-js";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { registerSchema, RegisterFormData } from "@/lib/utils/validators";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { z } from "zod";
import Link from "next/link";

export function RegisterForm() {
  const router = useRouter();
  const [formData, setFormData] = useState<RegisterFormData>({ fullName: "", email: "", password: "" });
  const [errors, setErrors] = useState<Partial<RegisterFormData>>({});
  const [globalError, setGlobalError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setGlobalError("");
    setSuccessMsg("");
    
    try {
      registerSchema.parse(formData);
      setIsLoading(true);

      const supabase = createClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL as string,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string
      );

      const { data, error } = await supabase.auth.signUp({
        email: formData.email,
        password: formData.password,
        options: {
          data: {
            full_name: formData.fullName,
          }
        }
      });

      if (error) {
        setGlobalError(error.message);
      } else {
        setSuccessMsg("Account created! Please check your email to verify (or sign in if auto-confirm is enabled).");
        // Optionally redirect to login page after a short delay
        setTimeout(() => router.push("/login"), 3000);
      }
    } catch (error) {
      if (error instanceof z.ZodError) {
        const newErrors: any = {};
        (error as any).errors.forEach((err: any) => {
          if (err.path[0]) newErrors[err.path[0]] = err.message;
        });
        setErrors(newErrors);
      } else {
        setGlobalError("An unexpected error occurred.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle>Create an Account</CardTitle>
        <CardDescription>Get started with SARPEBE</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="fullName">Full Name</Label>
            <Input
              id="fullName"
              placeholder="John Doe"
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
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className={errors.password ? "border-destructive" : ""}
            />
            {errors.password && <p className="text-sm font-medium text-destructive mt-1">{errors.password}</p>}
          </div>
          
          {globalError && (
            <div className="text-sm font-medium text-red-500 bg-red-50 p-3 rounded-md">
              {globalError}
            </div>
          )}

          {successMsg && (
            <div className="text-sm font-medium text-green-700 bg-green-50 p-3 rounded-md">
              {successMsg}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? "Signing Up..." : "Sign Up"}
          </Button>
          
          <div className="text-center text-sm mt-4 text-gray-600">
            Already have an account? <Link href="/login" className="text-blue-600 hover:underline">Sign In</Link>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
