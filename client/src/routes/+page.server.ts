

// To make the frontend automatically update when the backend data changes, there are several approaches you can take, depending on your use case and the frequency of updates required. Here are some common strategies:
// 1. Polling
// 2. WebSockets3. (example use node.js) https://www.youtube.com/watch?v=mAcKzdW5fR8
// 3. Server-Sent Events (SSE: example use node.js and express.js)
// 4. search for "Real-Time Data Synchronization"
// 5. the thing is, maybe you don't need real-time update, there are solution whenever you have some updated in the backend, it will then have a function automatically refresh the frontend, and maybe the problem is on the backend? so don't rush on this one, looking into it deeper.
// 6. write a loop to keep checking this is also a possible solution, if you don't heavily focus on latency and scalability
// resource: https://www.youtube.com/watch?v=Kzrz7GZ9pIg (Hook in svelte) | https://www.youtube.com/watch?v=rsmLu5nmh4g | https://www.youtube.com/watch?v=MoGkX4RvZ38&t=16s | https://www.youtube.com/watch?v=whEObh8waxg | https://www.youtube.com/watch?v=nDgdldBPoE0 | https://www.youtube.com/watch?v=7hXHbGj6iE0 | https://www.youtube.com/watch?v=rsmLu5nmh4g



