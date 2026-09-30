"use client";

import { ReactNode, useEffect, useRef, useState } from "react";
import { usePlaidLink } from "react-plaid-link";

import { readError, requestAutopsy } from "@/lib/api";

export function SignIntoBank({
  onPublicToken,
  children,
}: {
  onPublicToken: (publicToken: string) => void;
  children: (state: { start: () => void; busy: boolean; error: string | null }) => ReactNode;
}) {
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const opened = useRef(false);

  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: (publicToken) => {
      if (publicToken) onPublicToken(publicToken);
    },
  });

  useEffect(() => {
    if (linkToken && ready && !opened.current) {
      opened.current = true;
      open();
    }
  }, [linkToken, ready, open]);

  async function start() {
    opened.current = false;
    setBusy(true);
    setError(null);
    try {
      const response = await requestAutopsy("/api/plaid/link-token", { method: "POST" });
      if (!response.ok) {
        setError(await readError(response));
        return;
      }
      const body = (await response.json()) as { link_token: string };
      setLinkToken(body.link_token);
    } catch {
      setError("The API isn't running. Start the backend, then try again.");
    } finally {
      setBusy(false);
    }
  }

  return children({ start: () => void start(), busy, error });
}
