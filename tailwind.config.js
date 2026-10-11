/** Every colour comes from a CSS variable token (static/src/tokens.css). Never hardcode colours in templates. */
const rgb = (name) => `rgb(var(--${name}) / <alpha-value>)`;

module.exports = {
  darkMode: ["class", '[data-theme="dark"]'],
  content: ["./templates/**/*.html", "./apps/**/templates/**/*.html", "./static/js/**/*.js", "./apps/**/*.py"],
  theme: {
    extend: {
      colors: {
        base: rgb("bg-base"),
        raised: rgb("bg-raised"),
        sunken: rgb("bg-sunken"),
        line: rgb("border-subtle"),
        ink: rgb("text-primary"),
        mute: rgb("text-secondary"),
        water: rgb("accent-water"),
        laterite: rgb("accent-laterite"),
        leaf: rgb("accent-leaf"),
        skip: rgb("signal-skip"),
        watch: rgb("signal-watch"),
        stress: rgb("signal-stress"),
        onaccent: rgb("on-accent"),
        chart: { 1: rgb("chart-1"), 2: rgb("chart-2"), 3: rgb("chart-3"), 4: rgb("chart-4") },
      },
      fontFamily: {
        display: ["var(--font-display)"],
        sans: ["var(--font-sans)"],
        mono: ["var(--font-mono)"],
      },
      borderRadius: { sm: "6px", md: "10px", lg: "16px", xl: "24px" },
      spacing: { 4.5: "18px" },
      boxShadow: {
        raised: "var(--elev-1)",
        float: "var(--elev-2)",
        sheet: "var(--elev-3)",
      },
      zIndex: { nav: "var(--z-nav)", sheet: "var(--z-sheet)", palette: "var(--z-palette)", toast: "var(--z-toast)" },
      maxWidth: { prose: "66ch" },
      minHeight: { touch: "44px" },
      minWidth: { touch: "44px" },
      keyframes: {
        shimmer: { "100%": { transform: "translateX(100%)" } },
        breathe: { "0%,100%": { opacity: "0.55", transform: "scale(1)" }, "50%": { opacity: "1", transform: "scale(1.15)" } },
        drift: { "0%,100%": { transform: "translate3d(0,0,0)" }, "50%": { transform: "translate3d(2%,-2%,0)" } },
      },
      animation: {
        shimmer: "shimmer 2.4s ease-in-out infinite",
        breathe: "breathe 2.8s ease-in-out infinite",
        drift: "drift 18s ease-in-out infinite",
      },
    },
  },
  plugins: [require("@tailwindcss/forms")({ strategy: "class" })],
};
