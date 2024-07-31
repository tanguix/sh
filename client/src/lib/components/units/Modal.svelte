

<!-- Modal.svelte -->
<script>
    export let message = "";
    export let onConfirm;    // comment this, making them can only update before leaving
    export let onCancel;
</script>

<div class="modal-backdrop">
    <div class="modal">
        <p>{message}</p>
        <button class="btn" on:click={onConfirm}>Confirm</button>
        <button on:click={onCancel}>Cancel</button>
    </div>
</div>

<style>
    .modal-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .modal {
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    button {
        margin: 5px;
    }
</style>

