
import { fail, redirect } from '@sveltejs/kit'
import bcrypt from 'bcrypt'
import type { Action, Actions, PageServerLoad } from './$types'
import { API_ENDPOINTS, constructUrl } from '$lib/utils/api.ts';


export const load: PageServerLoad = async ({ locals }) => {
    if (locals.user) {
        throw redirect(302, '/')
    }
}

const login: Action = async ({ cookies, request }) => {
    const data = await request.formData()
    const username = data.get('username')
    const password = data.get('password')

    if (
        typeof username !== 'string' ||
        typeof password !== 'string' ||
        !username ||
        !password
    ) {
        return fail(400, { notUser: true })
    }

    // match the user to the database, and return user json object
    // const response = await fetch(`http://192.168.110.131:5000/api/match?username=${username}`);
    const url = constructUrl(API_ENDPOINTS.MATCH, { username: username });
    const response = await fetch(url);
    const user_obj = await response.json();
    // console.log(user_obj)

    // check if user object return 
    if (!user_obj.username) {
        return fail(400, { notUser: true })
    }
    
    // match user password as well (later use hasdPassword match)
    // const userPassword = await bcrypt.compare(password, user_obej.hasdPassword)
    const userPassword = user_obj.password
    if (userPassword != password) {
        return fail(400, { credentials: true })
    }

    // cookie
    // generate new token each time user login, because if don't do that someone might copy you old token
    // they are basically you at that time
    const newUserAuthToken = await crypto.randomUUID();
    // and update in the database
    // if don't need to receive the response from the backend, just await fetch('http://192.168.110.131:5000/
    await fetch('http://localhost:5000/auth/api/update_authtoken', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: user_obj.username, 
            authToken: newUserAuthToken
        }), 
    });

    // when you clear the cookies, you should have the same setup like this(at least, path and secure)
    cookies.set('session', newUserAuthToken, {
        // send cookie for every page 
        path: '/',
        // server side only cookie so you can't use 'document.cookie'
        httpOnly: true,
        // only requests from same site can send cookies 
        // https://developer.mozilla.org/en-US/docs/Glossary/CSRF
        sameSite: 'strict',
        // only send over HTTPS in production, 
        secure: process.env.NODE_ENV === 'production',
        // secure: false,
        // set cookies to expire after a month (secs * mins * hours * days)
        maxAge: 60 * 60 * 24 * 30,

    })

    redirect(302, '/')
}

export const actions: Actions = { login }
