

// since +layout.server.ts will be able to affect every page, so make sure page load variable, 
// and locals behavior is defined here, so you can use it on the client

import type { LayoutServerLoad } from './$types'

export const load: LayputServerLoad = async ({ locals }) => {
    // console.log(locals)
    return {
        user: locals.user
    }
}
