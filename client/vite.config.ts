import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
    server: {
        host: '0.0.0.0',    // expose to the local network
        port: 3000          // force the port to be on 3000
    }
});
