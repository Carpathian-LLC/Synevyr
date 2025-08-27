// app/login/page.tsx
import { Metadata } from "next";
import LoginClient from "./LoginClient";

export const metadata: Metadata = {
  title: "Login | Open Technology ⚡︎ Limitless Possibilities",
  description: "Login to your Carpathian Cloud Manager account.",
};

export default function LoginPage() {
  return <LoginClient />;
}
