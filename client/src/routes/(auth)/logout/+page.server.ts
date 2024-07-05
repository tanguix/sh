

// eat the cookies, and redirect user from backend. so not +page.svelte need for logout for now 
import { redirect } from "@sveltejs/kit"
import type { Actions, PageServerLoad } from './$types'

export const load: PageServerLoad = async () => {
    throw redirect(302, '/')
}

// set old cookies to empty string, and broadcast to all path, and set right now for expire date
// but it can't clear the cookies when you access the web application through http://192.168.110.131:3000/, you can start debugging from here
// not just cellphone, I tried it on the host machine as well. just need to find ways to clear the cookies, and all set. Check back if any code went wrong. Basically you can delete it by opening the inspect, and manually delete it
// but how it that happen? if you access through http://192.168.110.131:3000/, and delete it, it will regenerate a new one?
export const actions: Actions = {
    default({ cookies }) {
        cookies.set('session', '', {
            path: '/',
            expires: new Date(0),
            secure: process.env.NODE_ENV === 'production',
        })

        throw redirect(302, '/login')
    },
}
