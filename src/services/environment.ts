export const localHelperPage=['127.0.0.1','localhost'].includes(location.hostname)&&location.port==='8766';
export const staticPages = import.meta.env.VITE_STATIC_PAGES === '1';
