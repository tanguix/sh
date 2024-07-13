<script lang="ts">
    import type { ActionData } from './$types' // it's a type, how's that, speechless

    export let form: ActionData
</script>


<br>
<br>
<h1>Login (this below section is in auth route)</h1>

<form action="?/login" method="POST">
    <div>
        <label for="username">Username</label>
        <input id="username" name="username" type="text" required>
    </div>

    <div>
        <label for="password">password</label>
        <input id="password" name="password" type="password" required>
    </div>

    {#if form?.notUser}
        <p class="error">User Does't Exist</p>
    {/if}

    
    {#if form?.credentials}
        <p class="error">Wrong credentials</p>
    {/if}

    <button type="submit">Log in</button>

</form>
