


<script lang="ts">
    import { writable } from 'svelte/store';
    import { API_ENDPOINTS, constructUrl } from '$lib/utils/api';

    type Field = {
        id: number;
        key: string;
        value: string;
    };

    type Item = {
        id: number;
        value: string;
    };

    let fields = writable<Field[]>([]);
    let tags = writable<Item[]>([]);
    let categories = writable<Item[]>([]);
    let imageFile: File | null = null;
    let imagePath: string = '';
    let imagePreviewUrl: string = '';


    // new variables for production needed
    let unitPrice = '';
    let unitWeight = '';
    let source = '';
    let address = '';
    let phone = '';



    let additionalImages: File[] = [];
    let additionalImagePreviews: string[] = [];

    let isDragOverMain = false;
    let isDragOverAdditional = false;

    function addItem(store) {
        store.update(currentItems => [
            ...currentItems,
            { id: Date.now(), value: '' }
        ]);
    }

    function removeItem(store: any, id: number) {
        store.update(currentItems => currentItems.filter(item => item.id !== id));
    }

    function handleFileSelect(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files.length > 0) {
            imageFile = target.files[0];
            imagePath = target.files[0].name;
            imagePreviewUrl = URL.createObjectURL(imageFile);
        }
    }

    function handleDrop(event: DragEvent) {
        event.preventDefault();
        isDragOverMain = false;
        if (event.dataTransfer && event.dataTransfer.files.length > 0) {
            imageFile = event.dataTransfer.files[0];
            imagePath = imageFile.name;
            imagePreviewUrl = URL.createObjectURL(imageFile);
            
            const fileInput = document.getElementById('image') as HTMLInputElement;
            if (fileInput) {
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(imageFile);
                fileInput.files = dataTransfer.files;
            }
        }
    }

    function handleDragEnter(event: DragEvent) {
        event.preventDefault();
        isDragOverMain = true;
    }

    function handleDragLeave(event: DragEvent) {
        event.preventDefault();
        isDragOverMain = false;
    }

    function handleDragOver(event: DragEvent) {
        event.preventDefault();
    }

    function handleKeyDown(event: KeyboardEvent) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            const fileInput = document.getElementById('image') as HTMLInputElement;
            fileInput.click();
        }
    }

    function handleAdditionalFileSelect(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files) {
            processAdditionalFiles(Array.from(target.files));
        }
    }

    function handleAdditionalDrop(event: DragEvent) {
        event.preventDefault();
        isDragOverAdditional = false;
        if (event.dataTransfer && event.dataTransfer.files) {
            processAdditionalFiles(Array.from(event.dataTransfer.files));
            
            const fileInput = document.getElementById('additional-images') as HTMLInputElement;
            if (fileInput) {
                const dataTransfer = new DataTransfer();
                Array.from(event.dataTransfer.files).forEach(file => {
                    if (file.type.startsWith('image/')) {
                        dataTransfer.items.add(file);
                    }
                });
                fileInput.files = dataTransfer.files;
            }
        }
    }

    function processAdditionalFiles(files: File[]) {
        for (let file of files) {
            if (file.type.startsWith('image/')) {
                additionalImages = [...additionalImages, file];
                additionalImagePreviews = [...additionalImagePreviews, URL.createObjectURL(file)];
            }
        }
    }

    function handleAdditionalDragEnter(event: DragEvent) {
        event.preventDefault();
        isDragOverAdditional = true;
    }

    function handleAdditionalDragLeave(event: DragEvent) {
        event.preventDefault();
        isDragOverAdditional = false;
    }

    function removeAdditionalImage(event: Event, index: number) {
        event.stopPropagation();
        additionalImages = additionalImages.filter((_, i) => i !== index);
        additionalImagePreviews = additionalImagePreviews.filter((_, i) => i !== index);
    }

    async function sendSampleData(combinedFormData: FormData) {
        const response = await fetch(API_ENDPOINTS.UPLOAD_DATA, {
            method: 'POST',
            body: combinedFormData, 
        });

        if (!response.ok) {
            throw new Error('Failed to upload sample data');
        }

        return await response.json();
    }

    function handleSubmit(event: Event) {
        event.preventDefault();
        const form = event.target as HTMLFormElement;
        const formData = new FormData(form);

        if (imageFile) {
            formData.append('image', imageFile);
        }

        additionalImages.forEach((image, index) => {
            formData.append(`additional_image_${index}`, image);
        });

        const additionalFields: Record<string, string> = {};
        fields.subscribe(currentFields => {
            currentFields.forEach(field => {
                if (field.key) {
                    additionalFields[field.key] = field.value;
                }
            });
        })();

        const additionalTags: string[] = [];
        tags.subscribe(currentTags => {
            currentTags.forEach(tag => {
                if (tag.value) {
                    additionalTags.push(tag.value);
                }
            });
        })();

        const additionalCategories: string[] = [];
        categories.subscribe(currentCategories => {
            currentCategories.forEach(category => {
                if (category.value) {
                    additionalCategories.push(category.value);
                }
            });
        })();

        const originalTags = formData.get('tag') ? 
            formData.get('tag').toString().split(',').map(tag => tag.trim()) : [];
        const originalCategories = formData.get('category') ? 
            formData.get('category').toString().split(',').map(category => category.trim()) : [];

        const allTags = originalTags.concat(additionalTags);
        const allCategories = originalCategories.concat(additionalCategories);

        formData.append('tags', JSON.stringify(allTags));
        formData.append('categories', JSON.stringify(allCategories));
        formData.append('additional_fields', JSON.stringify(additionalFields));


        // production append
        formData.append('unit_price', unitPrice);
        formData.append('unit_weight', unitWeight);
        formData.append('source', source);
        formData.append('address', address);
        formData.append('phone', phone);




        // TODO: later implement a hints, use customized modals to tell users that they are why their upload is not 
        // successful, such as because the duplicated reference number, etc
        sendSampleData(formData)
            .then(response => {
                console.log('Upload successful:', response);
            })
            .catch(error => {
                console.error('Upload failed:', error);
            });

        form.reset();
        fields.set([]);
        tags.set([]);
        categories.set([]);
        imageFile = null;
        imagePath = '';
        imagePreviewUrl = '';
        additionalImages = [];
        additionalImagePreviews = [];
    }
</script>

<form action="?/upload" method="POST" on:submit={handleSubmit} enctype="multipart/form-data">
    <div class="upload-container">
        <div class="upload-left">
            <h3>Main Image:</h3>
            <div 
                class="drag-drop-area image-preview-main {imagePreviewUrl ? 'highlight' : ''} {isDragOverMain ? 'drag-over' : ''}"
                role="button"
                tabindex="0"
                on:keydown={handleKeyDown}
                on:drop={handleDrop}
                on:dragenter={handleDragEnter}
                on:dragleave={handleDragLeave}
                on:dragover={handleDragOver}
            >
                <input 
                    type="file" 
                    id="image" 
                    name="image_file" 
                    accept="image/*" 
                    on:change={handleFileSelect} 
                    required 
                    class="file-input"
                >
                <div class="image-preview-container">
                    {#if imagePreviewUrl}
                        <div class="image-preview">
                            <img src={imagePreviewUrl} alt="preview file" />
                        </div>
                    {/if}
                    {#if imagePath}
                        <p>{imagePath}</p>
                    {/if}
                    {!imagePath && !imagePreviewUrl ? '< main image >' : ''}
                </div>
            </div>

            <div class="additional-images">
                <h3>Additional Images:</h3>
                <div 
                    class="drag-drop-area additional-images-area {isDragOverAdditional ? 'drag-over' : ''}"
                    role="button"
                    tabindex="0"
                    on:keydown={handleKeyDown}
                    on:drop={handleAdditionalDrop}
                    on:dragenter={handleAdditionalDragEnter}
                    on:dragleave={handleAdditionalDragLeave}
                    on:dragover={handleDragOver}
                >
                    <input 
                        type="file" 
                        id="additional-images" 
                        name="additional_images" 
                        accept="image/*" 
                        on:change={handleAdditionalFileSelect} 
                        multiple 
                        class="file-input"
                    >
                    {#if additionalImagePreviews.length > 0}
                        <div class="additional-images-container">
                            <div class="additional-image-previews">
                                {#each additionalImagePreviews as preview, index}
                                    <div class="additional-image-preview">
                                        <img src={preview} alt={`Additional image ${index + 1}`} />
                                        <button type="button" on:click={(event) => removeAdditionalImage(event, index)}>remove</button>
                                    </div>
                                {/each}
                            </div>
                        </div>
                    {:else}
                        <p>Drag and drop additional images here.</p>
                    {/if}
                </div>
            </div>
        </div>

        <div class="upload-right">
            <!-- Categories -->
            <div class="input-group">
                <div class="input-button-group">
                    <input type="text" id="category" name="category" placeholder="Categories" required>
                    <button type="button" on:click={() => addItem(categories)}>add</button>
                </div>
            </div>

            {#each $categories as category (category.id)}
                <div class="input-group indent">
                    <div class="input-button-group">
                        <input type="text" id="category-{category.id}" bind:value={category.value} placeholder="New category">
                        <button class="remove-items" type="button" on:click={() => removeItem(categories, category.id)}>Remove</button>
                    </div>
                </div>
            {/each}

            <!-- Tags -->
            <div class="input-group">
                <div class="input-button-group">
                    <input type="text" id="tag" name="tag" placeholder="Tags" required>
                    <button type="button" on:click={() => addItem(tags)}>add</button>
                </div>
            </div>

            {#each $tags as tag (tag.id)}
                <div class="input-group indent">
                    <div class="input-button-group">
                        <input type="text" id="tag-{tag.id}" bind:value={tag.value} placeholder="New tag">
                        <button class="remove-items" type="button" on:click={() => removeItem(tags, tag.id)}>Remove</button>
                    </div>
                </div>
            {/each}

            <!-- Reference Number -->
            <div class="input-group">
                <input type="text" id="reference_no" name="reference_no" placeholder="Reference Number" required>
            </div>


            <div class="input-group">
                <input type="text" id="unit_price" name="unit_price" bind:value={unitPrice} placeholder="Unit Price (e.g., 5.99, USD)" required>
            </div>
            <div class="input-group">
                <input type="text" id="unit_weight" name="unit_weight" bind:value={unitWeight} placeholder="Unit Weight (e.g., 500, g)" required>
            </div>
            <div class="input-group">
                <input type="text" id="source" name="source" bind:value={source} placeholder="Source" required>
            </div>
            <div class="input-group">
                <input type="text" id="address" name="address" bind:value={address} placeholder="Address" required>
            </div>
            <div class="input-group">
                <input type="text" id="phone" name="phone" bind:value={phone} placeholder="Phone" required>
            </div>



            <!-- Separator -->
            <hr class="separator">

            <!-- Additional Fields -->
            {#each $fields as field (field.id)}
                <div class="input-group additional-field">
                    <div class="feature-value-group">
                        <div class="input-label-group">
                            <input type="text" id="key-{field.id}" bind:value={field.key} placeholder="Field name">
                        </div>
                        <div class="input-label-group">
                            <input type="text" id="value-{field.id}" bind:value={field.value} placeholder="Value">
                        </div>
                    </div>
                    <button class="remove-items" type="button" on:click={() => removeItem(fields, field.id)}>Remove</button>
                </div>
            {/each}
            <div class="addfield-submit-button">
              <button type="button" on:click={() => addItem(fields)}>Add Field</button>
              <button type="submit">Submit</button>
            </div>
        </div>
    </div>
</form>





<style>
    form {
        font-family: "Ubuntu";
    }

    .upload-container {
        display: flex;
        gap: 2rem;
    }

    .upload-left, .upload-right {
        flex: 1;
    }

    .upload-left {
        display: flex;
        flex-direction: column;
    }

    .upload-right {
        margin: 1.5rem 0;
    }

    .input-group {
        margin-bottom: 1rem;
    }

    .input-button-group {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .input-button-group input {
        flex-grow: 1;
    }

    .indent {
        margin-left: 1.4rem;
    }

    .additional-field {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }



    .feature-value-group {
        display: flex;
        gap: 0.5rem;
    }

    .input-label-group {
        display: flex;
        flex-direction: column;
        flex: 1;
    }

    .drag-drop-area {
        position: relative;
        border: 2px dashed #ccc;
        text-align: center;
        padding: 8px 0;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: border-color 0.3s, background-color 0.3s;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-sizing: border-box;
    }

    .drag-drop-area:hover, .drag-over {
        border-color: #007bff;
        background-color: #e7f3ff;
    }

    .file-input {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0;
        cursor: pointer;
    }

    .image-preview-main {
        height: 300px;
        width: 100%;
        max-width: 100%;
    }

    .image-preview-container {
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    .image-preview {
        max-width: 100%;
        max-height: calc(100% - 30px);
        display: flex;
        justify-content: center;
        align-items: center;
        overflow: hidden;
    }

    .image-preview img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }

    .image-preview-container p {
        padding: 5px 0 0 0;
        margin: 0;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .additional-images {
        margin-top: 1.75rem;
    }

    .additional-images-area {
        min-height: 150px;
    }

    .additional-images-container {
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .additional-image-previews {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        justify-content: center;
        align-items: center;
    }

    .additional-image-preview {
        position: relative;
        width: 80px;
        height: 80px;
        overflow: hidden;
    }

    .additional-image-preview img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .additional-image-preview button {
        position: absolute;
        bottom: 2px;
        right: 2px;
        background: rgba(0, 0, 0, 0.5);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 10px;
        line-height: 1;
        cursor: pointer;
        transition: background-color 0.3s ease;
        margin: 0;
    }

    .additional-image-preview button:hover {
        background: rgba(0, 0, 0, 0.7);
    }

    .separator {
        border: 0;
        height: 1px;
        background: #ccc;
        margin: 2.5rem 0 1rem 0;
    }

    .input-button-group button,
    .additional-field button {
        padding: 0.25rem 0.75rem;
        font-size: 0.875rem;
        line-height: 1.5;
        border-radius: 0.2rem;
        white-space: nowrap;
        min-width: 60px;
        border: none;
        cursor: pointer;
        transition: background-color 0.3s, opacity 0.3s;
        text-align: center;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }


    .additional-field button {
      width: 100%;
    }


    .input-button-group button:hover,
    .additional-field button:hover {
        opacity: 0.9;
    }

    .input-button-group button:last-child {
        /* background-color: #4CAF50; */
        color: black;
    }

    .input-button-group .indent button,
    .additional-field button {
        /* background-color: #f44336; */
        color: black;
    }

    .input-button-group,
    .additional-field .feature-value-group {
        display: flex;
        align-items: stretch;
    }

    .additional-field button {
        align-self: flex-start;
        margin-top: 0.25rem;
    }

    .addfield-submit-button {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin-top: 1rem;
    }

    .addfield-submit-button button {
        padding: 0.375rem 0.75rem;
        font-size: 0.875rem;
        line-height: 1.5;
        border-radius: 0.2rem;
        white-space: nowrap;
        min-width: 60px;
        border: none;
        cursor: pointer;
        transition: background-color 0.3s, opacity 0.3s;
    }

    .addfield-submit-button button:first-child {
        background-color: #f0f0f0;
        color: #333;
    }

    .addfield-submit-button button:last-child {
        background-color: #007bff;
        color: white;
    }

    .addfield-submit-button button:hover {
        opacity: 0.9;
    }

    input[type="text"] {
        height: 2rem;
        padding: 0.25rem 0.5rem;
        font-size: 0.875rem;
        line-height: 1.5;
        border-radius: 0.2rem;
        border: 1px solid #ccc;
    }

    .remove-items {
      background: #ccc;
    }

    /* Ensure responsiveness */
    @media (max-width: 768px) {
        .upload-container {
            flex-direction: column;
        }

        .upload-left, .upload-right {
            width: 100%;
        }

        .image-preview-main {
            height: 200px; /* Reduce height on smaller screens */
        }
    }
</style>




