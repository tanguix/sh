



<script lang="ts">
    import { writable } from 'svelte/store';
    import { API_ENDPOINTS } from '$lib/utils/api';

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

    let sideReferenceNumber = '';
    let referenceNumber = '';
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

    function validateReferenceNumbers(): boolean {
        const sideRefs = sideReferenceNumber.split(',').map(ref => ref.trim());
        const allRefs = [...sideRefs, referenceNumber];
        const uniqueRefs = new Set(allRefs);
        return uniqueRefs.size === allRefs.length;
    }



    function handleSubmit(event: Event) {
        event.preventDefault();
        if (!validateReferenceNumbers()) {
            alert("Reference numbers must be unique across all entries.");
            return;
        }

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

        const allTags: string[] = [];
        const defaultTag = (document.getElementById('tag') as HTMLInputElement).value;
        if (defaultTag) {
            allTags.push(defaultTag);
        }
        tags.subscribe(currentTags => {
            currentTags.forEach(tag => {
                if (tag.value) {
                    allTags.push(tag.value);
                }
            });
        })();

        const allCategories: string[] = [];
        const defaultCategory = (document.getElementById('category') as HTMLInputElement).value;
        if (defaultCategory) {
            allCategories.push(defaultCategory);
        }
        categories.subscribe(currentCategories => {
            currentCategories.forEach(category => {
                if (category.value) {
                    allCategories.push(category.value);
                }
            });
        })();

        formData.append('side_reference_no', sideReferenceNumber);
        formData.append('reference_no', referenceNumber);
        formData.append('tags', JSON.stringify(allTags));
        formData.append('categories', JSON.stringify(allCategories));
        formData.append('additional_fields', JSON.stringify(additionalFields));

        formData.append('unit_price', unitPrice);
        formData.append('unit_weight', unitWeight);
        formData.append('source', source);
        formData.append('address', address);
        formData.append('phone', phone);

        sendSampleData(formData)
            .then(response => {
                console.log('Upload successful:', response);
                // Reset form fields here
                sideReferenceNumber = '';
                referenceNumber = '';
                unitPrice = '';
                unitWeight = '';
                source = '';
                address = '';
                phone = '';
                fields.set([]);
                tags.set([]);
                categories.set([]);
                imageFile = null;
                imagePath = '';
                imagePreviewUrl = '';
                additionalImages = [];
                additionalImagePreviews = [];
                (document.getElementById('tag') as HTMLInputElement).value = '';
                (document.getElementById('category') as HTMLInputElement).value = '';
            })
            .catch(error => {
                console.error('Upload failed:', error);
            });
    }


</script>




<form action="?/upload" method="POST" on:submit={handleSubmit} enctype="multipart/form-data">
    <div class="upload-container">
        <div class="upload-left">
            <!-- Main image upload area -->
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

            <!-- Additional images upload area -->
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

            <div class="input-group full-width">
                <div class="input-button-group">
                    <input type="text" id="category" name="category" placeholder="Categories" required>
                    <button type="button" on:click={() => addItem(categories)}>add</button>
                </div>
            </div>

            {#each $categories as category (category.id)}
                <div class="input-group full-width indent">
                    <div class="input-button-group">
                        <input type="text" id="category-{category.id}" bind:value={category.value} placeholder="New category">
                        <button class="remove-items" type="button" on:click={() => removeItem(categories, category.id)}>Remove</button>
                    </div>
                </div>
            {/each}

            <div class="input-group full-width">
                <div class="input-button-group">
                    <input type="text" id="tag" name="tag" placeholder="Tags" required>
                    <button type="button" on:click={() => addItem(tags)}>add</button>
                </div>
            </div>

            {#each $tags as tag (tag.id)}
                <div class="input-group full-width indent">
                    <div class="input-button-group">
                        <input type="text" id="tag-{tag.id}" bind:value={tag.value} placeholder="New tag">
                        <button class="remove-items" type="button" on:click={() => removeItem(tags, tag.id)}>Remove</button>
                    </div>
                </div>
            {/each}



            <div class="reference-numbers">
                <div class="input-group full-width">
                    <input 
                      type="text" 
                      id="side_reference_no" 
                      name="side_reference_no" 
                      bind:value={sideReferenceNumber} 
                      placeholder="Side Reference Numbers (comma-separated)" 
                      required>
                    <label for="side_reference_no">side ref</label>
                </div>
                <div class="input-group full-width">
                    <input type="text" id="reference_no" name="reference_no" bind:value={referenceNumber} placeholder="Reference Number" required>
                    <label for="reference_no">main ref</label>
                </div>
            </div>



            <hr class="separator">
            <div class="additional-info">
                <div class="input-group unit-price">
                    <input type="text" id="unit_price" name="unit_price" bind:value={unitPrice} placeholder="e.g. 5.99, USD" required>
                    <label for="unit_price">u price</label>
                </div>
                <div class="input-group">
                    <input type="text" id="unit_weight" name="unit_weight" bind:value={unitWeight} placeholder="e.g. 500, g" required>
                    <label for="unit_weight">u weight</label>
                </div>
                <div class="input-group full-width">
                    <input type="text" id="source" name="source" bind:value={source} placeholder="Source" required>
                    <label for="source">source</label>
                </div>
                <div class="input-group full-width">
                    <input type="text" id="address" name="address" bind:value={address} placeholder="Address">
                    <label for="address">address</label>
                </div>
                <div class="input-group full-width">
                    <input type="text" id="phone" name="phone" bind:value={phone} placeholder="Phone" required>
                    <label for="phone">phone</label>
                </div>
            </div>


            <hr class="separator">
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
        margin-bottom: 10px;
        display: flex;
        align-items: center;
    }

    .input-group label {
        flex: 0 0 30px;
        text-align: center;
        justify-content: center;
        margin-left: 10px;
        /* padding: 0rem; */
        font-size: 0.875rem;
        line-height: 1.5;
        border-radius: 0.2rem;
        white-space: nowrap;
        min-width: 60px;
        /* border: solid 1px; */
        transition: background-color 0.3s, opacity 0.3s;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .input-group input {
        flex: 1;
    }

    .input-button-group {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        width: 100%;
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
        margin: 0.8rem 0 1rem 0;
    }

    button {
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

    button:hover {
        opacity: 0.9;
    }

    .input-button-group button:last-child {
        color: black;
    }

    .input-button-group .indent button,
    .additional-field button {
        color: black;
    }

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
        height: 2.5rem;
        padding: 0.25rem 0.5rem;
        font-size: 0.875rem;
        line-height: 1.5;
        border-radius: 0.2rem;
        border: 1px solid #ccc;
        width: 100%;
        box-sizing: border-box;
    }

    .remove-items {
      background: #ccc;
    }

    .full-width {
        width: 100%;
    }

    .reference-numbers {
        display: flex;
        flex-direction: column;
        /* gap: 1rem; */
        /* margin-bottom: 1rem; */
    }

    .reference-numbers .input-group {
        width: 100%;
    }

    .additional-info {
        display: flex;
        flex-wrap: wrap;
        /* gap: 1rem; */
    }

    .additional-info .unit-price {
        margin-right: 1rem;
    }

    .additional-info .input-group {
        flex: 1 1 calc(50% - 0.5rem);
        min-width: 200px;
    }

    .additional-info .input-group.full-width {
        flex: 1 1 100%;
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
            height: 200px;
        }

        .additional-info {
            flex-direction: column;
        }

        .additional-info .input-group,
        .additional-info .input-group.full-width {
            flex: 1 1 100%;
        }

        .input-group {
            flex-direction: column;
            align-items: flex-start;
        }


        .input-group {
            flex-direction: column;
            align-items: flex-start;
        }

        .input-group label {
            flex: 0 0 auto;
            text-align: left;
            margin-left: 0;
            margin-bottom: 5px;
        }

        .input-group input {
            width: 100%;
        }

        .input-button-group {
            flex-direction: column;
        }

        .input-button-group button {
            width: 100%;
            margin-top: 5px;
        }
    }
</style>






