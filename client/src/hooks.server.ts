

// ======================================== my understanding of cookies for now ========================================
// 1) frontend and backend are separated, so data stored on each of them could be different 
// 2) there are data you don't always needed from database, or it's repeative if different +page makes same API request
// 3) so you can use cookies (which is on client side, for small size data; session on the server side for larger file)
// 4) in svelte you can have load function to access event (local method) on current page, and that's when you use cookies to access 
// 5) Hooks method is how you can do that in svelte, like men in the middle between different pages
// 6) basically, in network flow, I guess you use cookies id and session id to identify users

import type { Handle } from '@sveltejs/kit'

export const handle: Handle = async ({ event, resolve }) => {
    const session = event.cookies.get('session') // get current page session, actually it's cookies, just with name session

    if (!session) {
        return await resolve(event)    // if sesssion doesn't exist, load page as normal
    }

    // API calls: user session to identify user, and get their role, 
    // replace localhost with real backend address for deployment "192.168.110.131"
    // const response = await fetch(`http://192.168.110.131:5000/api/match_token?authToken=${session}`);
    const response = await fetch(`http://localhost:5000/auth/api/match_token?authToken=${session}`);
    const result = await response.json(); // getting back json object with {_id, username, password, token, role}
    // console.log("USER EXIST?", result)

    // if user exist, then set 'events.local'
    // to make local recognize user variable, define it in app.d.ts
    // like this:
    // declare global {
    //     namespace App {
    //         // interface Error {}
    //         interface Locals {
    //             user: {
    //                 name: string 
    //                 role: string
    //             }
    //         }
    //         // interface PageData {}
    //         // interface PageState {}
    //         // interface Platform {}
    //     }
    // }
    if (result.username) {
        event.locals.user = {
            name: result.username,
            role: result.role,
        }
    }

    return await resolve(event)

}
