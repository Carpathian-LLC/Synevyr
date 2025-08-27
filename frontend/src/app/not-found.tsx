import { Suspense } from "react";
import Terminal404 from "@/components/Terminal404Client";

export default function NotFoundPage() {
  return (
    <Suspense fallback={<div className="text-center text-white p-8">Loading terminal…</div>}>
      <Terminal404 />
    </Suspense>
  );
}
