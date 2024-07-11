
<script lang="ts">

    // onMount
    import { onMount } from 'svelte';
    import FunctionalDisplay from './FunctionalDisplay.svelte';
    import { API_ENDPOINTS, constructUrl } from '$lib/utils/api';


    // typescript interface, think of Sample as a struct in python, is a object defining a object's shape and data type
    // currently not in usually, but later could be used for "type checking", "code documentation", etc
    interface Sample {
        referenceNumber: string;
        tags: string[];
        date: string;
    }

    // option instruction for search type (general search or sampling)
    export let searchOption = '';


    // I should exclude whatever sensitive collection at the backend
    // so the searchCollection variable here for filtering is not necessary, but just keep for now
    export let searchCollection: string[] = [];
    // same here, because search method is separated with searchOption, so no need to bypass, but keep for now
    export let searchKey: string[] = [];
    // export let keysForDisplay: string[] = [];


    // backend return
    let collections: string[] = [];                 // list of collections return from backend
    let keys: string[] = [];                        // list of keys rethrn from backend
    let results: any[] = [];                        // presumably(any), array of json object matched with key search from backend
    export let deepCopiedResults = [];              // deep copy immediately after fetch from backend, pass to <FunctionalDisplay />


    // frontend
    let selectedCollectionName: string = '';        // user's selection from html select tag
    let selectedKey: string = '';                   // same as above, let declarer make it changable compared to const
    let valueToSearch: string = '';                 // user's entered for form entry



    // automatically fetch collections list from the backend and display in the select for user to choose
    onMount(async () => {
        try {
            // user url const to fetch
            const response = await fetch(API_ENDPOINTS.FETCH_COLLECTIONS);
            if (response.ok) {
                const data = await response.json();
                // filter collection from frontend
                collections = data.collections.filter(collection => 
                    searchCollection.length === 0 || searchCollection.includes(collection)
                );
                // console.log("Filtered collections:", collections);
            } else {
                console.error('Failed to fetch collections');
            }
        } catch (error) {
            console.error('Error fetching collections:', error);
        }
    });

    // fetch backend routes that only return keys
    async function updateKeys() {
        if (selectedCollectionName) {
            try {
                // 'http://localhost:5000/search/api/keys?collection=${encodeURIComponent(selectedCollectionName)}';
                // refer to the utils/api.ts for the API setup and constructUrl function
                const url = constructUrl(API_ENDPOINTS.FETCH_KEYS, { collection: selectedCollectionName });
                const response = await fetch(url);
                if (response.ok) {
                    const data = await response.json();
                    // filter keys here if needed
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

    // actual search method
    async function search() {


        // make a check, if searchOption is passed in to this component, 
        // for example "sampling" auto-assign key to reference_no
        // and then you just need to conditionally render select or fixed form entry for search
        if (searchOption === "sampling") {
            selectedKey = "reference_no";

            try {

                // construct the search url query, "?" parameter 
                // will be append automatically by the constructUrl function
                const url = constructUrl(API_ENDPOINTS.SEARCH_RESULTS, {
                    collection: selectedCollectionName,
                    key: selectedKey,
                    value: valueToSearch
                });

                // construct url
                const response = await fetch(url);

                if (response.ok) {
                    const data = await response.json();

                    let newResults = Array.isArray(data) && data.length && Array.isArray(data[0]) ? data[0] : data;
                    results = [...results, ...newResults];
                    // deep copy immediately
                    deepCopiedResults = JSON.parse(JSON.stringify(results));
                    valueToSearch = ''; // Reset after adding

                } else {
                    const errorData = await response.json();
                    console.error('Error searching collection:', errorData.error);
                }
            } catch (error) {
                console.error('Error searching collection:', error);
            }
        }




        // normal check 
        if (!selectedCollectionName || !selectedKey || !valueToSearch) {
            return;
        }


        // if not searching method specify, do the normal search, fetch all keys
        try {
            const url = constructUrl(API_ENDPOINTS.SEARCH_RESULTS, {
                collection: selectedCollectionName,
                key: selectedKey,
                value: valueToSearch
            });

            // console.log("Search Url:", url)
            // construct
            const response = await fetch(url);


            if (response.ok) {
                const data = await response.json();
                results = data;

                // deep copy immediately
                deepCopiedResults = JSON.parse(JSON.stringify(results));

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





<!-- 
    design thought:  
        I want to make a tab selection here, so fuzzy search based on any key values 
        aside from fuzzy search, later you can also use unique identifier for invoice-generation search
        
        another tab for sampling search, where you can add item one by one for printing the sampling
        don't make it select tag, cause there are select tag for keys and collections already, I am tired of select tag
-->
<!-- Dropdown for selecting a collection -->
<select class="custom-select" bind:value={selectedCollectionName} on:change={updateKeys}>
    <option value="">Collection</option>
    {#each collections as collection}
        <option value={collection}>{collection}</option>
    {/each}
</select>


<!-- Input field for entering the value to search -->
{#if searchOption === "sampling"}
    <input type="text" bind:value={valueToSearch} placeholder="Enter reference number">
    <button on:click={search}>Add</button>
{:else}
    <!-- Render this part if searchOption is not 'sampling' -->
    <p>Non-sampling search mode</p>
    <div>
        <!-- Dropdown for selecting a key if keys exist in the selected collection -->
        {#if keys.length > 0}
            <select bind:value={selectedKey}>
                <option value="">Select a key</option>
                {#each keys as key}
                    <option value={key}>{key}</option>
                {/each}
            </select>
        {/if}
    </div>
     <div>
        {#if selectedKey}
            <input type="text" bind:value={valueToSearch} placeholder="Enter alternative value">
            <button on:click={search}>Fuzzy Finder</button>
        {/if}
    </div>
{/if}



<!-- Display the search results using DisplayResult component -->
<FunctionalDisplay {results} {deepCopiedResults}/>

<style>
    select {
        font-family: "Ubuntu";
    }

    option {
        font-family: "Ubuntu";
    }

    .custom-select {
        appearance: none;
        -webkit-appearance: none;
        -moz-appearance: none;
        background-color: #f0f0f0;
        border: 1px solid #ccc;
        padding: 10px;
        font-size: 14px;
        border-radius: 10px;
        width: 20%;
        background-repeat: no-repeat;
        background-position: right 10px center;
    }

    .custom-select:focus {
        outline: none;
        border-color: #007bff;
    }
</style>
