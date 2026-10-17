// Kept free of "use client" so the root layout (a server component) can import the string.

export const THEME_STORAGE_KEY = "sarpebe-theme";

/**
 * Runs in <head> before first paint so the page never flashes the wrong theme.
 * Saved choice first, then the OS preference.
 */
export const themeInitScript = `(function(){try{var t=localStorage.getItem("${THEME_STORAGE_KEY}");if(t!=="light"&&t!=="dark"){t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}document.documentElement.dataset.theme=t}catch(e){document.documentElement.dataset.theme="light"}})()`;
