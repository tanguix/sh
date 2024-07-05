// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		interface Locals {      // creating variable for event locals to use
            user: {
                name: string 
                role: string
            }
        }
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
