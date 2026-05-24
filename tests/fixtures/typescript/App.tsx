import React from "react";

export interface AppProps {
  title: string;
}

export function App({ title }: AppProps) {
  return <div>{title}</div>;
}

export default App;
