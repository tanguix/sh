
<script lang='ts'>
    import { page } from '$app/stores' // this is the function to import if you want to use locals' value
</script>

<h1>Sale Section</h1>
<h1>----------</h1>
{#if $page.data.user}
    <p>Welcome {$page.data.user.name}!</p>
{/if}

