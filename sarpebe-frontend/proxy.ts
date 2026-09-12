import { withAuth } from "next-auth/middleware";

// This middleware protects the dashboard routes and redirects unauthenticated users to /login
export default withAuth({
  pages: {
    signIn: "/login",
  },
});

// Specify the paths that require authentication
export const config = {
  matcher: [
    "/lesson-plans/:path*", 
    "/curriculum/:path*"
  ],
};
