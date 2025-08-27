"use client";

import { useRouter } from "next/navigation";

export default function GoBackButton() {
  const router = useRouter();

  return (
    <button
      onClick={() => router.back()}
      className="mt-6 px-6 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 transition"
    >
      Go Back
    </button>
  );
}
