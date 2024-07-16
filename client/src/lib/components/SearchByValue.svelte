

<script lang="ts">
    import { onMount } from 'svelte';
    import FunctionalDisplay from './FunctionalDisplay.svelte';
    import { API_ENDPOINTS, constructUrl } from '$lib/utils/api';

    interface Sample {
        referenceNumber: string;
        tags: string[];
        date: string;
    }

    export let searchOption = '';
    export let searchCollection: string[] = [];
    export let searchKey: string[] = [];

    let collections: string[] = [];
    let keys: string[] = [];
    let results: any[] = [];
    export let deepCopiedResults = [];

    let selectedCollectionName: string = '';
    let selectedKey: string = '';
    let valueToSearch: string = '';

    let isDropdownOpen = false;
    let selectedCollectionDisplay = 'Select Collection';

    $: isSamplingMode = searchOption === 'sampling';

    function toggleMode() {
        searchOption = isSamplingMode ? '' : 'sampling';
        // Reset search fields when switching modes
        selectedKey = '';
        valueToSearch = '';
        results = [];
        deepCopiedResults = [];
    }

    function toggleDropdown() {
        isDropdownOpen = !isDropdownOpen;
    }

    function selectCollection(collection: string) {
        selectedCollectionName = collection;
        selectedCollectionDisplay = collection;
        isDropdownOpen = false;
        updateKeys();
    }

    onMount(async () => {
        try {
            const response = await fetch(API_ENDPOINTS.FETCH_COLLECTIONS);
            if (response.ok) {
                const data = await response.json();
                collections = data.collections.filter(collection => 
                    searchCollection.length === 0 || searchCollection.includes(collection)
                );
            } else {
                console.error('Failed to fetch collections');
            }
        } catch (error) {
            console.error('Error fetching collections:', error);
        }
    });

    async function updateKeys() {
        if (selectedCollectionName) {
            try {
                const url = constructUrl(API_ENDPOINTS.FETCH_KEYS, { collection: selectedCollectionName });
                const response = await fetch(url);
                if (response.ok) {
                    const data = await response.json();
                    keys = data.keys.filter(key => 
                        searchKey.length === 0 || searchKey.includes(key)
                    );
                } else {
                    console.error('Failed to fetch keys');
                }
            } catch (error) {
                console.error('Error fetching keys:', error);
            }
        } else {
            keys = [];
        }
        selectedKey = ''; 
    }

    async function search() {
        if (isSamplingMode) {
            selectedKey = "reference_no";
        }

        if (!selectedCollectionName || !selectedKey || !valueToSearch) {
            return;
        }

        try {
            const url = constructUrl(API_ENDPOINTS.SEARCH_RESULTS, {
                collection: selectedCollectionName,
                key: selectedKey,
                value: valueToSearch
            });

            const response = await fetch(url);

            if (response.ok) {
                const data = await response.json();
                if (isSamplingMode) {
                    let newResults = Array.isArray(data) && data.length && Array.isArray(data[0]) ? data[0] : data;
                    results = [...results, ...newResults];
                } else {
                    results = data;
                }
                deepCopiedResults = JSON.parse(JSON.stringify(results));
                if (isSamplingMode) {
                    valueToSearch = ''; // Reset after adding in sampling mode
                }
            } else {
                const errorData = await response.json();
                console.error('Error searching collection:', errorData.error);
                results = [];
            }
        } catch (error) {
            console.error('Error searching collection:', error);
            results = [];
        }
    }
</script>

<div class="search-container">
    <h2>Search</h2>
    

    <div class="mode-switch">
        <label class="switch">
            <input type="checkbox" checked={isSamplingMode} on:change={toggleMode}>
            <span class="slider round"></span>
        </label>
        <span class="mode-label">{isSamplingMode ? 'Sampling' : 'Normal'} Mode</span>
    </div>



    <div class="search-controls">
        <select class="custom-select" bind:value={selectedCollectionName} on:change={updateKeys}>
            <option value="">Select Collection</option>
            {#each collections as collection}
                <option value={collection}>{collection}</option>
            {/each}
        </select>

        {#if isSamplingMode}
            <div class="input-group">
                <input type="text" bind:value={valueToSearch} placeholder="Enter reference number">
                <button on:click={search}>Add</button>
            </div>
        {:else}
            <div class="non-sampling-search">
                <p>Normal search mode</p>
                {#if keys.length > 0}
                    <select class="custom-select" bind:value={selectedKey}>
                        <option value="">Select a key</option>
                        {#each keys as key}
                            <option value={key}>{key}</option>
                        {/each}
                    </select>
                {/if}
                {#if selectedKey}
                    <div class="input-group">
                        <input type="text" bind:value={valueToSearch} placeholder="Enter search value">
                        <button on:click={search}>Search</button>
                    </div>
                {/if}
            </div>
        {/if}
    </div>
</div>

<FunctionalDisplay {results} {deepCopiedResults} {searchOption} />


<style>
    .search-container {
        font-family: 'Ubuntu', sans-serif;
        max-width: 600px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f5f5f5;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    h2 {
        color: #333;
        margin-bottom: 20px;
    }

    .search-controls {
        display: flex;
        flex-direction: column;
        gap: 15px;
    }

    .custom-select {
        font-family: "Ubuntu";
        appearance: none;
        background-color: #fff;
        border: 1px solid #ccc;
        padding: 10px;
        font-size: 16px;
        border-radius: 4px;
        width: 100%;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%23333' viewBox='0 0 16 16'%3E%3Cpath d='M7.247 11.14L2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 10px center;
    }


    .custom-select option {
        padding: 10px;
        background-color: #fff;
        color: #333;
    }

    .custom-select option:hover,
    .custom-select option:focus,
    .custom-select option:active {
        background-color: #007bff;
        color: #fff;
    }


    .input-group {
        display: flex;
        gap: 10px;
    }

    input[type="text"] {
        flex-grow: 1;
        padding: 10px;
        font-size: 16px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }

    button {
        padding: 10px 20px;
        font-size: 16px;
        color: #fff;
        background-color: #007bff;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s;
    }

    button:hover {
        background-color: #0056b3;
    }

    .non-sampling-search {
        background-color: #fff;
        padding: 15px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .non-sampling-search p {
        margin-bottom: 10px;
        color: #666;
    }


    .mode-switch {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }

    .mode-label {
        margin-left: 0.5rem;
    }

    /* The switch - the box around the slider */
    .switch {
        position: relative;
        display: inline-block;
        width: 60px;
        height: 34px;
    }

    /* Hide default HTML checkbox */
    .switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }

    /* The slider */
    .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        transition: .4s;
    }

    .slider:before {
        position: absolute;
        content: "";
        height: 26px;
        width: 26px;
        left: 4px;
        bottom: 4px;
        background-color: white;
        transition: .4s;
    }

    input:checked + .slider {
        background-color: #2196F3;
    }

    input:focus + .slider {
        box-shadow: 0 0 1px #2196F3;
    }

    input:checked + .slider:before {
        transform: translateX(26px);
    }

    /* Rounded sliders */
    .slider.round {
        border-radius: 34px;
    }

    .slider.round:before {
        border-radius: 50%;
    }

</style>



