"use client";
import { useState, useEffect } from "react";
import Script from "next/script";
import Link from "next/link";

const ConsentBanner = () => {
  const [consent, setConsent] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const storedConsent = localStorage.getItem("cookieConsent");
    if (storedConsent) {
      setConsent(storedConsent);
    }
    setIsLoaded(true);
  }, []);

  const handleAccept = () => {
    localStorage.setItem("cookieConsent", "accepted");
    setConsent("accepted");
  };

  const handleDecline = () => {
    localStorage.setItem("cookieConsent", "declined");
    setConsent("declined");
  };

  if (!isLoaded) return null;

  return (
    <>
      {consent === null && (
        <div className="fixed bottom-0 left-0 right-0 p-4 flex items-center justify-between gap-3
                        backdrop-blur-md bg-slate-900/70 border-t border-white/20 shadow-md z-50 
                        dark:bg-slate-900/40">
          <div className="text-white text-left max-w-xl text-sm">
            <h2 className="text-lg font-bold mb-1">🥠 Your Fortune: Good Things Come to Those Who Accept Cookies</h2>
            <p className="mb-1">
            We use cookies to make sure pages load properly, track issues, analyze traffic, and personalize content.
            By clicking &quot;Accept&quot; you&apos;re agreeing to let the cookies do their job :)
            </p>
            <p> See our <Link href="/privacy" className="underline">Privacy Policy</Link> for details.</p>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={handleAccept} 
              className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
            >
              Accept
            </button>
            <button 
              onClick={handleDecline} 
              className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
            >
              Decline
            </button>
          </div>
        </div>
      )}

      {consent === "accepted" && (
        <>
          <Script
            async
            src="https://www.googletagmanager.com/gtag/js?id=G-RL80S45GTX"
            strategy="afterInteractive"
          />
          <Script id="google-analytics" strategy="afterInteractive">
            {`
              window.dataLayer = window.dataLayer || [];
              function gtag(){ window.dataLayer.push(arguments); }
              gtag('js', new Date());
              gtag('config', 'G-RL80S45GTX');
            `}
          </Script>
        </>
      )}
    </>
  );
};

export default ConsentBanner;
