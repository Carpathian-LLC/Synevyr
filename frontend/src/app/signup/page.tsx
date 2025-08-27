// src/app/signup/page.tsx
import { Suspense } from "react"
import SignupForm from "./SignupForm"

export default function SignupPage() {
  return (
    <Suspense fallback={<div className="text-center py-20">Loading form...</div>}>
      <SignupForm />
    </Suspense>
  )
}
