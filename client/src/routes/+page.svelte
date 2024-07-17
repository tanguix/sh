


<script lang="ts">
    import "../app.css";
    import { writable } from 'svelte/store';
    import { onMount } from 'svelte';
    import { unsavedChanges } from '$lib/utils/vars';
    import { get } from 'svelte/store';
    import { goto } from '$app/navigation';
    import Modal from '../lib/components/Modal.svelte';



    let showModal = writable(false);
    let pendingNavigation = null;
    let pendingExternal = false;





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




<div class="leave">
  <a href="https://www.google.com">leave</a>
</div>


<style>

  .leave {
    display: flex;
    font-family: "Ubuntu";
    align-items: center;
    justify-content: center;
  }

</style>
