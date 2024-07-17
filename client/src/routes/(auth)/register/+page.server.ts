
import { fail, redirect } from '@sveltejs/kit'                      // utility function from SvelteKit
import type { Action, Actions, PageServerLoad } from './$types'     // types from SvelteKit:
                                                                    // Action is a single handler, Actions for multiple
import bcrypt from 'bcrypt'                                         // bcrypt library for hash encoding
// import { v4 as uuidv4 } from 'uuid'
import crypto from 'crypto'

import { API_ENDPOINTS, constructUrl } from '$lib/utils/api';



// const variable "load", with type "PageServerLoad" in async function 
// keep detecting locals acorss pages, e.g. if already login, and you go to url http://localhost:5000/register
// or you accidently click the register button, you will be take to '/'
export const load: PageServerLoad = async ({ locals }) => {
    if (locals.user) {
        throw redirect(302, '/')
    }
}


// register function, conforms to Action type. 
// think of the ({}) here as the bracket when you define function in python,
// so "request" is the parameter passed in
const register: Action = async ({ request }) => {
    const data = await request.formData()   // async function only excute until the stuff await after detected
                                            // in this case, when request form is submited in the frontend
    const username = data.get("username")
    const password = data.get("password")
    // get the role as well 
    const role = data.get("role")

    // checking, make sure there are valid, and are strings
    if (
        typeof username !== 'string' || 
        typeof password !== 'string' ||
        typeof role !== 'string' ||
        !username ||
        !password ||
        !role
    ) {
        return fail(400, { invalid: true })
    }

    // you can send frontend input through url for flask to use args.get(),
    // but don't send sensitive data through url "192.168.110.131"
    
    // create endpoint for natching user with username
    const matching_url = constructUrl(API_ENDPOINTS.MATCH, { username: username });
    const response = await fetch(matching_url);   // default request GET if not specify
    const result = await response.json();
    

    // if user exist, user: true, then indicate existence; if not pass this function
    if (result.username) {
        console.log("user exist")
        return fail(400, { userExist: true })
    }


    // hash your password
    // const hashedPassword = await bcrypt.hash(password, 10);
    // create user authentication token 
    const userAuthToken = await crypto.randomUUID();

    // create endpoint, for register
    const newUser = await fetch(API_ENDPOINTS.REGISTER, {
        method: 'POST',
        headers: {                                      // if don't specify the headers,
            'Content-Type': 'application/json',         // the server may parse the data as plain text, not json. 
        },                                              // on backend, data = request.json will return "None" 
        body: JSON.stringify({                          // convert it into json format, which is good for server and client
            username: username, 
            password: password,
            role: role,
            authToken: userAuthToken
        }), 
    });


    // todo: double check if the POST request is working fine, new type serverError
    if (!newUser.ok) {
        return fail(500, { serverError: true })
    }

    // todo: determine whether a newly register user should be ADMIN or just USER
    // 1) email verification with valid or invalid reponse for backend to react 
    // 2) Role-Based access control (RBAC)
    // right now I only force specific username to admin or users
    

    throw redirect(303, '/login')

}


// export means to make stuff after available for other files to import them
// export an object named 'actions'(a set of action handler) that contains the a 'register' action defined above
export const actions: Actions = { register }






// --------------------------------------- FILE BASED ROUTING ---------------------------------------
// file-base routing (what is this even mean?):
// 1) name your client file(+page.svelte) and server file(+page.server.ts) in specific convention
// 2) client file will automatically checking and receiving export data from server file 
// 3) just need to add Load function (take in PageServerLoad type) to make it work
// 4) export them, the cilent file have the following then you can use 
// <script lang="ts">
//     export let data: { 
//         images: Array<{ file_path: string, file_name: string, reference_no: string }>
//         users: Array<{ username: string, password: string }>
//     };
// </script>
// --------------------------------------- (GROUPs) ---------------------------------------
// groups are feature in svelte, basically directory, but don't create routes(url)
// (auth)
// (protected), make your route protected
//
