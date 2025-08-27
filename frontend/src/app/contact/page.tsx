// app/contact/page.tsx
import { Metadata } from "next";
import ContactClient from "./ContactClient";

export const metadata: Metadata = {
  title: "Contact Carpathian | Open Technology ⚡︎ Limitless Possibilities",
  description: "Ask Carpathian a question, get information or support on issues.",
      alternates: {
    canonical: "https://carpathian.ai/contact",
  },
};

export default function ContactPage() {
  return <ContactClient />;
}
