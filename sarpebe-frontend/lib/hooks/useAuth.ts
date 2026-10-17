"use client";

import { useMutation } from "@tanstack/react-query";
import {
  forgotPassword,
  registerAccount,
  resendVerification,
  resetPassword,
  verifyEmail,
} from "@/lib/api/auth";
import type { ResetPasswordInput } from "@/lib/utils/validators";

export function useRegister() {
  return useMutation({ mutationFn: registerAccount });
}

export function useVerifyEmail() {
  return useMutation({ mutationFn: verifyEmail });
}

export function useResendVerification() {
  return useMutation({ mutationFn: resendVerification });
}

export function useForgotPassword() {
  return useMutation({ mutationFn: forgotPassword });
}

export function useResetPassword(token: string) {
  return useMutation({ mutationFn: (input: ResetPasswordInput) => resetPassword(token, input) });
}
