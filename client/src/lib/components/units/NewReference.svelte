



<script lang="ts">
    import { onMount } from 'svelte';
    import { page } from '$app/stores';
    import { API_ENDPOINTS } from '$lib/utils/api';
    import { get } from 'svelte/store';

    export let onReferenceSelect: (value: string) => void;

    let isNewReference = false;
    let newReferenceName = '';
    let newReferenceAbbreviation = '';
    let existingReferences: Array<{ fullName: string, abbreviation: string }> = [];
    let errorMessage = '';
    let selectedReference = '';
    let isAdmin = false;
    let successMessage = '';


    $: checkboxClass = isAdmin ? 'admin-checkbox' : 'non-admin-checkbox';

    onMount(async () => {
        await fetchExistingReferences();
        const user = get(page).data.user;
        isAdmin = user && user.role === 'ADMIN';
    });

    async function fetchExistingReferences() {
        try {
            const response = await fetch(API_ENDPOINTS.FETCH_REF_KEYS);
            if (response.ok) {
                existingReferences = await response.json();
            } else {
                errorMessage = 'Failed to fetch existing references';
            }
        } catch (error) {
            errorMessage = `Error fetching existing references: ${error.message}`;
        }
    }

    async function uploadNewReference(event: Event) {
        event.preventDefault();
        errorMessage = '';
        successMessage = '';
        if (!newReferenceName || !newReferenceAbbreviation) {
            errorMessage = 'Both full name and abbreviation are required';
            return;
        }

        try {
            const response = await fetch(API_ENDPOINTS.UPLOAD_REFERENCE, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    fullName: newReferenceName,
                    abbreviation: newReferenceAbbreviation,
                }),
            });

            const responseData = await response.json();

            if (response.ok) {
                await fetchExistingReferences();
                successMessage = 'New reference added successfully';
                newReferenceName = '';
                newReferenceAbbreviation = '';
            } else {
                errorMessage = responseData.error || 'Failed to upload new reference';
            }
        } catch (error) {
            errorMessage = `Error uploading new reference: ${error.message}`;
        }
    }

    function handleReferenceChange(event: Event) {
        const target = event.target as HTMLSelectElement;
        selectedReference = target.value;
        onReferenceSelect(selectedReference);
    }


    // New function to reset the selection
    export function resetSelection() {
        selectedReference = '';
        onReferenceSelect('');
    }


</script>




<div class="reference-number-input">
    <div class="reference-select-container">
        <select value={selectedReference} on:change={handleReferenceChange} required>
            <option value="">main reference key</option>
            {#each existingReferences as ref}
                <option value={ref.abbreviation}>{ref.fullName} ({ref.abbreviation})</option>
            {/each}
        </select>

        <label class="checkbox-label {checkboxClass}">
            <input type="checkbox" bind:checked={isNewReference} disabled={!isAdmin} />
            <span class="checkbox-custom"></span>
        </label>
        <p>main ref</p>
    </div>

    {#if isAdmin && isNewReference}
        <div class="new-reference-inputs">
            <input
                type="text"
                placeholder="Full reference name"
                bind:value={newReferenceName}
            />
            <input
                type="text"
                placeholder="Abbreviation"
                bind:value={newReferenceAbbreviation}
            />
            <button type="button" on:click={uploadNewReference}>+Reference</button>
        </div>
    {/if}

    {#if errorMessage}
        <p class="error-message">{errorMessage}</p>
    {/if}

    {#if successMessage}
        <p class="success-message">{successMessage}</p>
    {/if}
</div>




<style>

    select {
        font-family: Ubuntu, sans-serif;
        height: 2.5rem;
        -webkit-appearance: none;
        -moz-appearance: none;
        appearance: none;
        background-image: url("data:image/svg+xml;utf8,<svg fill='black' height='24' viewBox='0 0 24 24' width='24' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/><path d='M0 0h24v24H0z' fill='none'/></svg>");
        background-repeat: no-repeat;
        background-position-x: calc(100% - 10px);
        background-position-y: 7px;
        padding-right: 30px;
    }

    select option {
        font-family: Ubuntu, sans-serif;
    }

    /* For Firefox */
    select {
        text-overflow: ellipsis;
    }

    /* For IE and Edge */
    select::-ms-expand {
        display: none;
    }


    p {
        font-family: "Ubuntu";
        flex: 0 0 30px;
        text-align: center;
        justify-content: center;
        margin-left: 10px;
        font-size: 0.875rem;
        line-height: 1.5;
        border-radius: 0.2rem;
        white-space: nowrap;
        min-width: 60px;
        transition: background-color 0.3s, opacity 0.3s;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .reference-number-input {
        width: 100%;
        margin-bottom: 1rem;
    }
    .reference-select-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .reference-select-container select {
        flex-grow: 1;
        margin-right: 1rem;
    }
    .checkbox-label {
        display: flex;
        align-items: center;
        white-space: nowrap;
    }
    .new-reference-inputs {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.5rem;
    }
    .new-reference-inputs input {
        flex-grow: 1;
    }
    input[type="text"], select {
        padding: 0.25rem 0.5rem;
        font-size: 0.875rem;
        line-height: 1.5;
        border-radius: 0.2rem;
        border: 1px solid #ccc;
    }
    button {
        padding: 0.25rem 0.75rem;
        font-size: 0.875rem;
        line-height: 1.5;
        border-radius: 0.2rem;
        border: none;
        background-color: #007bff;
        color: white;
        cursor: pointer;
        transition: background-color 0.3s;
        white-space: nowrap;
    }
    button:hover {
        background-color: #0056b3;
    }
    .error-message {
        color: red;
        font-size: 0.875rem;
        margin-top: 0.5rem;
    }
    .success-message {
        color: green;
        font-size: 0.875rem;
        margin-top: 0.5rem;
    }


    .checkbox-label {
        display: flex;
        align-items: center;
        white-space: nowrap;
        position: relative;
        cursor: pointer;
    }

    .checkbox-label input[type="checkbox"] {
        opacity: 0;
        position: absolute;
    }

    .checkbox-custom {
        width: 16px;
        height: 16px;
        border: 1px solid;
        border-color: ButtonBorder;
        border-radius: 3px;
        display: inline-block;
        position: relative;
        background-color: Canvas;
        transition: all 0.2s ease-in-out;
    }

    .admin-checkbox .checkbox-custom::after {
        content: '';
        position: absolute;
        display: none;
        left: 5px;
        top: 2px;
        width: 3px;
        height: 7px;
        border: solid;
        border-color: Canvas;
        border-width: 0 2px 2px 0;
        transform: rotate(45deg);
        transition: all 0.2s ease-in-out;
    }

  .non-admin-checkbox .checkbox-custom::after {
      content: '!';
      position: absolute;
      display: flex;
      justify-content: center;
      align-items: center;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      color: GrayText;
      font-size: 12px;
      transition: all 0.2s ease-in-out;
  }

  .admin-checkbox input[type="checkbox"]:checked + .checkbox-custom {
      background-color: #007bff;
      border-color: #ffebee;
  }

  .admin-checkbox input[type="checkbox"]:checked + .checkbox-custom::after {
      display: block;
  }

  .non-admin-checkbox .checkbox-custom {
      background-color: ButtonFace;
      cursor: not-allowed;
  }

  .checkbox-label:hover .checkbox-custom {
      border-color: Highlight;
  }
    


</style>





