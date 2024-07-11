


<script lang="ts">

  import { API_ENDPOINTS, constructUrl } from '../utils/api.ts'; // api helper function
  import { page } from '$app/stores'  // this is the function to import if you want to use locals' value
  import { get } from 'svelte/store'; // the correct way to retrieve locals values in .ts file

  import { writable } from 'svelte/store';
  import { unsavedChanges } from '$lib/utils/vars';
  import { loadBase64Font, addImageToPDF, generatePDF } from '$lib/utils/pdf.ts';

  export let results: any[] = [];
  export let deepCopiedResults: any[] = [];

  export let keysToExclude: string[] = ['image_url', 'categories', 'tags'];
  let content: string = `
      Marks & Order Nos.(标志及订单号码)\n
      Description & Specifications (描述及规格)\n
      Unit Price (单价)\n
      Total Price (总值)\n
      H.S.CODE (商品编码)\n
      From 由\n
      To 至
  `;

    const displayedForms = writable({});
    let selectedKeys = {};
    let selectedDates = writable({});
    let removeClickCounts = writable({}); // To track remove button clicks
    let selectedForRemoval = writable({}); // To track selected keys for removal

    function filterDisplayedKeys(result) {
        const filteredResult = {};
        for (const key in result) {
            if (!keysToExclude.includes(key)) {
                filteredResult[key] = result[key];
            }
        }
        return filteredResult;
    }

    async function generatePDFWrapper() {
        await generatePDF(results, content);
    }

    function addForm(index: number) {
        displayedForms.update(forms => {
            if (!forms[index]) {
                forms[index] = [];
            }
            forms[index].push({ key: '', value: '', isRemove: false });
            return forms;
        });
    }

    function removeKey(index: number) {
        displayedForms.update(forms => {
            if (!forms[index]) {
                forms[index] = [];
            }
            forms[index].push({ key: '', isRemove: true });
            return forms;
        });

        removeClickCounts.update(counts => {
            counts[index] = (counts[index] || 0) + 1;
            return counts;
        });
    }

    function lessForm(index: number) {
        displayedForms.update(forms => {
            if (!forms || !forms[index] || forms[index].length === 0) {
                console.error("Attempt to remove a form from an uninitialized index or empty forms array.");
                return forms;
            }
            const lastForm = forms[index].pop();
            if (lastForm && lastForm.isRemove) {
                removeClickCounts.update(counts => {
                    counts[index] = (counts[index] || 1) - 1;
                    return counts;
                });
            }
            if (forms[index].length === 0) {
                delete forms[index];
            }
            return forms;
        });

        selectedForRemoval.update(selections => {
            delete selections[index];
            return selections;
        });
    }

    function clearForms(index: number) {
        displayedForms.update(forms => {
            if (forms[index]) {
                forms[index] = [];
            }
            return forms;
        });

        removeClickCounts.update(counts => {
            counts[index] = 0;
            return counts;
        });

        selectedForRemoval.update(selections => {
            selections[index] = [];
            return selections;
        });
    }




    function updateForm(index: number, entryIndex: number, field: string, value: string) {
        displayedForms.update(forms => {
            if (forms[index] && forms[index][entryIndex]) {
                if (field === 'value' && forms[index][entryIndex].isDate) {
                    // Convert the date value to a suitable format if necessary
                    const dateValue = new Date(value).toISOString().split('T')[0];
                    forms[index][entryIndex][field] = dateValue;
                } else {
                    forms[index][entryIndex][field] = value;
                }
            }
            return forms;
        });
    }




    function toggleDateInput(index: number, entryIndex: number) {
        displayedForms.update(forms => {
            if (forms[index] && forms[index][entryIndex]) {
                forms[index][entryIndex].isDate = !forms[index][entryIndex].isDate;
                if (forms[index][entryIndex].isDate) {
                    forms[index][entryIndex].key = 'delivery_date';
                    forms[index][entryIndex].value = ''; // Clear the value when toggling to date
                } else {
                    forms[index][entryIndex].key = '';
                    forms[index][entryIndex].value = ''; // Clear the value when toggling to text
                }
            }
            return forms;
        });
    }



    function updateResults(index: number) {
        const user = get(page).data.user;

        if (user) {
            const formData = $displayedForms[index] || [];
            const updates = formData.reduce((acc, curr) => {
                if (curr.key && curr.value && !curr.isRemove) {
                    acc[curr.key] = curr.value;
                } else if (curr.key && curr.isRemove) {
                    delete results[index][curr.key];
                }
                return acc;
            }, {});

            console.log("Original deepCopiedResults:", deepCopiedResults);

            results[index] = { ...results[index], ...updates };

            // Handle modifiedBy field
            if (results[index].modifiedBy) {
                if (Array.isArray(results[index].modifiedBy)) {
                    results[index].modifiedBy.push(user);
                } else {
                    results[index].modifiedBy = [results[index].modifiedBy, user];
                }
            } else {
                results[index].modifiedBy = [user];
            }

            console.log("Updated results:", results);

            clearForms(index);
            unsavedChanges.set(true);
        } else {
            console.log("undefined user");
        }
    }



    function arraysEqual(a, b) {
        a = JSON.stringify(a);
        b = JSON.stringify(b);

        return a === b;
    }


    function countRemovableKeys(result) {
        return Object.keys(result).filter(key => !keysToExclude.includes(key)).length;
    }

    function canRemoveKeys(index) {
        const result = results[index];
        const removableKeysCount = countRemovableKeys(result);
        const formData = $displayedForms[index] || [];
        const existingRemoves = formData.filter(form => form.isRemove).length;
        return removableKeysCount > existingRemoves;
    }

    $: canRemove = results.map((result, index) => {
        const formData = $displayedForms[index] || [];
        const existingRemoves = formData.filter(form => form.isRemove).length;
        const removableKeysCount = countRemovableKeys(result);
        return removableKeysCount > existingRemoves;
    });




    // after push to the database, remmeber to make a blinking realtime effect showing the unique identifier for a side tab 
    // mostly they don't need to use that immediately so user windows' update could use traditional way: fetch responds 
    // but if they want to use that immediately, they can copy from the blinking tab


    async function pushChangesToBackend() {
        try{
            if (!arraysEqual(deepCopiedResults, results)) {
                console.log("Pushing changes to the database:", results);

                // results is an array, need to convert into JSON object for sending, but still backend will receive array
                // create api endpoint: original url ('http://localhost:5000/upload/api/upload_sample')
                const response = await fetch(API_ENDPOINTS.UPLOAD_SAMPLE, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(results), // convert the result to a JSON object
                });

                if (!response.ok) {
                    throw new Error('Failed to upload sample data');
                }

                unsavedChanges.set(false);
                const sampling_response = await response.json();
                console.log(sampling_response.message, ":", sampling_response.sample_token)

            } else {
                console.log("No changes to push");
            }
        } catch (error) {
            console.error("Caught unexpected error:", error.message)
        }
    }






</script>

<div id="result">
    {#if results.length > 0}
        {#each results as result, index}
            <h3>{content}</h3>
            <div class="result-container">
                <pre>{JSON.stringify(filterDisplayedKeys(result), null, 2)}</pre>
                {#if result.image_url}
                    <img src={result.image_url} alt="searched_image" onerror="this.onerror=null;this.src='fallback-image-url';">
                {/if}
            </div>
            <button on:click={() => addForm(index)}>Add</button>
            {#if canRemove[index]}
                <button on:click={() => removeKey(index)}>Remove</button>
            {/if}
            {#if $displayedForms[index]}
                {#each $displayedForms[index] as form, entryIndex}
                    <div>
                        <form>

                            {#if form.isRemove}
                                <label for={`key-${index}-${entryIndex}`}>Select Key to Remove:</label>
                                <select id={`key-${index}-${entryIndex}`} on:change={e => updateForm(index, entryIndex, 'key', e.target.value)}>
                                    <option value="">Select key</option>
                                    {#each Object.keys(results[index]) as key}
                                        {#if !keysToExclude.includes(key) && !($selectedForRemoval[index] || []).includes(key)}
                                            <option value={key}>{key}</option>
                                        {/if}
                                    {/each}
                                </select>
                            {:else}
                                <label for={`key-${index}-${entryIndex}`}>Key:</label>
                                <input id={`key-${index}-${entryIndex}`} type="text" on:input={e => updateForm(index, entryIndex, 'key', e.target.value)} value={form.key} readonly={form.isDate} />
                                <label for={`value-${index}-${entryIndex}`}>Value:</label>
                                <input id={`value-${index}-${entryIndex}`} type={form.isDate ? 'date' : 'text'} on:input={e => updateForm(index, entryIndex, 'value', e.target.value)} value={form.value} />

                                <label class="custom-checkbox">
                                    <input type="checkbox" on:click={() => toggleDateInput(index, entryIndex)} checked={form.isDate} />
                                    <span class="outer-circle">
                                        <span class="inner-circle"></span>
                                    </span>
                                    Date Type
                                </label>
                            {/if}

                        </form>
                    </div>
                {/each}
            {/if}
            <button on:click={() => updateResults(index)}>Update</button>
            <button on:click={() => lessForm(index)}>Cancel</button>
        {/each}
        <div>
            <br>
            <hr>
            <button on:click={pushChangesToBackend}>Push Changes</button>
            <button on:click={generatePDFWrapper}>Download PDF</button>
        </div>
    {:else}
        <p>No results found</p>
    {/if}
</div>





<style>
    .result-container {
        margin-top: 10px;
        width: 100%;
    }
    img {
        max-width: 70%;
        height: auto;
        display: block;
        margin: 10px 0;
    }
    .custom-checkbox {
        display: inline-block;
        position: relative;
        padding-left: 35px;
        margin-top: 20px;
        cursor: pointer;
        font-size: 16px;
        user-select: none;
    }

    .custom-checkbox input {
        position: absolute;
        opacity: 0;
        cursor: pointer;
        height: 0;
        width: 0;
    }

    .outer-circle {
        position: absolute;
        top: 0;
        left: 0;
        height: 20px;
        width: 20px;
        background-color: transparent;
        border: 2px solid #ccc;
        border-radius: 50%;
        box-shadow: 0 0 3px rgba(0, 0, 0, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .inner-circle {
        height: 12px;
        width: 12px;
        border: 2px solid #ccc;
        background-color: transparent;
        border-radius: 50%;
        transition: background-color 0.3s;
    }

    .custom-checkbox input:checked ~ .outer-circle .inner-circle {
        background-color: #2196F3;
    }
</style>



