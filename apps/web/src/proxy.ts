import { clerkMiddleware } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import type { NextRequest, NextFetchEvent } from "next/server";
import { isClerkServerConfigured, publicOrigin } from "@/lib/config";
const middleware = clerkMiddleware({
  signInUrl: "/login",
  signUpUrl: "/signup",
  authorizedParties: [publicOrigin],
});
export default function proxy(request: NextRequest, event: NextFetchEvent) {
  if (!isClerkServerConfigured) return NextResponse.next();
  return middleware(request, event);
}
export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|map)).*)",
    "/api/(.*)",
  ],
};
