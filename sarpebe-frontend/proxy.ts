import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";

// Proteksi rute berbasis autentikasi dan peran (Role-Based Access Control)
export default withAuth(
  function middleware(req) {
    const token = req.nextauth.token;
    const pathname = req.nextUrl.pathname;

    // Rute /curriculum hanya boleh diakses oleh pengguna dengan role 'admin'
    if (pathname.startsWith("/curriculum")) {
      const role = (token as any)?.role;
      if (role !== "admin") {
        const redirectUrl = new URL("/lesson-plans", req.url);
        redirectUrl.searchParams.set("error", "unauthorized_admin");
        return NextResponse.redirect(redirectUrl);
      }
    }

    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token }) => !!token,
    },
    pages: {
      signIn: "/login",
    },
  }
);

// Tentukan rute yang wajib melewati filter autentikasi dan otorisasi
export const config = {
  matcher: [
    "/lesson-plans/:path*",
    "/curriculum/:path*"
  ],
};
