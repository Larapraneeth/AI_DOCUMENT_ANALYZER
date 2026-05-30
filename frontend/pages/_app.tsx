import type { AppProps } from "next/app";
import { Toaster } from "react-hot-toast";
import "../styles/globals.css";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: "#fff",
            color: "#333",
            border: "1px solid #DDE3EC",
            fontSize: "13px",
          },
          success: { iconTheme: { primary: "#1B7A3A", secondary: "#fff" } },
          error:   { iconTheme: { primary: "#C0392B", secondary: "#fff" } },
        }}
      />
      <Component {...pageProps} />
    </>
  );
}
