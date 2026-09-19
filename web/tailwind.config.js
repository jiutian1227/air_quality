/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,vue}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        surface: "var(--bg-primary)",
        "surface-secondary": "var(--bg-secondary)",
        card: "var(--bg-card)",
        elevated: "var(--bg-elevated)",
        ink: "var(--text-primary)",
        "ink-secondary": "var(--text-secondary)",
        "ink-tertiary": "var(--text-tertiary)",
        line: "var(--border-color)",
        "line-light": "var(--border-light)",
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
      },
      boxShadow: {
        glow: "var(--shadow-glow)",
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-out",
        "slide-in": "slideIn 0.3s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideIn: {
          "0%": { opacity: "0", transform: "translateX(-12px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
      },
    },
  },
  plugins: [],
};
