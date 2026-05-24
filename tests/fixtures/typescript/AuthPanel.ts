import type { User } from "./types";

export interface PanelProps {
  userId: string;
}

export type Status = "ok" | "error";

export class AuthPanel {
  verify(userId: string): boolean {
    return userId.length > 0;
  }
}

export const loadStatus = (): Status => "ok";

export function usePanelState() {
  return { ready: true };
}
