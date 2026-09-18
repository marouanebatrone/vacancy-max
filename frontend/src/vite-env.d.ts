/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Origin of the API in production, e.g. https://vacancy-max-api.onrender.com */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
