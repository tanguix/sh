<!-- set up users for registration -->

<script lang="ts">
    import type { ActionData } from './$types'
    
    export let form: ActionData

    // possible roles for user to select during registration, this is a required selection
    // PROCUREMENT 采购 (professional English name)
    const roles = ["Admin", "Data", "Sale", "Finance", "Production", "Procurement"]
    let selectedRole: string = '';

    // handle role value, make sure they are valid and make them uppercase
    // writing this so I can see the selection with console log right after "select" action for checking
    function handleRoleChange(event: Event) {
        const target = event.target as HTMLSelectElement;
        selectedRole = target.value;
        console.log("Selected role:", selectedRole.toUpperCase());
    }



    // todos: rendering some loading icon when button is clicked, and inform user that their registration is under review
    // todos: blinking might be used

</script>

<h1>Register</h1>

<!-- 
action="?/register":
1) the "action" attribute of the <form> tag specifies where to send the form data when the form is submitted
2) This is the URL to which the browser will make a request when the user submits the form.
3) "?/register" means after the submit the form, the page go to url <your_host:your_port>/register?/register
    - right now the page is already on localhost:3000/register, by default after submission it will send to localhost:3000/register?/register
    - which is the same as saying stay at the current URL
    - and it's the method="POST" make that action happen, if not method specified, it will then send your field entered to the web url
    - something like: http://localhost:3000/?username=Ben&email=mikiyax09%40gmail.com&company=zd%3Blkfjg%3Bldzkf (dangerous!)
    - when you set the form like <form action="?/upload" on:submit={handleSubmit}>
    - if you do this on the homepage(localhost:3000), say this time you what to upload samples information to the database
    - and specify the path like <form action="?/upload" method="POST">, the server will assume you have path(directory) for upload/, 
    - a path like localhost:3000/?/upload, but you don't have that. So will run into error
-->

<form action="?/register" method="POST">
    <div>
        <label for="username">Username</label>
        <input id="username" name="username" type="text" required>
    </div>

    <div>
        <label for="password">password</label>
        <input id="password" name="password" type="password" required>
    </div>

    <!-- adding a name for select tag within the form tag, this ensuring data is sent along with form data 
         remember to catch the POST request in +page.server.ts -->
    <div>
        <label for="role">role</label>
        {#if roles.length > 0}
            <select id="role" name="role" bind:value={selectedRole} on:change={handleRoleChange} required>
                <option value="">Select a role</option>
                {#each roles as role}
                    <!-- here to convert all letter into uppercase before sending to +page.server.ts -->
                    <option value={role.toUpperCase()}>{role}</option>
                {/each}
            </select>
        {/if}
    </div>

    <!-- access 'user' property on form object; if form is null, the expression return null instead of error  -->
    <!-- 
    this 'user' property is a custom property defined in the +page.svelte.ts with fail function, 
    you name property anything, when user is evaluated to true in +page.server.ts, on this page it's saying
    check form object using "user" property
    -->

    {#if form?.userExist} 
        <p class="error">Username is taken</p>
    {/if}

    {#if form?.serverError} 
        <p class="error">Backend function Error</p>
    {/if}


    <button type="submit">Register</button>
</form>





<!--
• id attribute 
1) label association <label> tag 
2) javascript targeting 
3) css styling 

• name attribute 
crucial for form submission: 
when a form is submitted, </select> 'name' attribute of each input element becomes the key in the form 
data key-value pair sent to the server.

======
------
client side:
<input id="username" name="username" type="text" required>

server side:
$username = $_POST['username'];
------

you can access the form data using the name attribute as the key, say for example you enter
"Ben" for the username field, then you can get the "Ben" string from server side using js:
const username = data.get('username')
console.log(username) is "Ben"
======
-->
