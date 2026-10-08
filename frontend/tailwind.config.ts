import type { Config } from "tailwindcss";
export default { content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"], theme: { extend: { colors: { ink: "#14201d", canvas: "#f6f7f4", teal: "#087f6a", line: "#dce3de" } } }, plugins: [] } satisfies Config;
