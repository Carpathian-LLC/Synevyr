// app/company/page.tsx
import { Metadata } from "next";
import CompanyClient from "./CompanyClient";

export const metadata: Metadata = {
  title: "Company | Open Technology ⚡︎ Limitless Possibilities",
  description: "Learn more about Synevyr and who we serve.",
    alternates: {
    canonical: "https://synevyr.org/company",
  },
};

export default function CompanyPage() {
  return <CompanyClient />;
}
