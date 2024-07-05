

// if user are not login, or don't have access to admin, and they enter localhost:5000/admin 
// we need to redirec them to honme page 

import { redirect } from '@sveltejs/kit'
import type { PageServerLoad }  from './$types'

export const load: PageServerLoad = async ({ locals }) => {
    // console.log(locals.user)
    // console.log(locals.user.role)
    // first check if user login or not
    if (!locals.user) {
        throw redirect(302, '/')
    }
    // then check if user's identity, later you can create a 404 page, or maybe 9829 page I don't know to redirect
    if (locals.user.role !== "ADMIN") {
        // maybe redirect or pring something for warnings in the frontend
        throw redirect(404, '/')
    }
}
