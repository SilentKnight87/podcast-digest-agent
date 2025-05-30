"use client";

import { useState, useEffect } from "react";

/**
 * Custom hook to detect if the code is running on the client side
 * Helps prevent hydration errors with components that need client-only rendering
 */
export const useIsClient = () => {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  return isClient;
};
