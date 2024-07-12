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
    import { userRoles } from "$lib/utils/vars";
    import { page } from '$app/stores';
    import { onMount } from 'svelte';
    import Header from "$lib/components/Header.svelte";
    import UserWindow from '$lib/components/UserWindow.svelte';
    import DataUpload from '../lib/components/DataUpload.svelte';
    import SearchByValue from '../lib/components/SearchByValue.svelte';
    import '../app.css';

    // Helper function to capitalize first letter
    const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();

    let userRole = '';
    let navLinks = <any>[];

    // Function to check if the current user has access to a specific role's route
    const hasAccess = (role: string) => userRole === 'ADMIN' || userRole === role.toUpperCase();

    // Update navigation links when user role changes
    $: {
        console.log('User data updated:', $page.data.user); // Debug log
        userRole = $page.data.user?.role || '';
        navLinks = userRoles
            .filter(role => hasAccess(role))
            .map(role => ({
                href: `/${role.toLowerCase()}`,
                label: capitalize(role)
            }));
        console.log('Updated navLinks:', navLinks); // Debug log
    }

    onMount(() => {
        console.log('Component mounted. Initial user data:', $page.data.user); // Debug log
    });
</script>

<svelte:head>
    <title>SH System</title>
</svelte:head>

<main>
    <Header />
    <nav>
        {#if $page.data.user === undefined}
            <p>Loading...</p>
        {:else if !$page.data.user}
            <div class="auth-section">
                <p><a href="/login">Login</a></p>
                <p><a href="/register">Register</a></p>
            </div>
        {:else}
            {#each navLinks as { href, label }}
                <a {href}>{label}</a>
            {/each}
            <form class="logout" action="/logout" method="POST">
                <button type="submit">Log Out</button>
            </form>
        {/if}
    </nav>

    {#if $page.data.user}
        {#if userRole === 'ADMIN' || userRole === 'DATA'}
            <hr>
            <h2>Data Upload</h2>
            <DataUpload />
        {/if}

        {#if ['ADMIN', 'DATA', 'SALE'].includes(userRole)}
            <hr>
            <h2>Search</h2>
            <SearchByValue />
        {/if}

        {#if userRole === 'SALE'}
            <hr>
            <h2>Sampling (Prototype)</h2>
            <!-- Add Sampling component here when it's ready -->

            <hr>
            <h2>Invoice</h2>
            <!-- Add Invoice component here when it's ready -->
        {/if}
    {/if}

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
        padding: 10px;
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
        gap: 10px;
        margin: 1rem 0rem;
    }

</style>
