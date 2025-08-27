// app/settings/page.tsx
import { redirect } from "next/navigation";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Settings | Carpathian",
  description: "Manage your account preferences, security, notifications, billing, and support options.",
};

export default function SettingsIndex() {
  // Immediately send users to the account tab
  redirect("/dashboard/settings/account");
}
