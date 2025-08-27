// app/pricing/page.tsx
import { Metadata } from "next";
import PricingClient from "./PricingClient";

export const metadata: Metadata = {
  title: "Pricing | Open Technology ⚡︎ Limitless Possibilities",
  description:
    "See Carpathian's pricing for launching virtual and physical machines, or contact us for additional services.",
        alternates: {
    canonical: "https://carpathian.ai/pricing",
  },
};

export default function PricingPage() {
  return <PricingClient />;
}
