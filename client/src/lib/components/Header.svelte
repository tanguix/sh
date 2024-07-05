<script lang="ts">
    // refer to this line for svg: https://www.svgviewer.dev/
    import Cat1 from "$lib/components/svg/Cat1.svelte";
    import Cat2 from "$lib/components/svg/Cat2.svelte";
    import Cat3 from "$lib/components/svg/Cat3.svelte";
    import "../../app.css";
</script>




<header class="">
    <nav class="nav">
        <div>
            <h1><a href="/">SH Database</a></h1>
            <a href="https://www.google.com/"><Cat3 class="svg-icon" /></a>
            <a href="https://www.google.com/"><Cat2 class="svg-icon" /></a>
            <a href="https://www.google.com/"><Cat1 class="svg-icon" /></a>
        </div>
    </nav>
</header>

<!-- local style only apply to this svelte page -->
<style>
    header {
        display: flex;
        justify-content: center;
        align-item: center;
    }

    h1 {
        display: flex;
        justify-content: center;
        align-item: center;
        margin: 1rem 0rem;
    }

    .nav {
        display: flex;
        flex-direction: column;
        gap: 10px;  /* adjust the gap between flex item (h1 and div) */
    }

</style>


