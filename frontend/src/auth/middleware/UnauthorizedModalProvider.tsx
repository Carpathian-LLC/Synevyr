"use client";

import { useEffect, useState } from "react";
import UnauthorizedDebugModal from "./UnauthorizedDebugModal";
import { registerUnauthorizedModalSetter } from "./unauthorizedModalTrigger";

export default function UnauthorizedModalProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [state, setState] = useState<{ path: string; status: number } | null>(
    null
  );

  useEffect(() => {
    registerUnauthorizedModalSetter(setState);
  }, []);

  return (
    <>
      {state && (
        <UnauthorizedDebugModal
          path={state.path}
          status={state.status}
          onClose={() => setState(null)}
        />
      )}
      {children}
    </>
  );
}
