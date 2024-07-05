<!-- 
• writing typescript you need to make extra modification, at least in neovim svelte project 
• select the option that you are going to write typescript, and setup tsconfig.json
    "plugins": [
        {
            "name": "typescript-svelte-plugin"
        }
    ]

-->


<script lang="ts">
    // page variable, for accessing locals 
    import { page } from '$app/stores'

    // other components
    import Header from "$lib/components/Header.svelte";
    import DataUpload from '../lib/components/DataUpload.svelte';
    import SearchByValue from '../lib/components/SearchByValue.svelte';
    import UserWindow from '$lib/components/UserWindow.svelte';

    // css style
    import '../app.css'
</script>


<svelte:head>
    <title>SH System</title>
</svelte:head>



<main>
    <Header />
    <nav>
        <!-- if logout, there are no cookies for client to send request get user, indicating no user login -->
        {#if !$page.data.user}
            <div class="auth-section">
                <p><a href="/login">Login</a></p>
                <p><a href="/register">Register</a></p>
            </div>


        <!-- and we actually can add more link display here, just based on their roles level follow the same
        structure, redirect stuff, also see if these part can be arrange to a single components 
        should be fine, just import { page } in nav component 
        
        It's better to have all the function and components within different role's route, and for admin just need to 
        be able to go to their route, in this case code in the layout.svelte won't be that messy and repeitive
        -->
        {:else if $page.data.user.role === "ADMIN"}
            <a href="/admin">admin</a>
            <a href="/sale">sale</a>
            <a href="/data">data</a>
            <a href="/finance">finance</a>
            <a href="/procurement">procurement</a>
            <a href="/production">production</a>
            <form class="logout" action="/logout" method="POST">
                <button type="submit">Log Out</button>
            </form>
            <hr>
            <h2>Data Upload</h2>
            <DataUpload />

            <hr>
            <h2>Search</h2>
            <SearchByValue />
        <br>


        {:else if $page.data.user.role === "DATA"}
            <a href="/data">data</a>
            <form class="logout" action="/logout" method="POST">
                <button type="submit">Log Out</button>
            </form>
            <hr>
            <h2>Data Upload</h2>
            <DataUpload />

            <hr>
            <h2>Search</h2>
            <SearchByValue />
        <br> 


        <!-- a good practice to implement is to import components here I think, at least for right now 
        but later definitely need to organize this part, also some functionality is sensitive, 
        the problem need to consider is: 1) make functionality inaccessible or 2) to make data inaccessible -->
        {:else if $page.data.user.role === "SALE"}
            <a href="/sale">sale</a>
            <form class="logout" action="/logout" method="POST">
                <button type="submit">Log Out</button>
            </form>

            <hr>
            <h2>Search</h2>
            <SearchByValue />

            <hr>
            <h2>Sampling (Prototype)</h2>

            <hr>
            <h2>Invoice</h2>
        <br>



        {:else if $page.data.user.role === "FINANCE"}
            <a href="/finance">finance</a>
            <form class="logout" action="/logout" method="POST">
                <button type="submit">Log Out</button>
            </form>
        <br>



        {:else if $page.data.user.role === "PROCUREMENT"}
            <a href="/procurement">procurement</a>
            <form class="logout" action="/logout" method="POST">
                <button type="submit">Log Out</button>
            </form>
        <br>
        {/if}


    </nav>

    <UserWindow />
    <slot />


</main>

<style>

    p {
        font-size: 13px;
        padding: 5px 0px;
        background-color: #f0f0f0;
    }

    a {
        text-decoration: none;
        border: solid;
        border-radius: 8px;
        padding: 5px 7px;
        color: var(--color-black);
    }

    h2 {
        margin: 10px 0px;
    }

    a:hover {
        color: var(--color-hyperlink);
    }

    .auth-section {
        display: flex;
        justify-content: center;
        align-item: center;
        gap: 10px;
        margin: 1rem 0rem;
    }

</style>
