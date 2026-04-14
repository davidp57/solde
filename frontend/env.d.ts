/// <reference types="vite/client" />

interface ImportMetaEnv {
	readonly VITE_DEV_AUTO_LOGIN?: string
	readonly VITE_DEV_AUTO_LOGIN_USERNAME?: string
	readonly VITE_DEV_AUTO_LOGIN_PASSWORD?: string
}

interface ImportMeta {
	readonly env: ImportMetaEnv
}
