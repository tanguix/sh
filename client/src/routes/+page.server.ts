

// To make the frontend automatically update when the backend data changes, there are several approaches you can take, depending on your use case and the frequency of updates required. Here are some common strategies:
// 1. Polling
// 2. WebSockets3. (example use node.js) https://www.youtube.com/watch?v=mAcKzdW5fR8
// 3. Server-Sent Events (SSE: example use node.js and express.js)
// 4. search for "Real-Time Data Synchronization"
// 5. the thing is, maybe you don't need real-time update, there are solution whenever you have some updated in the backend, it will then have a function automatically refresh the frontend, and maybe the problem is on the backend? so don't rush on this one, looking into it deeper.
// 6. write a loop to keep checking this is also a possible solution, if you don't heavily focus on latency and scalability
// resource: https://www.youtube.com/watch?v=Kzrz7GZ9pIg (Hook in svelte) | https://www.youtube.com/watch?v=rsmLu5nmh4g | https://www.youtube.com/watch?v=MoGkX4RvZ38&t=16s | https://www.youtube.com/watch?v=whEObh8waxg | https://www.youtube.com/watch?v=nDgdldBPoE0 | https://www.youtube.com/watch?v=7hXHbGj6iE0 | https://www.youtube.com/watch?v=rsmLu5nmh4g


// receive exchange rate data, and structure them 
// ======================================== old way (auto-call) =========================================
//     
//     // since you need to pay for exchange rate API, so better to not make the api calls automatically 
//     // happen in the main layout or front page, that will make it call it everytime you enter website
//     // better to make it a button, only make the call when update is needed (click)
//     // for the rest of the time, just display the rate of last call if you want
//     // but when calculating the price, you need to make calls each time you cal
// import type { PageServerLoad } from './$types';

// export const load: PageServerLoad = async () => {
//     const response = await fetch('http://localhost:5000/api/exchange_rate');
//     if (!response.ok) {
//         throw new Error('Failed to fetch users');
//     }
//     const exchange_rate = await response.json();
//     // console.log(exchange_rate)

//     return { exchange_rate };   // when you export, you have to be in the parenthses, and structured json
//                                 // on the +page.svelte, your export let should follow this return structure
// }
// ======================================== old way (auto-call) =========================================


import type { RequestHandler } from '@sveltejs/kit';

export const GET: RequestHandler = async () => {
    const response = await fetch('http://localhost:5000/extra/api/exchange_rate');
    if (!response.ok) {
        return new Response('Failed to fetch exchange rates', { status: 500 });
    }
    const exchange_rate = await response.json();
    return new Response(JSON.stringify(exchange_rate), { status: 200 });
};
