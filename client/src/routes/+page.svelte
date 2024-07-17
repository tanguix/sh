


<script lang="ts">
    import "../app.css";
    import { writable } from 'svelte/store';
    import { onMount, onDestroy } from 'svelte';
    import { unsavedChanges } from '$lib/utils/vars';
    import { get } from 'svelte/store';
    import { goto } from '$app/navigation';
    import Modal from '../lib/components/Modal.svelte';

    // Sampling Step
    import SearchByValue from '$lib/components/SearchByValue.svelte';

    // Invoice Generation Step 
    import Invoice from '$lib/components/Invoice.svelte';

    // WorkFlow
    import WorkFlow from '$lib/components/WorkFlow.svelte';


    let exchange_rate = writable(null);
    let error = writable('');
    let showModal = writable(false);
    let pendingNavigation = null;
    let pendingExternal = false;

    async function fetchExchangeRate() {
        try {
            const response = await fetch('http://localhost:5000/extra/api/exchange_rate');
            if (!response.ok) {
                throw new Error('Failed to fetch exchange rates');
            }
            const data = await response.json();
            exchange_rate.set(data);
        } catch (err) {
            error.set(err.message);
        }
    }

    function formatTimestamp(timestamp: number): string {
        const date = new Date(timestamp * 1000); // Convert seconds to milliseconds
        return date.toLocaleString(); // Format date and time
    }

    function handleNavigation(event: any) {
        if (get(unsavedChanges)) {
            event.preventDefault();
            event.stopPropagation();
            if (event.detail && event.detail.to) {
                pendingNavigation = event.detail.to.href.toString();
            } else {
                pendingExternal = true;
                pendingNavigation = event.target.href;
            }
            showModal.set(true);
        }
    }

    function confirmNavigation() {
        unsavedChanges.set(false);
        showModal.set(false);
        if (pendingNavigation) {
            if (pendingExternal) {
                window.location.href = pendingNavigation;
            } else {
                goto(pendingNavigation, { invalidateAll: true });
            }
        }
        pendingNavigation = null;
        pendingExternal = false;
    }

    function cancelNavigation() {
        showModal.set(false);
        pendingNavigation = null;
        pendingExternal = false;
    }

    function handleBeforeUnload(event: BeforeUnloadEvent) {
        if (get(unsavedChanges)) {
            event.preventDefault();
            event.returnValue = ''; // This is necessary for the event to trigger the confirmation dialog in some browsers.
        }
    }

    onMount(() => {
        window.addEventListener('beforeunload', handleBeforeUnload);
        document.addEventListener('click', handleInternalLinks, true);
        return () => {
            window.removeEventListener('beforeunload', handleBeforeUnload);
            document.removeEventListener('click', handleInternalLinks, true);
        };
    });

    function handleInternalLinks(event: MouseEvent) {
        const target = event.target as HTMLAnchorElement;
        if (target && target.tagName === 'A' && target.href) {
            if (target.origin === window.location.origin) {
                // Handle internal link
                event.preventDefault();
                event.stopPropagation();
                if (get(unsavedChanges)) {
                    pendingNavigation = target.href;
                    showModal.set(true);
                } else {
                    window.location.href = target.href;
                }
            } else {
                // Handle external link
                event.preventDefault();
                event.stopPropagation();
                if (get(unsavedChanges)) {
                    pendingExternal = true;
                    pendingNavigation = target.href;
                    showModal.set(true);
                } else {
                    window.location.href = target.href;
                }
            }
        }
    }
</script>

<svelte:window on:navigating={handleNavigation} />

        
<!-- 
you can add this line: onConfirm={confirmNavigation}
above the onCancel={cancelNavigation}, to give user option to choose if that's not force 
-->
{#if $showModal}
    <Modal
        message="You have unsaved changes. Are you sure you want to leave?"
        onCancel={cancelNavigation} />
{/if}




<!-- this is sampling -->
<SearchByValue searchOption="sampling"/>
<!-- invoice generation -->
<Invoice />

<hr>
<br>
<!-- <WorkFlow /> -->


<a href="https://www.google.com">leave</a>
<button on:click={fetchExchangeRate}>Exchange Rates</button>

{#if $exchange_rate}
    <div class="ex-card">
        <h4>Date: {$exchange_rate.date}</h4>
        <h4>Time: {formatTimestamp($exchange_rate.timestamp)}</h4>
        <h4>Base Currency: {$exchange_rate.base}</h4>
    </div>
    <!-- Loop to display all following rates -->
    {#each Object.entries($exchange_rate.rates) as [currency, rate]}
        <div class="ex-card"><h3>{currency}: {rate}</h3></div>
    {/each}
{:else if $error}
    <p>{$error}</p>
{/if}

<style>
    .ex-card {
        border: 1px solid #ddd;
        padding: 16px;
        margin: 16px 0;
        background-color: #f9f9f9;
    }
</style>
