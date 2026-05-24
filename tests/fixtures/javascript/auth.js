import React from "react";
import { useMemo } from "react";

export class AuthService {
  verify(token) {
    return Boolean(token);
  }
}

export const fetchUser = async (id) => id;

export function useAuth() {
  return useMemo(() => null, []);
}

export default function App() {
  return React.createElement("div", null, "ok");
}

const ArrowHelper = () => null;
